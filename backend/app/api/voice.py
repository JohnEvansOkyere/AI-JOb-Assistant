from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
import json

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

                    # Generate initial questions and send the first one
                    questions = await interview_ai.generate_initial_questions(
                        UUID(interview["id"]),
                        job_description or {},
                        cv_text,
                        num_questions=5,
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
                                    "message": "Failed to generate initial question",
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

                # Analyze response and store it
                analysis = await interview_ai.process_response(
                    UUID(interview["id"]),
                    UUID(question_id),
                    answer_text,
                    job_description or {},
                    cv_text,
                )

                # Update / create interview-level report (non-blocking for UX if it fails)
                await InterviewReportService.upsert_from_analysis(
                    UUID(interview["id"]),
                    analysis,
                )

                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "analysis",
                            "question_id": question_id,
                            "analysis": analysis,
                        }
                    )
                )

                # Decide whether to ask a follow-up based on quality and question limit
                if questions_asked >= MAX_QUESTIONS:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "info",
                                "message": "We have reached the end of the interview for now. Thank you for your time.",
                            }
                        )
                    )
                    continue

                response_quality = analysis.get("quality") or analysis.get("response_quality", "adequate")
                followup = await interview_ai.generate_followup_question(
                    UUID(interview["id"]),
                    job_description or {},
                    cv_text,
                    UUID(question_id),
                    response_quality,
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
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "info",
                                "message": "No further questions. Interview can be completed.",
                            }
                        )
                    )

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


