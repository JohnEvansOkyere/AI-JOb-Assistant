"""
Interview Report Service
Aggregates per-question analyses into an interview-level report.
"""

from __future__ import annotations

from typing import Dict, Any, List
from uuid import UUID
from decimal import Decimal

from app.models.interview_report import InterviewReportCreate, InterviewReportUpdate
from app.database import db
import structlog

logger = structlog.get_logger()


class InterviewReportService:
    """Service for creating and updating interview reports."""

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        try:
            if value is None:
                return None
            return Decimal(str(value))
        except Exception:
            return None

    @staticmethod
    def _merge_lists(base: List[str] | None, extra: List[str] | None) -> List[str] | None:
        if not base and not extra:
            return None
        base = base or []
        extra = extra or []
        # Preserve order, avoid duplicates
        seen = set()
        merged: List[str] = []
        for item in base + extra:
            if not item:
                continue
            if item not in seen:
                seen.add(item)
                merged.append(item)
        return merged or None

    @staticmethod
    async def upsert_from_analysis(
        interview_id: UUID,
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Upsert an interview_report row using the latest per-question analysis.

        This keeps things simple for now:
        - Aggregates strengths / weaknesses / red_flags.
        - Tracks a simple average skill_match_score based on alignment_score.
        - Stores the latest analysis payload in full_report["latest_analysis"].
        - Sets a coarse hiring_recommendation based on quality + red flags.
        """
        try:
            # Load existing report, if any
            existing_resp = (
                db.service_client.table("interview_reports")
                .select("*")
                .eq("interview_id", str(interview_id))
                .execute()
            )
            existing = (existing_resp.data or [None])[0]

            strengths = analysis.get("strengths") or []
            weaknesses = analysis.get("weaknesses") or []
            red_flags = analysis.get("red_flags") or []
            quality = (analysis.get("quality") or "").lower()
            alignment_score = InterviewReportService._to_decimal(
                analysis.get("alignment_score") or analysis.get("relevance_score")
            )

            # Provide simple fallbacks when AI did not return detailed lists
            if quality == "strong" and not strengths:
                strengths = ["Provides clear, detailed responses aligned with role requirements"]
            if quality == "weak" and not weaknesses:
                weaknesses = ["Responses are brief or lack specific, concrete examples"]

            if existing:
                # Merge into existing report
                update_data = InterviewReportUpdate(
                    strengths=InterviewReportService._merge_lists(
                        existing.get("strengths"), strengths
                    ),
                    weaknesses=InterviewReportService._merge_lists(
                        existing.get("weaknesses"), weaknesses
                    ),
                    red_flags=InterviewReportService._merge_lists(
                        existing.get("red_flags"), red_flags
                    ),
                    full_report={
                        **(existing.get("full_report") or {}),
                        "latest_analysis": analysis,
                    },
                )

                # Update skill_match_score as a simple moving average
                prev_score = existing.get("skill_match_score")
                if alignment_score is not None:
                    if prev_score is None:
                        update_data.skill_match_score = alignment_score
                    else:
                        try:
                            prev_dec = Decimal(str(prev_score))
                            update_data.skill_match_score = (prev_dec + alignment_score) / Decimal(
                                "2"
                            )
                        except Exception:
                            update_data.skill_match_score = alignment_score

                # Derive a coarse hiring recommendation
                current_rec = existing.get("hiring_recommendation")
                update_data.hiring_recommendation = (
                    InterviewReportService._derive_recommendation(
                        quality, update_data.red_flags or existing.get("red_flags") or [], current_rec
                    )
                )

                resp = (
                    db.service_client.table("interview_reports")
                    .update(update_data.model_dump(mode="json", exclude_unset=True))
                    .eq("interview_id", str(interview_id))
                    .execute()
                )
                report = (resp.data or [existing])[0]
            else:
                # Create a new report
                create_data = InterviewReportCreate(
                    interview_id=interview_id,
                    strengths=strengths or None,
                    weaknesses=weaknesses or None,
                    red_flags=red_flags or None,
                    skill_match_score=alignment_score,
                    full_report={"latest_analysis": analysis},
                    hiring_recommendation=InterviewReportService._derive_recommendation(
                        quality, red_flags, None
                    ),
                )
                resp = (
                    db.service_client.table("interview_reports")
                    .insert(create_data.model_dump(mode="json"))
                    .execute()
                )
                report = (resp.data or [None])[0] or {}

            logger.info("Interview report upserted", interview_id=str(interview_id))
            return report

        except Exception as e:
            logger.error(
                "Error upserting interview report",
                interview_id=str(interview_id),
                error=str(e),
            )
            # Do not break the interview flow on reporting issues
            return {}

    @staticmethod
    def _derive_recommendation(
        quality: str,
        red_flags: List[str],
        current: str | None,
    ) -> str:
        """Very simple heuristic for hiring recommendation."""
        if red_flags:
            return "no_hire"
        if quality == "strong":
            return "hire" if current is None else current
        if quality == "weak":
            return current or "neutral"
        return current or "neutral"


