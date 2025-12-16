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
                new_rec = InterviewReportService._derive_recommendation(
                    quality, update_data.red_flags or existing.get("red_flags") or [], current_rec
                )
                update_data.hiring_recommendation = new_rec

                # Determine experience level if not already set
                if not existing.get("experience_level"):
                    exp_level = await InterviewReportService._determine_experience_level(interview_id)
                    if exp_level:
                        update_data.experience_level = exp_level

                # Generate recommendation justification if not already set or if recommendation changed
                if not existing.get("recommendation_justification") or current_rec != new_rec:
                    update_data.recommendation_justification = (
                        InterviewReportService._generate_recommendation_justification(
                            new_rec,
                            update_data.skill_match_score or existing.get("skill_match_score"),
                            update_data.strengths or existing.get("strengths"),
                            update_data.weaknesses or existing.get("weaknesses"),
                            update_data.red_flags or existing.get("red_flags"),
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
                hiring_rec = InterviewReportService._derive_recommendation(quality, red_flags, None)
                
                # Generate recommendation justification
                justification = InterviewReportService._generate_recommendation_justification(
                    hiring_rec,
                    alignment_score,
                    strengths,
                    weaknesses,
                    red_flags,
                )
                
                # Determine experience level
                exp_level = await InterviewReportService._determine_experience_level(interview_id)
                
                create_data = InterviewReportCreate(
                    interview_id=interview_id,
                    strengths=strengths or None,
                    weaknesses=weaknesses or None,
                    red_flags=red_flags or None,
                    skill_match_score=alignment_score,
                    experience_level=exp_level,
                    hiring_recommendation=hiring_rec,
                    recommendation_justification=justification,
                    full_report={"latest_analysis": analysis},
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

    @staticmethod
    def _generate_recommendation_justification(
        hiring_recommendation: str,
        skill_match_score: Decimal | None,
        strengths: List[str] | None,
        weaknesses: List[str] | None,
        red_flags: List[str] | None,
    ) -> str:
        """Generate a human-readable justification for the hiring recommendation."""
        justification_parts = []
        
        # Start with the recommendation
        rec_map = {
            "strong_hire": "Strong Hire",
            "hire": "Hire",
            "neutral": "Neutral",
            "no_hire": "No Hire"
        }
        rec_text = rec_map.get(hiring_recommendation, hiring_recommendation)
        
        # Add skill match score context
        if skill_match_score is not None:
            score_val = float(skill_match_score)
            if score_val >= 70:
                justification_parts.append(f"Strong skill alignment with the role (match score: {score_val:.0f}%)")
            elif score_val >= 50:
                justification_parts.append(f"Moderate skill alignment (match score: {score_val:.0f}%)")
            else:
                justification_parts.append(f"Limited skill alignment (match score: {score_val:.0f}%)")
        
        # Add strengths
        if strengths:
            strengths_list = strengths[:3]  # Limit to top 3
            if len(strengths_list) == 1:
                justification_parts.append(f"Notable strength: {strengths_list[0]}")
            elif len(strengths_list) > 1:
                justification_parts.append(f"Key strengths include: {', '.join(strengths_list[:-1])}, and {strengths_list[-1]}")
        
        # Add weaknesses
        if weaknesses:
            weaknesses_list = weaknesses[:3]  # Limit to top 3
            if len(weaknesses_list) == 1:
                justification_parts.append(f"Area for improvement: {weaknesses_list[0]}")
            elif len(weaknesses_list) > 1:
                justification_parts.append(f"Areas for improvement include: {', '.join(weaknesses_list[:-1])}, and {weaknesses_list[-1]}")
        
        # Add red flags if any
        if red_flags:
            flags_list = red_flags[:2]  # Limit to top 2
            if len(flags_list) == 1:
                justification_parts.append(f"Concern identified: {flags_list[0]}")
            else:
                justification_parts.append(f"Concerns identified: {', '.join(flags_list)}")
        
        # Combine into a paragraph
        if justification_parts:
            return f"{rec_text} recommendation. " + " ".join(justification_parts) + "."
        else:
            return f"{rec_text} recommendation based on interview performance."

    @staticmethod
    async def _determine_experience_level(
        interview_id: UUID,
    ) -> str | None:
        """Determine candidate experience level from CV and interview responses."""
        try:
            # Get interview to access CV
            interview_resp = (
                db.service_client.table("interviews")
                .select("candidate_id, job_description_id")
                .eq("id", str(interview_id))
                .execute()
            )
            if not interview_resp.data:
                return None
            
            interview = interview_resp.data[0]
            candidate_id = interview.get("candidate_id")
            
            # Try to get experience level from CV parsed data
            cv_resp = (
                db.service_client.table("cvs")
                .select("parsed_json")
                .eq("candidate_id", str(candidate_id))
                .order("uploaded_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if cv_resp.data and cv_resp.data[0].get("parsed_json"):
                cv_json = cv_resp.data[0]["parsed_json"]
                if isinstance(cv_json, dict):
                    # Check for explicit experience_level
                    if "experience_level" in cv_json:
                        level = str(cv_json["experience_level"]).lower()
                        if level in ["junior", "mid", "senior"]:
                            return level
                    
                    # Infer from years of experience if available
                    if "years_of_experience" in cv_json:
                        try:
                            years = float(str(cv_json["years_of_experience"]))
                            if years >= 5:
                                return "senior"
                            elif years >= 2:
                                return "mid"
                            else:
                                return "junior"
                        except (ValueError, TypeError):
                            pass
                    
                    # Check work experience section
                    if "experience" in cv_json:
                        exp = cv_json["experience"]
                        if isinstance(exp, list) and len(exp) > 0:
                            # Count years from experience entries
                            total_years = 0
                            for entry in exp:
                                if isinstance(entry, dict) and "years" in entry:
                                    try:
                                        total_years += float(str(entry["years"]))
                                    except (ValueError, TypeError):
                                        pass
                            
                            if total_years >= 5:
                                return "senior"
                            elif total_years >= 2:
                                return "mid"
                            elif total_years > 0:
                                return "junior"
            
            # Fallback: check job description requirements
            job_id = interview.get("job_description_id")
            if job_id:
                job_resp = (
                    db.service_client.table("job_descriptions")
                    .select("experience_level")
                    .eq("id", str(job_id))
                    .execute()
                )
                if job_resp.data and job_resp.data[0].get("experience_level"):
                    return str(job_resp.data[0]["experience_level"]).lower()
            
            return None
        except Exception as e:
            logger.error("Error determining experience level", error=str(e), interview_id=str(interview_id))
            return None

    @staticmethod
    async def backfill_missing_fields(interview_id: UUID) -> Dict[str, Any] | None:
        """
        Backfill missing experience_level and recommendation_justification for an existing report.
        Useful for fixing reports created before these fields were implemented.
        """
        try:
            # Get existing report
            report_resp = (
                db.service_client.table("interview_reports")
                .select("*")
                .eq("interview_id", str(interview_id))
                .execute()
            )
            
            if not report_resp.data:
                logger.warning("No report found for interview", interview_id=str(interview_id))
                return None
            
            existing = report_resp.data[0]
            needs_update = False
            update_data = InterviewReportUpdate()
            
            # Backfill experience_level if missing
            if not existing.get("experience_level"):
                exp_level = await InterviewReportService._determine_experience_level(interview_id)
                if exp_level:
                    update_data.experience_level = exp_level
                    needs_update = True
            
            # Backfill recommendation_justification if missing
            if not existing.get("recommendation_justification"):
                hiring_rec = existing.get("hiring_recommendation") or "neutral"
                justification = InterviewReportService._generate_recommendation_justification(
                    hiring_rec,
                    InterviewReportService._to_decimal(existing.get("skill_match_score")),
                    existing.get("strengths"),
                    existing.get("weaknesses"),
                    existing.get("red_flags"),
                )
                update_data.recommendation_justification = justification
                needs_update = True
            
            if needs_update:
                resp = (
                    db.service_client.table("interview_reports")
                    .update(update_data.model_dump(mode="json", exclude_unset=True))
                    .eq("interview_id", str(interview_id))
                    .execute()
                )
                logger.info("Backfilled missing fields", interview_id=str(interview_id))
                return (resp.data or [existing])[0]
            
            return existing
        except Exception as e:
            logger.error("Error backfilling missing fields", error=str(e), interview_id=str(interview_id))
            return None


