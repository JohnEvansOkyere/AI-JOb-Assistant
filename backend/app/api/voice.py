from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
import json
import asyncio

from app.config import settings
from app.services.interview_service import InterviewService
from app.services.interview_ai_service import InterviewAIService
from app.services.ticket_service import TicketService
from app.services.interview_report_service import InterviewReportService
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
    WebSocket endpoint for **text-based** realtime interviews (no audio yet).

    Protocol (JSON text messages):
    - Client → server:
      { "type": "start" }
        - Creates & starts interview from ticket, sends first question.
      { "type": "answer", "question_id": "<uuid>", "text": "candidate answer" }
        - Saves response, analyzes it, and sends follow-up question.

    - Server → client:
      { "type": "error", "message": "..." }
      { "type": "question", "question_id": "<uuid>", "text": "..." }
      { "type": "analysis", ... }  (optional, future use)
    """

    await websocket.accept()

    # Placeholder providers (not yet used for text-only mode but initialized for future audio support)
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

    try:
        # Validate ticket first
        try:
            ticket = await TicketService.validate_ticket(ticket_code)
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
            raw = await websocket.receive_text()
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
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "question",
                                        "question_id": first_q["id"],
                                        "text": first_q["question_text"],
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

            elif msg_type == "answer":
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

                    if followup:
                        questions_asked += 1
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "question",
                                    "question_id": followup["id"],
                                    "text": followup["question_text"],
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


