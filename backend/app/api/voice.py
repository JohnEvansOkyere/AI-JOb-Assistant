from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from uuid import UUID
import json
import asyncio
from io import BytesIO

from app.config import settings
from app.services.interview_service import InterviewService
from app.services.interview_ai_service import InterviewAIService
from app.services.ticket_service import TicketService
from app.services.interview_report_service import InterviewReportService
from app.services.storage_service import StorageService
from app.database import db
from app.utils.errors import NotFoundError, ForbiddenError
from app.voice.stt_service import get_stt_provider
from app.voice.tts_service import get_tts_provider
import structlog


logger = structlog.get_logger()

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.websocket("/interview/{ticket_code}")
async def voice_interview(
    websocket: WebSocket,
    ticket_code: str,
):
    """
    WebSocket endpoint for realtime interviews (supports both text and voice modes).

    Protocol:
    - JSON text messages (control):
      Client → server:
        { "type": "start" }
        { "type": "answer", "question_id": "<uuid>", "text": "candidate answer" }  // Text mode
        { "type": "audio_start" }  // Voice mode: candidate started speaking
        { "type": "audio_end" }    // Voice mode: candidate finished speaking
        { "type": "final_message", "text": "..." }
      
      Server → client:
        { "type": "question", "question_id": "<uuid>", "text": "..." }
        { "type": "audio_question_start" }  // Voice mode: AI is about to speak
        { "type": "audio_question_end" }    // Voice mode: AI finished speaking
        { "type": "transcription", "text": "..." }  // Voice mode: confirmed transcription
        { "type": "error", "message": "..." }
        { "type": "analysis", ... }
    
    - Binary messages (audio):
      Client → server: Raw audio chunks (WebM/Opus format)
      Server → client: TTS audio chunks (MP3 format)
    """

    await websocket.accept()

    # Initialize STT and TTS providers
    stt = get_stt_provider(settings.stt_provider)
    tts = get_tts_provider()

    interview_ai = InterviewAIService()
    interview = None
    job_description = None
    cv_text = ""
    waiting_for_final_message = False
    # Limit the total number of questions per interview to control token usage
    MAX_QUESTIONS = 5
    questions_asked = 0
    
    # Voice mode state
    interview_mode = "text"  # Will be set from ticket
    audio_buffer = BytesIO()  # Buffer for accumulating audio chunks
    is_recording_audio = False  # Track if we're currently recording candidate audio
    current_question_id = None  # Track current question for voice mode
    response_audio_paths = {}  # Track audio paths by question_id for voice mode responses

    try:
        # Validate ticket first
        try:
            ticket = await TicketService.validate_ticket(ticket_code)
            # Get interview mode from ticket
            interview_mode = ticket.get("interview_mode", "text")
            logger.info(
                "WebSocket connected for interview",
                ticket_code=ticket_code,
                interview_mode=interview_mode
            )
        except NotFoundError:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid ticket code"}))
            await websocket.close()
            return
        except ForbiddenError as e:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
            await websocket.close()
            return

        # Lazy-create interview on "start" message, so we don't consume the ticket until client is ready

        while True:
            # Receive message (can be text or binary)
            message_data = await websocket.receive()
            
            # Handle binary audio chunks - check for bytes key or bytes type
            if "bytes" in message_data or message_data.get("type") == "websocket.receive.bytes":
                if interview_mode == "voice" and is_recording_audio:
                    # Accumulate audio chunk in buffer
                    audio_chunk = message_data.get("bytes", b"")
                    if audio_chunk:
                        audio_buffer.write(audio_chunk)
                        logger.debug("Received audio chunk", chunk_size=len(audio_chunk), buffer_size=audio_buffer.tell())
                else:
                    logger.warning("Received binary message but not in voice recording mode", interview_mode=interview_mode, is_recording=is_recording_audio)
                continue
            
            # Handle text messages - check for text key (more reliable than type string)
            if "text" not in message_data and message_data.get("type") != "websocket.receive.text":
                # Log full message_data for debugging unexpected types
                logger.warning(
                    "Unexpected message type",
                    msg_type=message_data.get("type"),
                    message_keys=list(message_data.keys()) if isinstance(message_data, dict) else None,
                    interview_mode=interview_mode
                )
                continue
            
            raw = message_data.get("text", "")
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON message"}))
                continue

            msg_type = message.get("type")

            if msg_type == "start":
                # Create + start interview if not created yet
                if interview is None:
                    interview = await InterviewService.create_interview_from_ticket(ticket_code)
                    interview = await InterviewService.start_interview(UUID(interview["id"]))

                    # Load job description and CV text
                    job_response = db.service_client.table("job_descriptions").select("*").eq(
                        "id", str(interview["job_description_id"])
                    ).execute()
                    job_description = (job_response.data or [None])[0]

                    cv_response = (
                        db.service_client.table("cvs")
                        .select("parsed_text")
                        .eq("candidate_id", str(interview["candidate_id"]))
                        # Order by uploaded_at (existing column) to get the latest CV
                        .order("uploaded_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    cv_text = (cv_response.data or [{}])[0].get("parsed_text", "") or ""

                    # Generate initial questions and send the first one (with timeout)
                    try:
                        questions = await asyncio.wait_for(
                            interview_ai.generate_initial_questions(
                                UUID(interview["id"]),
                                job_description or {},
                                cv_text,
                                num_questions=5,
                            ),
                            timeout=60.0  # 60 second timeout for question generation
                        )

                        # Persisted rows exist in DB already; fetch the first question row to get its ID
                        first_q_response = (
                            db.service_client.table("interview_questions")
                            .select("id, question_text")
                            .eq("interview_id", str(interview["id"]))
                            .order("order_index")
                            .limit(1)
                            .execute()
                        )
                        first_q = (first_q_response.data or [None])[0]

                        if first_q:
                            questions_asked = 1
                            current_question_id = first_q["id"]
                            question_text = first_q["question_text"]
                            
                            # Send question (text mode) or generate audio (voice mode)
                            if interview_mode == "voice":
                                # Generate TTS audio for question
                                try:
                                    await websocket.send_text(
                                        json.dumps({"type": "audio_question_start"})
                                    )
                                    
                                    # Generate audio
                                    logger.info("Starting TTS synthesis", question_id=first_q["id"], text_length=len(question_text))
                                    audio_bytes = await tts.synthesize(question_text)
                                    
                                    # Validate audio bytes
                                    if not audio_bytes:
                                        raise ValueError("TTS returned empty audio bytes")
                                    if not isinstance(audio_bytes, bytes):
                                        raise TypeError(f"TTS returned wrong type: {type(audio_bytes)}, expected bytes")
                                    
                                    logger.info(
                                        "TTS synthesis successful, sending audio",
                                        question_id=first_q["id"],
                                        audio_size=len(audio_bytes),
                                        audio_type=type(audio_bytes).__name__
                                    )
                                    
                                    # Check WebSocket state before sending
                                    if websocket.client_state != WebSocketState.CONNECTED:
                                        raise ConnectionError(f"WebSocket not connected, state: {websocket.client_state}")
                                    
                                    # Send audio as binary
                                    # FastAPI/Starlette WebSocket send_bytes handles bytes directly
                                    await websocket.send_bytes(audio_bytes)
                                    logger.info("Audio bytes sent successfully", question_id=first_q["id"], bytes_sent=len(audio_bytes))
                                    
                                    await websocket.send_text(
                                        json.dumps({"type": "audio_question_end"})
                                    )
                                    
                                    # Also send text for display/accessibility
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "question",
                                                "question_id": first_q["id"],
                                                "text": question_text,
                                            }
                                        )
                                    )
                                    logger.info("Question sent successfully with audio", question_id=first_q["id"])
                                except Exception as e:
                                    logger.error(
                                        "TTS or audio sending failed, falling back to text",
                                        error=str(e),
                                        error_type=type(e).__name__,
                                        question_id=first_q["id"],
                                        exc_info=True
                                    )
                                    # Fallback to text if TTS fails
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "question",
                                                "question_id": first_q["id"],
                                                "text": question_text,
                                            }
                                        )
                                    )
                            else:
                                # Text mode - send text only
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "question",
                                            "question_id": first_q["id"],
                                            "text": question_text,
                                        }
                                    )
                                )
                        else:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "error",
                                        "message": "Failed to generate initial question. Please try again.",
                                    }
                                )
                            )
                    except asyncio.TimeoutError:
                        logger.error("Timeout generating initial questions", ticket_code=ticket_code)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "The AI is taking longer than expected. Please refresh and try again.",
                                }
                            )
                        )
                    except Exception as e:
                        logger.error("Error generating initial questions", error=str(e), ticket_code=ticket_code, exc_info=True)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "An error occurred while generating questions. Please try again later.",
                                }
                            )
                        )

                else:
                    # Interview already started; ignore duplicate start
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "info",
                                "message": "Interview already started",
                            }
                        )
                    )

            elif msg_type == "audio_start":
                # Candidate started speaking (voice mode)
                if interview_mode != "voice":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "audio_start only valid in voice mode",
                            }
                        )
                    )
                    continue
                
                if not is_recording_audio:
                    is_recording_audio = True
                    audio_buffer.seek(0)
                    audio_buffer.truncate(0)  # Clear buffer
                    logger.info("Started recording candidate audio")
                else:
                    logger.warning("audio_start received but already recording")

            elif msg_type == "audio_end":
                # Candidate finished speaking (voice mode) - transcribe audio
                if interview_mode != "voice":
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "audio_end only valid in voice mode",
                            }
                        )
                    )
                    continue
                
                if not is_recording_audio:
                    logger.warning(
                        "audio_end received but not recording - ignoring duplicate message",
                        current_question_id=current_question_id,
                        audio_buffer_size=audio_buffer.tell()
                    )
                    continue
                
                if interview is None:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Interview not started. Send a 'start' message first.",
                            }
                        )
                    )
                    continue
                
                # Get audio from buffer
                audio_buffer.seek(0)
                audio_bytes = audio_buffer.read()
                audio_buffer.seek(0)
                audio_buffer.truncate(0)  # Clear buffer
                is_recording_audio = False
                
                if not audio_bytes or len(audio_bytes) == 0:
                    logger.warning("audio_end received but buffer is empty")
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "No audio data received. Please try speaking again.",
                            }
                        )
                    )
                    continue
                
                # Transcribe audio using STT
                try:
                    logger.info("Transcribing audio", audio_size=len(audio_bytes))
                    answer_text = await stt.transcribe_chunk(audio_bytes, language="en")
                    
                    if not answer_text or len(answer_text.strip()) == 0:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Could not transcribe audio. Please try speaking again.",
                                }
                            )
                        )
                        continue
                    
                    # Send transcription confirmation
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "transcription",
                                "text": answer_text,
                            }
                        )
                    )
                    
                    # Save audio to storage (non-blocking, don't fail interview if storage fails)
                    question_id = current_question_id
                    if question_id and interview:
                        try:
                            # Detect file extension from audio bytes (default to webm)
                            file_extension = "webm"  # Default for browser MediaRecorder
                            if audio_bytes[:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE':
                                file_extension = "wav"
                            elif audio_bytes[:3] == b'ID3' or audio_bytes[:2] in (b'\xff\xfb', b'\xff\xf3'):
                                file_extension = "mp3"
                            elif audio_bytes[4:8] == b'ftyp':
                                file_extension = "m4a"
                            
                            # Upload response audio
                            storage_path = await StorageService.upload_response_audio(
                                UUID(interview["id"]),
                                UUID(question_id),
                                audio_bytes,
                                response_index=1,  # Could track multiple responses per question
                                file_extension=file_extension
                            )
                            
                            # Store audio path for later update when response is saved
                            response_audio_paths[question_id] = storage_path
                            
                            logger.info(
                                "Response audio saved to storage",
                                interview_id=str(interview["id"]),
                                question_id=question_id,
                                storage_path=storage_path
                            )
                            
                        except Exception as storage_error:
                            # Don't fail the interview if storage fails
                            logger.warning(
                                "Failed to save response audio to storage",
                                interview_id=str(interview["id"]),
                                question_id=question_id,
                                error=str(storage_error)
                            )
                    
                    # Process as answer (reuse answer handling logic)
                    if not question_id:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "No current question. Please start the interview.",
                                }
                            )
                        )
                        continue
                    
                    # Process answer immediately (don't rely on fall-through since elif won't re-check)
                    logger.info(
                        "Transcription completed, processing answer immediately",
                        question_id=question_id,
                        answer_length=len(answer_text),
                        questions_asked=questions_asked
                    )
                    
                    # Process answer directly here - can't use fall-through because elif conditions
                    # are only checked at the start of the if/elif chain
                    
                    # Validate question_id and answer_text
                    if not question_id or not answer_text:
                        logger.warning("Answer missing required fields after transcription", question_id=question_id, has_text=bool(answer_text))
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "Missing question or answer data. Please try again.",
                                }
                            )
                        )
                        continue
                    
                    # Analyze response and store it (with timeout)
                    logger.info("Starting response analysis", question_id=question_id, questions_asked=questions_asked)
                    try:
                        analysis = await asyncio.wait_for(
                            interview_ai.process_response(
                                UUID(interview["id"]),
                                UUID(question_id),
                                answer_text,
                                job_description or {},
                                cv_text,
                            ),
                            timeout=45.0  # 45 second timeout for response analysis
                        )
                        
                        # Update response with audio path if available (for voice mode)
                        if interview_mode == "voice" and question_id in response_audio_paths:
                            audio_path = response_audio_paths[question_id]
                            # Find the most recent response for this question and update it
                            # Note: update() doesn't support order(), so we need to select first, then update
                            try:
                                response_query = db.service_client.table("interview_responses").select("id").eq("interview_id", str(interview["id"])).eq("question_id", question_id).order("created_at", desc=True).limit(1).execute()
                                if response_query.data and len(response_query.data) > 0:
                                    response_id = response_query.data[0]["id"]
                                    db.service_client.table("interview_responses").update({
                                        "response_audio_path": audio_path
                                    }).eq("id", response_id).execute()
                                    logger.info("Updated response with audio path", question_id=question_id, response_id=response_id, audio_path=audio_path)
                                else:
                                    logger.warning("No response found to update with audio path", question_id=question_id, interview_id=str(interview["id"]))
                            except Exception as update_err:
                                logger.warning("Failed to update response with audio path", question_id=question_id, error=str(update_err))
                            # Remove from tracking dict
                            del response_audio_paths[question_id]

                        # Update / create interview-level report (non-blocking for UX if it fails)
                        try:
                            await InterviewReportService.upsert_from_analysis(
                                UUID(interview["id"]),
                                analysis,
                            )
                        except Exception as report_err:
                            logger.warning("Failed to update interview report", error=str(report_err), interview_id=str(interview["id"]))

                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "analysis",
                                    "question_id": question_id,
                                    "analysis": analysis,
                                }
                            )
                        )
                    except asyncio.TimeoutError:
                        logger.error("Timeout analyzing response", ticket_code=ticket_code, question_id=question_id)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "The AI is taking longer than expected to analyze your response. We'll continue with the next question.",
                                }
                            )
                        )
                        # Continue to next question even if analysis timed out
                        analysis = {"quality": "adequate", "response_quality": "adequate"}
                    except Exception as e:
                        logger.error("Error analyzing response", error=str(e), ticket_code=ticket_code, question_id=question_id, exc_info=True)
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "error",
                                    "message": "An error occurred while analyzing your response. We'll continue with the next question.",
                                }
                            )
                        )
                        # Continue to next question even if analysis failed
                        analysis = {"quality": "adequate", "response_quality": "adequate"}

                    # Check if we're at the question limit
                    if questions_asked >= MAX_QUESTIONS:
                        # Ask for final message from candidate
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                        continue

                    # Warn candidate if next question will be the last one
                    if questions_asked == MAX_QUESTIONS - 1:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "info",
                                    "message": "Just a heads up - we have one more question, and then we'll wrap up the interview.",
                                }
                            )
                        )

                    response_quality = analysis.get("quality") or analysis.get("response_quality", "adequate")
                    non_answer_type = analysis.get("non_answer_type")  # Extract non-answer type if detected
                    
                    logger.info(
                        "Starting follow-up question generation",
                        question_id=question_id,
                        questions_asked=questions_asked,
                        max_questions=MAX_QUESTIONS,
                        response_quality=response_quality
                    )
                    
                    try:
                        followup = await asyncio.wait_for(
                            interview_ai.generate_followup_question(
                                UUID(interview["id"]),
                                job_description or {},
                                cv_text,
                                UUID(question_id),
                                response_quality,
                                answer_text,  # Pass the candidate's response text
                                non_answer_type  # Pass non-answer type if detected
                            ),
                            timeout=45.0  # 45 second timeout for follow-up question generation
                        )
                        logger.info(
                            "Follow-up question generated successfully",
                            followup_question_id=followup.get("id") if followup else None,
                            has_followup=bool(followup)
                        )
                        
                        if followup:
                            questions_asked += 1
                            current_question_id = followup["id"]
                            question_text = followup["question_text"]
                            
                            # Send question (text mode) or generate audio (voice mode)
                            if interview_mode == "voice":
                                # Generate TTS audio for question
                                try:
                                    await websocket.send_text(
                                        json.dumps({"type": "audio_question_start"})
                                    )
                                    
                                    # Generate audio
                                    logger.info("Starting TTS synthesis for followup", question_id=followup["id"], text_length=len(question_text))
                                    audio_bytes = await tts.synthesize(question_text)
                                    
                                    # Validate audio bytes
                                    if not audio_bytes:
                                        raise ValueError("TTS returned empty audio bytes")
                                    if not isinstance(audio_bytes, bytes):
                                        raise TypeError(f"TTS returned wrong type: {type(audio_bytes)}, expected bytes")
                                    
                                    logger.info(
                                        "TTS synthesis successful, sending audio",
                                        question_id=followup["id"],
                                        audio_size=len(audio_bytes),
                                        audio_type=type(audio_bytes).__name__
                                    )
                                    
                                    # Check WebSocket state before sending
                                    if websocket.client_state != WebSocketState.CONNECTED:
                                        raise ConnectionError(f"WebSocket not connected, state: {websocket.client_state}")
                                    
                                    # Send audio as binary
                                    await websocket.send_bytes(audio_bytes)
                                    logger.info("Audio bytes sent successfully", question_id=followup["id"], bytes_sent=len(audio_bytes))
                                    
                                    await websocket.send_text(
                                        json.dumps({"type": "audio_question_end"})
                                    )
                                    
                                    # Also send text for display/accessibility
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "question",
                                                "question_id": followup["id"],
                                                "text": question_text,
                                            }
                                        )
                                    )
                                    logger.info("Follow-up question sent successfully with audio", question_id=followup["id"])
                                except Exception as e:
                                    logger.error(
                                        "TTS or audio sending failed for followup, falling back to text",
                                        error=str(e),
                                        error_type=type(e).__name__,
                                        question_id=followup["id"],
                                        exc_info=True
                                    )
                                    # Fallback to text if TTS fails
                                    await websocket.send_text(
                                        json.dumps(
                                            {
                                                "type": "question",
                                                "question_id": followup["id"],
                                                "text": question_text,
                                            }
                                        )
                                    )
                            else:
                                # Text mode - send text only
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "question",
                                            "question_id": followup["id"],
                                            "text": question_text,
                                        }
                                    )
                                )
                        else:
                            # If no followup generated, end interview gracefully
                            waiting_for_final_message = True
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "final_message_request",
                                        "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                    }
                                )
                            )
                    except asyncio.TimeoutError:
                        logger.error("Timeout generating follow-up question", ticket_code=ticket_code, question_id=question_id)
                        # End interview gracefully if we can't generate next question
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                    except Exception as e:
                        logger.error("Error generating follow-up question", error=str(e), ticket_code=ticket_code, question_id=question_id, exc_info=True)
                        # End interview gracefully if we can't generate next question
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                    
                except Exception as e:
                    logger.error("STT transcription failed", error=str(e), exc_info=True)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": f"Failed to transcribe audio: {str(e)}. Please try again.",
                            }
                        )
                    )
                    continue

            elif msg_type == "answer":
                logger.info(
                    "Processing answer message",
                    question_id=message.get("question_id"),
                    answer_length=len(message.get("text", "")),
                    interview_started=interview is not None
                )
                
                if interview is None:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Interview not started. Send a 'start' message first.",
                            }
                        )
                    )
                    continue

                question_id = message.get("question_id")
                answer_text = message.get("text") or ""

                if not question_id or not answer_text:
                    logger.warning("Answer message missing required fields", question_id=question_id, has_text=bool(answer_text))
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Missing 'question_id' or 'text' in answer message",
                            }
                        )
                    )
                    continue

                # Analyze response and store it (with timeout)
                logger.info("Starting response analysis", question_id=question_id, questions_asked=questions_asked)
                try:
                    analysis = await asyncio.wait_for(
                        interview_ai.process_response(
                            UUID(interview["id"]),
                            UUID(question_id),
                            answer_text,
                            job_description or {},
                            cv_text,
                        ),
                        timeout=45.0  # 45 second timeout for response analysis
                    )
                    
                    # Update response with audio path if available (for voice mode)
                    if interview_mode == "voice" and question_id in response_audio_paths:
                        audio_path = response_audio_paths[question_id]
                        # Find the most recent response for this question and update it
                        # Note: update() doesn't support order(), so we need to select first, then update
                        try:
                            response_query = db.service_client.table("interview_responses").select("id").eq("interview_id", str(interview["id"])).eq("question_id", question_id).order("created_at", desc=True).limit(1).execute()
                            if response_query.data and len(response_query.data) > 0:
                                response_id = response_query.data[0]["id"]
                                db.service_client.table("interview_responses").update({
                                    "response_audio_path": audio_path
                                }).eq("id", response_id).execute()
                                logger.info("Updated response with audio path", question_id=question_id, response_id=response_id, audio_path=audio_path)
                            else:
                                logger.warning("No response found to update with audio path", question_id=question_id, interview_id=str(interview["id"]))
                        except Exception as update_err:
                            logger.warning("Failed to update response with audio path", question_id=question_id, error=str(update_err))
                        # Remove from tracking dict
                        del response_audio_paths[question_id]

                    # Update / create interview-level report (non-blocking for UX if it fails)
                    try:
                        await InterviewReportService.upsert_from_analysis(
                            UUID(interview["id"]),
                            analysis,
                        )
                    except Exception as report_err:
                        logger.warning("Failed to update interview report", error=str(report_err), interview_id=str(interview["id"]))

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "analysis",
                                "question_id": question_id,
                                "analysis": analysis,
                            }
                        )
                    )
                except asyncio.TimeoutError:
                    logger.error("Timeout analyzing response", ticket_code=ticket_code, question_id=question_id)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "The AI is taking longer than expected to analyze your response. We'll continue with the next question.",
                            }
                        )
                    )
                    # Continue to next question even if analysis timed out
                    analysis = {"quality": "adequate", "response_quality": "adequate"}
                except Exception as e:
                    logger.error("Error analyzing response", error=str(e), ticket_code=ticket_code, question_id=question_id, exc_info=True)
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "An error occurred while analyzing your response. We'll continue with the next question.",
                            }
                        )
                    )
                    # Continue to next question even if analysis failed
                    analysis = {"quality": "adequate", "response_quality": "adequate"}

                # Check if we're at the question limit
                if questions_asked >= MAX_QUESTIONS:
                    # Ask for final message from candidate
                    waiting_for_final_message = True
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final_message_request",
                                "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                            }
                        )
                    )
                    continue

                # Warn candidate if next question will be the last one
                if questions_asked == MAX_QUESTIONS - 1:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "info",
                                "message": "Just a heads up - we have one more question, and then we'll wrap up the interview.",
                            }
                        )
                    )

                response_quality = analysis.get("quality") or analysis.get("response_quality", "adequate")
                non_answer_type = analysis.get("non_answer_type")  # Extract non-answer type if detected
                
                logger.info(
                    "Starting follow-up question generation",
                    question_id=question_id,
                    questions_asked=questions_asked,
                    max_questions=MAX_QUESTIONS,
                    response_quality=response_quality
                )
                
                try:
                    followup = await asyncio.wait_for(
                        interview_ai.generate_followup_question(
                            UUID(interview["id"]),
                            job_description or {},
                            cv_text,
                            UUID(question_id),
                            response_quality,
                            answer_text,  # Pass the candidate's response text
                            non_answer_type  # Pass non-answer type if detected
                        ),
                        timeout=45.0  # 45 second timeout for follow-up question generation
                    )
                    logger.info(
                        "Follow-up question generated successfully",
                        followup_question_id=followup.get("id") if followup else None,
                        has_followup=bool(followup)
                    )

                    if followup:
                        questions_asked += 1
                        current_question_id = followup["id"]
                        question_text = followup["question_text"]
                        
                        # Send question (text mode) or generate audio (voice mode)
                        if interview_mode == "voice":
                            # Generate TTS audio for question
                            try:
                                await websocket.send_text(
                                    json.dumps({"type": "audio_question_start"})
                                )
                                
                                # Generate audio
                                logger.info("Starting TTS synthesis for followup", question_id=followup["id"], text_length=len(question_text))
                                audio_bytes = await tts.synthesize(question_text)
                                
                                # Validate audio bytes
                                if not audio_bytes:
                                    raise ValueError("TTS returned empty audio bytes")
                                if not isinstance(audio_bytes, bytes):
                                    raise TypeError(f"TTS returned wrong type: {type(audio_bytes)}, expected bytes")
                                
                                logger.info(
                                    "TTS synthesis successful, sending audio",
                                    question_id=followup["id"],
                                    audio_size=len(audio_bytes),
                                    audio_type=type(audio_bytes).__name__
                                )
                                
                                # Check WebSocket state before sending
                                if websocket.client_state != WebSocketState.CONNECTED:
                                    raise ConnectionError(f"WebSocket not connected, state: {websocket.client_state}")
                                
                                # Send audio as binary
                                # FastAPI/Starlette WebSocket send_bytes handles bytes directly
                                await websocket.send_bytes(audio_bytes)
                                logger.info("Audio bytes sent successfully", question_id=followup["id"], bytes_sent=len(audio_bytes))
                                
                                await websocket.send_text(
                                    json.dumps({"type": "audio_question_end"})
                                )
                                
                                # Also send text for display/accessibility
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "question",
                                            "question_id": followup["id"],
                                            "text": question_text,
                                        }
                                    )
                                )
                                logger.info("Followup question sent successfully with audio", question_id=followup["id"])
                            except Exception as e:
                                logger.error(
                                    "TTS or audio sending failed, falling back to text",
                                    error=str(e),
                                    error_type=type(e).__name__,
                                    question_id=followup["id"],
                                    exc_info=True
                                )
                                # Fallback to text if TTS fails
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "question",
                                            "question_id": followup["id"],
                                            "text": question_text,
                                        }
                                    )
                                )
                        else:
                            # Text mode - send text only
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "question",
                                        "question_id": followup["id"],
                                        "text": question_text,
                                    }
                                )
                            )
                    else:
                        # If no followup generated, end interview gracefully
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                except asyncio.TimeoutError:
                    logger.error("Timeout generating follow-up question", ticket_code=ticket_code, question_id=question_id)
                    # End interview gracefully if we can't generate next question
                    waiting_for_final_message = True
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final_message_request",
                                "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                            }
                        )
                    )
                except Exception as e:
                    logger.error("Error generating follow-up question", error=str(e), ticket_code=ticket_code, question_id=question_id, exc_info=True)
                    # End interview gracefully if we can't generate next question
                    waiting_for_final_message = True
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final_message_request",
                                "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                            }
                        )
                    )

            elif msg_type == "final_message":
                # Handle candidate's final message
                if not waiting_for_final_message:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Unexpected final message. Please send a regular answer.",
                            }
                        )
                    )
                    continue

                final_message_text = message.get("text") or ""
                
                # Store the final message (optional - could save to interview_responses or transcript)
                if final_message_text:
                    logger.info("Final message received", interview_id=str(interview["id"]), message=final_message_text[:100])
                
                # Send closing message
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "interview_complete",
                            "message": "Thank you so much for taking the time to interview with us today. We really appreciate your interest in this role and the insights you've shared. We'll be reviewing your responses and will be in touch with you soon. Have a great day!",
                        }
                    )
                )
                
                # Mark interview as completed
                try:
                    await InterviewService.complete_interview(UUID(interview["id"]))
                    
                    # Save full interview audio if in voice mode and we have accumulated audio
                    # Note: For full interview audio, we'd need to accumulate all audio chunks
                    # This is a simplified version - in production, you might want to accumulate
                    # all audio throughout the interview
                    if interview_mode == "voice":
                        # Optionally save a combined audio file if we track it
                        # For now, individual response audio files are saved above
                        logger.info("Interview completed in voice mode", interview_id=str(interview["id"]))
                        
                except Exception as e:
                    logger.error("Error completing interview", error=str(e))
                
                # Close the connection after a brief delay
                await websocket.close()
                return

            else:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "Unknown message type",
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info("Voice interview websocket disconnected", ticket_code=ticket_code)
        return
    except Exception as e:
        logger.error("Voice interview websocket error", ticket_code=ticket_code, error=str(e))
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": "Internal server error"}))
        except Exception:
            pass
        finally:
            await websocket.close()


