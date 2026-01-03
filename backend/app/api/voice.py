from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from uuid import UUID
from typing import Optional
import json
import asyncio
from io import BytesIO

from app.config import settings
from app.services.interview_service import InterviewService
from app.services.interview_ai_service import InterviewAIService
from app.services.ticket_service import TicketService
from app.services.interview_report_service import InterviewReportService
from app.services.storage_service import StorageService
from app.services.email_service import EmailService
from app.database import db
from app.utils.errors import NotFoundError, ForbiddenError
from app.voice.stt_service import get_stt_provider
from app.voice.tts_service import get_tts_provider
import structlog


logger = structlog.get_logger()

router = APIRouter(prefix="/voice", tags=["Voice"])


async def aggregate_interview_audio(interview_id: UUID) -> Optional[str]:
    """
    Aggregate all response audio files into a single full interview audio file.
    
    Args:
        interview_id: Interview ID
    
    Returns:
        Storage path to aggregated audio file, or None if no audio files found
    """
    try:
        # Get all response audio paths from database, ordered by creation time
        responses_response = (
            db.service_client.table("interview_responses")
            .select("id, response_audio_path, created_at")
            .eq("interview_id", str(interview_id))
            .not_.is_("response_audio_path", "null")
            .order("created_at")
            .execute()
        )
        
        if not responses_response.data or len(responses_response.data) == 0:
            logger.info("No response audio files found to aggregate", interview_id=str(interview_id))
            return None
        
        audio_paths = [resp["response_audio_path"] for resp in responses_response.data if resp.get("response_audio_path")]
        
        if not audio_paths:
            logger.info("No valid audio paths found", interview_id=str(interview_id))
            return None
        
        logger.info(
            "Aggregating interview audio",
            interview_id=str(interview_id),
            num_files=len(audio_paths)
        )
        
        bucket_name = settings.supabase_storage_bucket_audio
        audio_chunks = []
        
        # Download all audio files and concatenate them
        for audio_path in audio_paths:
            try:
                # Download audio file from storage
                audio_data = db.service_client.storage.from_(bucket_name).download(audio_path)
                if audio_data:
                    audio_chunks.append(audio_data)
                    logger.debug("Downloaded audio chunk", path=audio_path, size=len(audio_data))
            except Exception as download_err:
                logger.warning("Failed to download audio file", path=audio_path, error=str(download_err))
                # Continue with other files - don't fail entire aggregation if one file fails
        
        if not audio_chunks:
            logger.warning("No audio chunks were successfully downloaded", interview_id=str(interview_id))
            return None
        
        # Concatenate all audio chunks
        # Note: Simple byte concatenation works for WebM in some cases, but for proper audio merging
        # you would need to use ffmpeg or pydub to re-encode. This simple approach creates a file
        # that may or may not play correctly depending on the WebM container format.
        combined_audio = b''.join(audio_chunks)
        
        logger.info(
            "Combined audio chunks",
            interview_id=str(interview_id),
            total_size=len(combined_audio),
            num_chunks=len(audio_chunks)
        )
        
        # Upload combined audio file
        storage_path = await StorageService.upload_interview_audio(
            interview_id=interview_id,
            audio_bytes=combined_audio,
            file_extension="webm"  # Default to webm format
        )
        
        logger.info(
            "Successfully aggregated interview audio",
            interview_id=str(interview_id),
            storage_path=storage_path,
            total_size=len(combined_audio)
        )
        
        return storage_path
        
    except Exception as e:
        logger.error(
            "Failed to aggregate interview audio",
            interview_id=str(interview_id),
            error=str(e),
            exc_info=True
        )
        # Return None instead of raising - don't fail interview completion if audio aggregation fails
        return None


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
    cover_letter_text = None
    waiting_for_final_message = False
    # Core questions (must complete) - follow-ups don't count toward this limit
    MAX_CORE_QUESTIONS = 5
    questions_asked = 0
    core_questions_asked = 0
    
    # Time tracking for 20-minute maximum
    import time
    interview_start_time = None
    MAX_INTERVIEW_DURATION_SECONDS = 20 * 60  # 20 minutes
    
    # Track follow-ups per question (max 1-2 per core question)
    followups_per_question = {}  # question_id -> followup_count
    MAX_FOLLOWUPS_PER_QUESTION = 2
    
    # Voice mode state
    interview_mode = "text"  # Will be set from ticket
    audio_buffer = BytesIO()  # Buffer for accumulating audio chunks
    is_recording_audio = False  # Track if we're currently recording candidate audio
    current_question_id = None  # Track current question for voice mode
    response_audio_paths = {}  # Track audio paths by question_id for voice mode responses
    candidate_name = None  # Cache candidate name for file naming
    question_order_map = {}  # Map question_id -> order_index for file naming

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
                    
                    # Load cover letter if available
                    try:
                        from app.services.interview_question_service import InterviewQuestionService
                        question_service = InterviewQuestionService()
                        cover_letter_text = await question_service.get_cover_letter_text(
                            UUID(interview["candidate_id"]),
                            UUID(interview["job_description_id"])
                        )
                        if cover_letter_text:
                            logger.info("Cover letter loaded for interview", interview_id=str(interview["id"]))
                    except Exception as e:
                        logger.warning("Failed to load cover letter", error=str(e), interview_id=str(interview["id"]))
                        cover_letter_text = None
                    
                    # Fetch candidate name for file naming
                    try:
                        candidate_response = db.service_client.table("candidates").select("full_name").eq("id", str(interview["candidate_id"])).execute()
                        if candidate_response.data and candidate_response.data[0].get("full_name"):
                            candidate_name = candidate_response.data[0]["full_name"]
                    except Exception as e:
                        logger.warning("Failed to fetch candidate name for file naming", error=str(e))
                        candidate_name = None
                    
                    # Set interview start time for duration tracking
                    interview_start_time = time.time()

                    # Generate initial questions with cover letter support (with timeout)
                    try:
                        questions = await asyncio.wait_for(
                            interview_ai.generate_initial_questions(
                                UUID(interview["id"]),
                                job_description or {},
                                cv_text,
                                cover_letter_text=cover_letter_text,
                                num_questions=5,
                            ),
                            timeout=60.0  # 60 second timeout for question generation
                        )

                        # Persisted rows exist in DB already; fetch questions with order_index to build mapping
                        questions_response = (
                            db.service_client.table("interview_questions")
                            .select("id, question_text, order_index")
                            .eq("interview_id", str(interview["id"]))
                            .order("order_index")
                            .execute()
                        )
                        questions_list = questions_response.data or []
                        
                        # Build question order map: question_id -> order_index (1-based)
                        for q in questions_list:
                            question_order_map[q["id"]] = q.get("order_index", 0) + 1  # order_index is 0-based, we want 1-based
                        
                        first_q = questions_list[0] if questions_list else None

                        if first_q:
                            questions_asked = 1
                            # Check if first question is core (warmup doesn't count)
                            first_q_type = first_q.get("question_type", "")
                            if first_q_type != "warmup":
                                core_questions_asked = 1
                            else:
                                core_questions_asked = 0
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
                                    # Get context for logging
                                    interview_id_val = UUID(interview["id"]) if interview else None
                                    job_desc_id = UUID(job_description["id"]) if job_description else None
                                    candidate_id_val = UUID(interview["candidate_id"]) if interview and interview.get("candidate_id") else None
                                    recruiter_id_val = UUID(job_description["recruiter_id"]) if job_description and job_description.get("recruiter_id") else None
                                    audio_bytes = await tts.synthesize(
                                        question_text,
                                        recruiter_id=recruiter_id_val,
                                        interview_id=interview_id_val,
                                        job_description_id=job_desc_id,
                                        candidate_id=candidate_id_val
                                    )
                                    
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
                    # Get context for logging
                    interview_id_val = UUID(interview["id"]) if interview else None
                    job_desc_id = UUID(job_description["id"]) if job_description else None
                    candidate_id_val = UUID(interview["candidate_id"]) if interview and interview.get("candidate_id") else None
                    recruiter_id_val = UUID(job_description["recruiter_id"]) if job_description and job_description.get("recruiter_id") else None
                    answer_text = await stt.transcribe_chunk(
                        audio_bytes,
                        language="en",
                        recruiter_id=recruiter_id_val,
                        interview_id=interview_id_val,
                        job_description_id=job_desc_id,
                        candidate_id=candidate_id_val
                    )
                    
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
                    
                    # If waiting for final message, treat this audio as the final message
                    if waiting_for_final_message:
                        logger.info(
                            "Final message received via audio in voice mode",
                            interview_id=str(interview["id"]) if interview else None,
                            transcription_length=len(answer_text)
                        )
                        # Treat transcribed audio as final message
                        # Build transcript from all responses before completing
                        try:
                            all_responses = db.service_client.table("interview_responses").select("question_id, response_text").eq("interview_id", str(interview["id"])).order("created_at").execute()
                            
                            transcript_parts = []
                            for resp in (all_responses.data or []):
                                response_text = resp.get("response_text") or ""
                                if response_text:
                                    transcript_parts.append(response_text)
                            
                            # Add final message (transcribed audio)
                            if answer_text:
                                transcript_parts.append(answer_text)
                            
                            transcript = "\n\n".join(transcript_parts) if transcript_parts else None
                            logger.info("Built transcript for completion from audio final message", interview_id=str(interview["id"]), transcript_length=len(transcript) if transcript else 0, num_responses=len(transcript_parts))
                        except Exception as transcript_err:
                            logger.warning("Failed to build transcript", error=str(transcript_err), interview_id=str(interview["id"]))
                            transcript = None
                        
                        # Send closing message
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "interview_complete",
                                    "message": "Thank you so much for taking the time to interview with us today. We really appreciate your interest in this role and the insights you've shared. We'll be reviewing your responses and will be in touch with you soon. Have a great day!",
                                }
                            )
                        )
                        
                        # Aggregate all interview audio files before completing
                        full_audio_path = None
                        if interview_mode == "voice":
                            try:
                                full_audio_path = await aggregate_interview_audio(UUID(interview["id"]))
                            except Exception as audio_err:
                                logger.warning("Failed to aggregate interview audio", error=str(audio_err), interview_id=str(interview["id"]))
                                # Continue without full audio - individual files are still available
                        
                        # Mark interview as completed
                        logger.info("Starting interview completion process from audio final message", interview_id=str(interview["id"]), interview_mode=interview_mode)
                        try:
                            # Complete the interview - this updates the status to "completed"
                            completed_interview = await InterviewService.complete_interview(
                                interview_id=UUID(interview["id"]),
                                transcript=transcript,
                                audio_file_path=full_audio_path
                            )
                            logger.info(
                                "Interview marked as completed successfully",
                                interview_id=str(interview["id"]),
                                completed_at=completed_interview.get("completed_at")
                            )
                        except Exception as complete_err:
                            logger.error("Failed to mark interview as completed", error=str(complete_err), interview_id=str(interview["id"]), exc_info=True)
                            # Don't fail the websocket - interview data is still saved
                        
                        logger.info("Interview completed in voice mode via audio final message", interview_id=str(interview["id"]))
                        # Close the connection gracefully
                        await websocket.close()
                        return
                    
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
                            
                            # Get question order index for file naming
                            question_order_idx = question_order_map.get(question_id)
                            
                            # Upload response audio with improved naming
                            storage_path = await StorageService.upload_response_audio(
                                UUID(interview["id"]),
                                UUID(question_id),
                                audio_bytes,
                                response_index=1,  # Could track multiple responses per question
                                file_extension=file_extension,
                                candidate_name=candidate_name,
                                question_order_index=question_order_idx
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
                    
                    # Get audio path if available (for voice mode)
                    audio_path = None
                    if interview_mode == "voice" and question_id in response_audio_paths:
                        audio_path = response_audio_paths[question_id]
                        # Remove from tracking dict since we're using it now
                        del response_audio_paths[question_id]
                    
                    # Analyze response and store it (with timeout)
                    logger.info("Starting response analysis", question_id=question_id, questions_asked=questions_asked, has_audio=bool(audio_path))
                    try:
                        analysis = await asyncio.wait_for(
                            interview_ai.process_response(
                                UUID(interview["id"]),
                                UUID(question_id),
                                answer_text,
                                job_description or {},
                                cv_text,
                                response_audio_path=audio_path  # Pass audio path directly
                            ),
                            timeout=45.0  # 45 second timeout for response analysis
                        )

                        # Update / create interview-level report (non-blocking for UX if it fails)
                        try:
                            await InterviewReportService.upsert_from_analysis(
                                UUID(interview["id"]),
                                analysis,
                                question_id=UUID(question_id),  # Pass question_id for tracking
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

                    # Check time limit (20 minutes maximum)
                    elapsed_time = time.time() - interview_start_time if interview_start_time else 0
                    time_remaining = MAX_INTERVIEW_DURATION_SECONDS - elapsed_time
                    
                    # Check if we've exceeded time limit
                    if elapsed_time >= MAX_INTERVIEW_DURATION_SECONDS:
                        logger.info("Interview time limit reached (20 minutes)", interview_id=str(interview["id"]), elapsed_seconds=elapsed_time)
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We've reached the end of our interview time. Thank you so much for your responses. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                        continue
                    
                    # Check if all core questions have been asked
                    if core_questions_asked >= MAX_CORE_QUESTIONS:
                        # All core questions completed - ask for final message
                        waiting_for_final_message = True
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "final_message_request",
                                    "message": "We've completed our core questions. Thank you so much for your responses. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                }
                            )
                        )
                        continue
                    
                    # Warn if approaching time limit (18 minutes = 1080 seconds)
                    if time_remaining <= 120 and time_remaining > 60:  # 2 minutes remaining
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "info",
                                    "message": "We have about 2 minutes left. Let's make sure we cover the remaining questions.",
                                }
                            )
                        )

                    response_quality = analysis.get("quality") or analysis.get("response_quality", "adequate")
                    non_answer_type = analysis.get("non_answer_type")  # Extract non-answer type if detected
                    
                    # Determine if we should ask a follow-up question
                    should_ask_followup = False
                    followup_reason = None
                    
                    # Get current question to check if it's a core question
                    current_q_response = db.service_client.table("interview_questions").select("question_type, order_index").eq("id", str(question_id)).execute()
                    current_question = current_q_response.data[0] if current_q_response.data else {}
                    is_core_question = current_question.get("question_type", "") != "warmup" and current_question.get("order_index", 0) > 0
                    
                    # Check follow-up conditions
                    followup_count = followups_per_question.get(question_id, 0)
                    
                    # Ask follow-up if:
                    # 1. It's a core question (not warmup)
                    # 2. Follow-up count is below limit
                    # 3. Response needs clarification (weak/unclear) OR there's a non-answer
                    # 4. Enough time remaining (> 3 minutes)
                    if (is_core_question and 
                        followup_count < MAX_FOLLOWUPS_PER_QUESTION and
                        time_remaining > 180 and  # At least 3 minutes remaining
                        (response_quality == "weak" or non_answer_type or response_quality == "unclear")):
                        should_ask_followup = True
                        if non_answer_type:
                            followup_reason = f"non_answer_{non_answer_type}"
                        elif response_quality == "weak":
                            followup_reason = "needs_clarification"
                        elif response_quality == "unclear":
                            followup_reason = "unclear_response"
                    
                    # Log follow-up decision
                    logger.info(
                        "Follow-up decision",
                        question_id=question_id,
                        should_ask_followup=should_ask_followup,
                        followup_reason=followup_reason,
                        followup_count=followup_count,
                        max_followups=MAX_FOLLOWUPS_PER_QUESTION,
                        is_core=is_core_question,
                        time_remaining=time_remaining,
                        response_quality=response_quality
                    )
                    
                    # Generate and ask follow-up if conditions met
                    if should_ask_followup:
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
                                has_followup=bool(followup),
                                reason=followup_reason
                            )
                            
                            if followup:
                                # Increment follow-up count for this question
                                followups_per_question[question_id] = followup_count + 1
                                questions_asked += 1  # Track total questions
                                # Note: Follow-ups don't increment core_questions_asked
                                
                                followup_id = followup["id"]
                                current_question_id = followup_id
                                question_text = followup["question_text"]
                                
                                # Update question order map for the new followup question
                                # Fetch the question's order_index from DB
                                try:
                                    followup_q_response = db.service_client.table("interview_questions").select("order_index").eq("id", str(followup_id)).execute()
                                    if followup_q_response.data:
                                        order_idx = followup_q_response.data[0].get("order_index", 0)
                                        question_order_map[followup_id] = order_idx + 1  # 1-based
                                except Exception as e:
                                    logger.warning("Failed to fetch order_index for followup question", question_id=str(followup_id), error=str(e))
                                
                                # Send question (text mode) or generate audio (voice mode)
                                if interview_mode == "voice":
                                    # Generate TTS audio for question
                                    try:
                                        await websocket.send_text(
                                            json.dumps({"type": "audio_question_start"})
                                        )
                                        
                                        # Generate audio
                                        logger.info("Starting TTS synthesis for followup", question_id=followup["id"], text_length=len(question_text))
                                        # Get context for logging
                                        interview_id_val = UUID(interview["id"]) if interview else None
                                        job_desc_id = UUID(job_description["id"]) if job_description else None
                                        candidate_id_val = UUID(interview["candidate_id"]) if interview and interview.get("candidate_id") else None
                                        recruiter_id_val = UUID(job_description["recruiter_id"]) if job_description and job_description.get("recruiter_id") else None
                                        audio_bytes = await tts.synthesize(
                                            question_text,
                                            recruiter_id=recruiter_id_val,
                                            interview_id=interview_id_val,
                                            job_description_id=job_desc_id,
                                            candidate_id=candidate_id_val
                                        )
                                        
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
                                # No follow-up needed - move to next core question
                                # Find next unanswered core question
                                try:
                                    all_questions_response = (
                                        db.service_client.table("interview_questions")
                                        .select("id, question_text, order_index, question_type")
                                        .eq("interview_id", str(interview["id"]))
                                        .order("order_index")
                                        .execute()
                                    )
                                    all_questions = all_questions_response.data or []
                                    answered_questions_response = (
                                        db.service_client.table("interview_responses")
                                        .select("question_id")
                                        .eq("interview_id", str(interview["id"]))
                                        .execute()
                                    )
                                    answered_question_ids = {r["question_id"] for r in (answered_questions_response.data or [])}
                                    next_core_question = None
                                    for q in all_questions:
                                        q_id = q["id"]
                                        q_type = q.get("question_type", "")
                                        q_order = q.get("order_index", 0)
                                        if q_id in answered_question_ids or q_type == "warmup" or q_order == 0:
                                            continue
                                        next_core_question = q
                                        break
                                    if next_core_question:
                                        questions_asked += 1
                                        core_questions_asked += 1
                                        next_question_id = next_core_question["id"]
                                        current_question_id = next_question_id
                                        next_question_text = next_core_question["question_text"]
                                        order_idx = next_core_question.get("order_index", 0)
                                        question_order_map[next_question_id] = order_idx + 1
                                        if interview_mode == "voice":
                                            try:
                                                await websocket.send_text(json.dumps({"type": "audio_question_start"}))
                                                interview_id_val = UUID(interview["id"]) if interview else None
                                                job_desc_id = UUID(job_description["id"]) if job_description else None
                                                candidate_id_val = UUID(interview["candidate_id"]) if interview and interview.get("candidate_id") else None
                                                recruiter_id_val = UUID(job_description["recruiter_id"]) if job_description and job_description.get("recruiter_id") else None
                                                audio_bytes = await tts.synthesize(
                                                    next_question_text,
                                                    recruiter_id=recruiter_id_val,
                                                    interview_id=interview_id_val,
                                                    job_description_id=job_desc_id,
                                                    candidate_id=candidate_id_val
                                                )
                                                if not audio_bytes or not isinstance(audio_bytes, bytes):
                                                    raise ValueError("TTS returned invalid audio")
                                                await websocket.send_bytes(audio_bytes)
                                                await websocket.send_text(json.dumps({"type": "audio_question_end"}))
                                                await websocket.send_text(
                                                    json.dumps({"type": "question", "question_id": next_question_id, "text": next_question_text})
                                                )
                                            except Exception as e:
                                                logger.error("TTS failed for next core question, falling back to text", error=str(e))
                                                await websocket.send_text(
                                                    json.dumps({"type": "question", "question_id": next_question_id, "text": next_question_text})
                                                )
                                        else:
                                            await websocket.send_text(
                                                json.dumps({"type": "question", "question_id": next_question_id, "text": next_question_text})
                                            )
                                    else:
                                        waiting_for_final_message = True
                                        await websocket.send_text(
                                            json.dumps({
                                                "type": "final_message_request",
                                                "message": "We've completed our questions. Thank you so much for your responses. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                                            })
                                        )
                                except Exception as e:
                                    logger.error("Error finding next core question (audio_end)", error=str(e), exc_info=True)
                                    waiting_for_final_message = True
                                    await websocket.send_text(
                                        json.dumps({
                                            "type": "final_message_request",
                                            "message": "We're coming to the end of our interview. Is there anything else you'd like to share with us?",
                                        })
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

                # Get audio path if available (for voice mode)
                audio_path = None
                if interview_mode == "voice" and question_id in response_audio_paths:
                    audio_path = response_audio_paths[question_id]
                    # Remove from tracking dict since we're using it now
                    del response_audio_paths[question_id]
                
                # Analyze response and store it (with timeout)
                logger.info("Starting response analysis", question_id=question_id, questions_asked=questions_asked, has_audio=bool(audio_path))
                try:
                    analysis = await asyncio.wait_for(
                        interview_ai.process_response(
                            UUID(interview["id"]),
                            UUID(question_id),
                            answer_text,
                            job_description or {},
                            cv_text,
                            response_audio_path=audio_path  # Pass audio path directly
                        ),
                        timeout=45.0  # 45 second timeout for response analysis
                    )

                    # Update / create interview-level report (non-blocking for UX if it fails)
                    try:
                        await InterviewReportService.upsert_from_analysis(
                            UUID(interview["id"]),
                            analysis,
                            question_id=UUID(question_id),  # Pass question_id for tracking
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

                # Check time limit (20 minutes maximum)
                elapsed_time = time.time() - interview_start_time if interview_start_time else 0
                time_remaining = MAX_INTERVIEW_DURATION_SECONDS - elapsed_time
                
                # Check if we've exceeded time limit
                if elapsed_time >= MAX_INTERVIEW_DURATION_SECONDS:
                    logger.info("Interview time limit reached (20 minutes)", interview_id=str(interview["id"]), elapsed_seconds=elapsed_time)
                    waiting_for_final_message = True
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final_message_request",
                                "message": "We've reached the end of our interview time. Thank you so much for your responses. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                            }
                        )
                    )
                    continue
                
                # Check if all core questions have been asked
                # Determine if current question is core or follow-up
                current_q_response = db.service_client.table("interview_questions").select("question_type, order_index").eq("id", str(question_id)).execute()
                current_question = current_q_response.data[0] if current_q_response.data else {}
                is_current_core = current_question.get("question_type", "") != "warmup" and current_question.get("order_index", 0) > 0
                
                # If current question was a core question and we haven't counted it yet, increment
                if is_current_core and question_id not in followups_per_question:
                    core_questions_asked += 1
                
                if core_questions_asked >= MAX_CORE_QUESTIONS:
                    # All core questions completed - ask for final message
                    waiting_for_final_message = True
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "final_message_request",
                                "message": "We've completed our core questions. Thank you so much for your responses. Is there anything else you'd like to share with us, or any questions you have about the role or our organization?",
                            }
                        )
                    )
                    continue
                
                # Warn if approaching time limit (18 minutes = 1080 seconds)
                if time_remaining <= 120 and time_remaining > 60:  # 2 minutes remaining
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "info",
                                "message": "We have about 2 minutes left. Let's make sure we cover the remaining questions.",
                            }
                        )
                    )

                response_quality = analysis.get("quality") or analysis.get("response_quality", "adequate")
                non_answer_type = analysis.get("non_answer_type")  # Extract non-answer type if detected
                
                # Determine if we should ask a follow-up question
                should_ask_followup = False
                followup_reason = None
                
                # Get current question to check if it's a core question
                is_core_question = current_question.get("question_type", "") != "warmup" and current_question.get("order_index", 0) > 0
                
                # Check follow-up conditions
                followup_count = followups_per_question.get(question_id, 0)
                
                # Ask follow-up if:
                # 1. It's a core question (not warmup)
                # 2. Follow-up count is below limit
                # 3. Response needs clarification (weak/unclear) OR there's a non-answer
                # 4. Enough time remaining (> 3 minutes)
                if (is_core_question and 
                    followup_count < MAX_FOLLOWUPS_PER_QUESTION and
                    time_remaining > 180 and  # At least 3 minutes remaining
                    (response_quality == "weak" or non_answer_type or response_quality == "unclear")):
                    should_ask_followup = True
                    if non_answer_type:
                        followup_reason = f"non_answer_{non_answer_type}"
                    elif response_quality == "weak":
                        followup_reason = "needs_clarification"
                    elif response_quality == "unclear":
                        followup_reason = "unclear_response"
                
                # Log follow-up decision
                logger.info(
                    "Follow-up decision (text mode)",
                    question_id=question_id,
                    should_ask_followup=should_ask_followup,
                    followup_reason=followup_reason,
                    followup_count=followup_count,
                    max_followups=MAX_FOLLOWUPS_PER_QUESTION,
                    is_core=is_core_question,
                    time_remaining=time_remaining,
                    response_quality=response_quality
                )
                
                # Generate and ask follow-up if conditions met
                if should_ask_followup:
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
                            "Follow-up question generated successfully (text mode)",
                            followup_question_id=followup.get("id") if followup else None,
                            has_followup=bool(followup),
                            reason=followup_reason
                        )

                        if followup:
                            # Increment follow-up count for this question
                            followups_per_question[question_id] = followup_count + 1
                            questions_asked += 1  # Track total questions
                            # Note: Follow-ups don't increment core_questions_asked
                            
                            followup_id = followup["id"]
                            current_question_id = followup_id
                            question_text = followup["question_text"]
                            
                            # Update question order map for the new followup question
                            # Fetch the question's order_index from DB
                            try:
                                followup_q_response = db.service_client.table("interview_questions").select("order_index").eq("id", str(followup_id)).execute()
                                if followup_q_response.data:
                                    order_idx = followup_q_response.data[0].get("order_index", 0)
                                    question_order_map[followup_id] = order_idx + 1  # 1-based
                            except Exception as e:
                                logger.warning("Failed to fetch order_index for followup question", question_id=str(followup_id), error=str(e))
                            
                            # Send question (text mode) or generate audio (voice mode)
                            if interview_mode == "voice":
                                # Generate TTS audio for question
                                try:
                                    await websocket.send_text(
                                        json.dumps({"type": "audio_question_start"})
                                    )
                                    
                                    # Generate audio
                                    logger.info("Starting TTS synthesis for followup", question_id=followup["id"], text_length=len(question_text))
                                    # Get context for logging
                                    interview_id_val = UUID(interview["id"]) if interview else None
                                    job_desc_id = UUID(job_description["id"]) if job_description else None
                                    candidate_id_val = UUID(interview["candidate_id"]) if interview and interview.get("candidate_id") else None
                                    recruiter_id_val = UUID(job_description["recruiter_id"]) if job_description and job_description.get("recruiter_id") else None
                                    audio_bytes = await tts.synthesize(
                                        question_text,
                                        recruiter_id=recruiter_id_val,
                                        interview_id=interview_id_val,
                                        job_description_id=job_desc_id,
                                        candidate_id=candidate_id_val
                                    )
                                    
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
                
                # Build transcript from all responses before completing
                try:
                    all_responses = db.service_client.table("interview_responses").select("question_id, response_text").eq("interview_id", str(interview["id"])).order("created_at").execute()
                    
                    transcript_parts = []
                    for resp in (all_responses.data or []):
                        response_text = resp.get("response_text") or ""
                        if response_text:
                            transcript_parts.append(response_text)
                    
                    # Add final message if provided
                    if final_message_text:
                        transcript_parts.append(final_message_text)
                    
                    transcript = "\n\n".join(transcript_parts) if transcript_parts else None
                    logger.info("Built transcript for completion", interview_id=str(interview["id"]), transcript_length=len(transcript) if transcript else 0, num_responses=len(transcript_parts))
                except Exception as transcript_err:
                    logger.warning("Failed to build transcript", error=str(transcript_err), interview_id=str(interview["id"]))
                    transcript = None
                
                # Send closing message
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "interview_complete",
                            "message": "Thank you so much for taking the time to interview with us today. We really appreciate your interest in this role and the insights you've shared. We'll be reviewing your responses and will be in touch with you soon. Have a great day!",
                        }
                    )
                )
                
                # Aggregate all interview audio files before completing
                full_audio_path = None
                if interview_mode == "voice":
                    try:
                        full_audio_path = await aggregate_interview_audio(UUID(interview["id"]))
                    except Exception as audio_err:
                        logger.warning("Failed to aggregate interview audio", error=str(audio_err), interview_id=str(interview["id"]))
                        # Continue without full audio - individual files are still available
                
                # Mark interview as completed
                logger.info("Starting interview completion process", interview_id=str(interview["id"]), interview_mode=interview_mode)
                try:
                    # Complete the interview - this updates the status to "completed"
                    completed_interview = await InterviewService.complete_interview(
                        UUID(interview["id"]),
                        transcript=transcript,
                        audio_file_path=full_audio_path
                    )
                    logger.info(
                        "Interview marked as completed successfully",
                        interview_id=str(interview["id"]),
                        status=completed_interview.get("status"),
                        completed_at=completed_interview.get("completed_at")
                    )
                    
                    # Save full interview audio if in voice mode and we have accumulated audio
                    # Note: For full interview audio, we'd need to accumulate all audio chunks
                    # This is a simplified version - in production, you might want to accumulate
                    # all audio throughout the interview
                    if interview_mode == "voice":
                        # Optionally save a combined audio file if we track it
                        # For now, individual response audio files are saved above
                        logger.info("Interview completed in voice mode", interview_id=str(interview["id"]))
                    
                    # Send confirmation email to candidate (non-blocking - don't fail interview if email fails)
                    try:
                        # Fetch candidate details
                        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(interview["candidate_id"])).execute()
                        if candidate_response.data and candidate_response.data[0].get("email"):
                            candidate = candidate_response.data[0]
                            candidate_email = candidate["email"]
                            candidate_name = candidate.get("full_name", "Candidate")
                            
                            # Fetch job description to get recruiter_id and job title
                            job_response = db.service_client.table("job_descriptions").select("recruiter_id, title").eq("id", str(interview["job_description_id"])).execute()
                            if job_response.data:
                                job = job_response.data[0]
                                recruiter_id = UUID(job["recruiter_id"])
                                job_title = job.get("title", "the position")
                                
                                # Create email content
                                subject = f"Thank You - We've Received Your Interview"
                                body_html = f"""
                                <p>Dear {candidate_name},</p>
                                
                                <p>Thank you for completing your interview for the <strong>{job_title}</strong> position. We have successfully received your interview responses.</p>
                                
                                <p>Our team will review your interview and we'll be in touch with you as soon as possible. We appreciate your time and interest in joining our organization.</p>
                                
                                <p>If you have any questions in the meantime, please don't hesitate to reach out to us.</p>
                                
                                <p>Best regards,<br>The Recruiting Team</p>
                                """
                                body_text = f"""
                                Dear {candidate_name},
                                
                                Thank you for completing your interview for the {job_title} position. We have successfully received your interview responses.
                                
                                Our team will review your interview and we'll be in touch with you as soon as possible. We appreciate your time and interest in joining our organization.
                                
                                If you have any questions in the meantime, please don't hesitate to reach out to us.
                                
                                Best regards,
                                The Recruiting Team
                                """
                                
                                # Send email (non-blocking - don't fail interview if email fails)
                                await EmailService.send_email(
                                    recruiter_id=recruiter_id,
                                    recipient_email=candidate_email,
                                    recipient_name=candidate_name,
                                    subject=subject,
                                    body_html=body_html,
                                    body_text=body_text,
                                    candidate_id=UUID(interview["candidate_id"]),
                                    job_description_id=UUID(interview["job_description_id"]),
                                )
                                logger.info("Interview completion confirmation email sent", interview_id=str(interview["id"]), candidate_email=candidate_email)
                            else:
                                logger.warning("Job description not found for interview completion email", interview_id=str(interview["id"]), job_id=str(interview["job_description_id"]))
                        else:
                            logger.warning("Candidate email not found for interview completion email", interview_id=str(interview["id"]), candidate_id=str(interview["candidate_id"]))
                    except Exception as email_err:
                        # Log error but don't fail the interview completion
                        logger.error("Failed to send interview completion email", error=str(email_err), interview_id=str(interview["id"]), exc_info=True)
                        
                except Exception as e:
                    logger.error("Error completing interview", error=str(e), interview_id=str(interview["id"]), exc_info=True)
                    # Even if completion fails, we still want to close the connection
                    # The interview might still be marked as completed if the error occurred after the DB update
                
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
        logger.info("Voice interview websocket disconnected", ticket_code=ticket_code, interview_id=str(interview["id"]) if interview else None)
        
        # Auto-complete interview if it has responses but wasn't completed
        if interview and interview.get("status") in ["in_progress", "pending"]:
            try:
                # Check if interview has responses
                responses_check = db.service_client.table("interview_responses").select("id").eq("interview_id", str(interview["id"])).limit(1).execute()
                if responses_check.data and len(responses_check.data) > 0:
                    # Build transcript from responses
                    all_responses = db.service_client.table("interview_responses").select("question_id, response_text").eq("interview_id", str(interview["id"])).order("created_at").execute()
                    
                    transcript_parts = []
                    for resp in (all_responses.data or []):
                        response_text = resp.get("response_text") or ""
                        if response_text:
                            transcript_parts.append(response_text)
                    
                    transcript = "\n\n".join(transcript_parts) if transcript_parts else None
                    
                    logger.info("Auto-completing interview after disconnect", interview_id=str(interview["id"]), has_responses=True, transcript_length=len(transcript) if transcript else 0)
                    
                    # Complete the interview
                    await InterviewService.complete_interview(
                        UUID(interview["id"]),
                        transcript=transcript
                    )
                    logger.info("Interview auto-completed after disconnect", interview_id=str(interview["id"]))
            except Exception as e:
                logger.error("Error auto-completing interview after disconnect", error=str(e), interview_id=str(interview["id"]) if interview else None, exc_info=True)
        return
    except Exception as e:
        logger.error("Voice interview websocket error", ticket_code=ticket_code, error=str(e))
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": "Internal server error"}))
        except Exception:
            pass
        finally:
            await websocket.close()


