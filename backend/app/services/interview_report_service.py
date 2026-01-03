"""
Interview Report Service
Aggregates per-question analyses into an interview-level report.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

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
        question_id: Optional[UUID] = None,
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
                existing_full_report = existing.get("full_report") or {}
                analysis_history = existing_full_report.get("analysis_history", [])
                
                # Add current analysis to history (limit to last 20 analyses to avoid bloat)
                analysis_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "question_id": str(question_id) if question_id else None,
                    "quality": quality,
                    "alignment_score": float(alignment_score) if alignment_score else None,
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "red_flags": red_flags,
                    "analysis": analysis,
                }
                analysis_history.append(analysis_entry)
                if len(analysis_history) > 20:
                    analysis_history = analysis_history[-20:]  # Keep last 20
                
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
                        **existing_full_report,
                        "latest_analysis": analysis,
                        "analysis_history": analysis_history,
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
                    full_report={
                        "latest_analysis": analysis,
                        "analysis_history": [{
                            "timestamp": datetime.utcnow().isoformat(),
                            "question_id": str(question_id) if question_id else None,
                            "quality": quality,
                            "alignment_score": float(alignment_score) if alignment_score else None,
                            "strengths": strengths,
                            "weaknesses": weaknesses,
                            "red_flags": red_flags,
                            "analysis": analysis,
                        }],
                    },
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
    def _get_question_weight(question_type: str, order_index: int) -> Decimal:
        """
        Get weight for a question based on type and order.
        
        Weights:
        - Core questions (skill_validation, experience, gap_probing, behavioral, motivation): 2.0
        - Follow-up questions: 1.0
        - Warmup: 0.5 (minimal impact on final score)
        """
        if question_type == "warmup" or order_index == 0:
            return Decimal("0.5")
        elif question_type in ["skill_validation", "experience", "gap_probing", "behavioral", "motivation", "skill", "experience"]:
            return Decimal("2.0")
        else:
            # Follow-ups or other types
            return Decimal("1.0")
    
    @staticmethod
    async def _load_all_question_analyses(interview_id: UUID) -> List[Dict[str, Any]]:
        """Load all questions, responses, and their analyses for the interview."""
        try:
            # Load all questions
            questions_resp = (
                db.service_client.table("interview_questions")
                .select("id, question_text, question_type, order_index, skill_category")
                .eq("interview_id", str(interview_id))
                .order("order_index")
                .execute()
            )
            questions = {q["id"]: q for q in (questions_resp.data or [])}
            
            # Load all responses
            responses_resp = (
                db.service_client.table("interview_responses")
                .select("question_id, response_text, created_at")
                .eq("interview_id", str(interview_id))
                .order("created_at")
                .execute()
            )
            
            # Load report to get analysis history
            report_resp = (
                db.service_client.table("interview_reports")
                .select("full_report")
                .eq("interview_id", str(interview_id))
                .execute()
            )
            full_report = report_resp.data[0].get("full_report", {}) if report_resp.data else {}
            analysis_history = full_report.get("analysis_history", [])
            
            # Build question-analysis pairs
            analyses = []
            for resp in (responses_resp.data or []):
                q_id = resp["question_id"]
                question = questions.get(q_id, {})
                
                # Try to find analysis for this question from history
                # Match by question_id first, then fallback to timestamp proximity
                analysis = None
                response_time = resp.get("created_at")
                
                if analysis_history:
                    # First try to match by question_id
                    for hist_entry in reversed(analysis_history):  # Start from most recent
                        if hist_entry.get("question_id") == str(q_id):
                            analysis = hist_entry.get("analysis", {})
                            break
                    
                    # If no match by question_id, try to match by response time proximity
                    if not analysis and response_time:
                        # Find analysis entry closest to response time
                        for hist_entry in reversed(analysis_history):
                            hist_analysis = hist_entry.get("analysis", {})
                            # If analysis has data, use it
                            if hist_analysis and (hist_analysis.get("strengths") or hist_analysis.get("weaknesses") or hist_analysis.get("quality")):
                                analysis = hist_analysis
                                break
                
                # If no analysis found, create a basic one from response quality indicators
                if not analysis:
                    # Try to infer quality from response length and content
                    response_text = resp.get("response_text", "")
                    if len(response_text) < 50:
                        quality = "weak"
                    elif len(response_text) > 200:
                        quality = "strong"
                    else:
                        quality = "adequate"
                    
                    analysis = {
                        "quality": quality,
                        "response_quality": quality,
                        "alignment_score": None,
                        "strengths": [],
                        "weaknesses": [],
                        "red_flags": [],
                    }
                
                analyses.append({
                    "question_id": q_id,
                    "question": question.get("question_text", ""),
                    "question_type": question.get("question_type", ""),
                    "order_index": question.get("order_index", 0),
                    "skill_category": question.get("skill_category"),
                    "response_text": resp.get("response_text", ""),
                    "analysis": analysis,
                    "created_at": resp.get("created_at"),
                })
            
            return analyses
        except Exception as e:
            logger.error("Error loading question analyses", error=str(e), interview_id=str(interview_id))
            return []
    
    @staticmethod
    async def _calculate_weighted_skill_match_score(interview_id: UUID) -> Decimal | None:
        """
        Calculate weighted skill match score based on all responses.
        
        Formula: Σ(score × weight) / Σ(weights)
        """
        try:
            analyses = await InterviewReportService._load_all_question_analyses(interview_id)
            
            if not analyses:
                return None
            
            total_weighted_score = Decimal("0")
            total_weight = Decimal("0")
            
            for item in analyses:
                analysis = item.get("analysis", {})
                alignment_score = InterviewReportService._to_decimal(
                    analysis.get("alignment_score") or analysis.get("relevance_score")
                )
                
                if alignment_score is None:
                    continue
                
                weight = InterviewReportService._get_question_weight(
                    item.get("question_type", ""),
                    item.get("order_index", 0)
                )
                
                total_weighted_score += alignment_score * weight
                total_weight += weight
            
            if total_weight == 0:
                return None
            
            return total_weighted_score / total_weight
        except Exception as e:
            logger.error("Error calculating weighted skill match score", error=str(e), interview_id=str(interview_id))
            return None
    
    @staticmethod
    async def _derive_comprehensive_recommendation(interview_id: UUID) -> str:
        """
        Generate recommendation based on ALL responses, not just the last one.
        
        Logic:
        - If any red flags: no_hire
        - Count strong/adequate/weak responses weighted by question priority
        - If >70% strong responses: strong_hire
        - If >50% strong+adequate responses: hire
        - If >50% weak responses: maybe/no_hire (depending on severity)
        """
        try:
            analyses = await InterviewReportService._load_all_question_analyses(interview_id)
            
            if not analyses:
                return "neutral"
            
            # Check for red flags first
            all_red_flags = []
            strong_count = Decimal("0")
            adequate_count = Decimal("0")
            weak_count = Decimal("0")
            total_weight = Decimal("0")
            
            for item in analyses:
                analysis = item.get("analysis", {})
                quality = (analysis.get("quality") or analysis.get("response_quality", "")).lower()
                red_flags = analysis.get("red_flags", [])
                
                if red_flags:
                    all_red_flags.extend(red_flags)
                
                weight = InterviewReportService._get_question_weight(
                    item.get("question_type", ""),
                    item.get("order_index", 0)
                )
                
                # Skip warmup questions from recommendation calculation
                if item.get("question_type") == "warmup" or item.get("order_index", 0) == 0:
                    continue
                
                total_weight += weight
                
                if quality == "strong":
                    strong_count += weight
                elif quality == "weak":
                    weak_count += weight
                else:
                    adequate_count += weight
            
            # Red flags override everything
            if all_red_flags:
                return "no_hire"
            
            if total_weight == 0:
                return "neutral"
            
            # Calculate percentages
            strong_pct = (strong_count / total_weight) * 100
            weak_pct = (weak_count / total_weight) * 100
            adequate_pct = (adequate_count / total_weight) * 100
            
            # Decision logic
            if strong_pct >= 70:
                return "strong_hire"
            elif strong_pct + adequate_pct >= 70:
                return "hire"
            elif weak_pct >= 50:
                return "maybe"
            elif strong_pct >= 40:
                return "hire"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error("Error deriving comprehensive recommendation", error=str(e), interview_id=str(interview_id))
            return "neutral"
    
    @staticmethod
    async def _aggregate_all_analysis_data(interview_id: UUID) -> Dict[str, Any]:
        """Aggregate all strengths, weaknesses, and red flags from all responses."""
        try:
            analyses = await InterviewReportService._load_all_question_analyses(interview_id)
            
            all_strengths = []
            all_weaknesses = []
            all_red_flags = []
            analysis_history = []
            
            for item in analyses:
                analysis = item.get("analysis", {})
                
                # Collect strengths
                strengths = analysis.get("strengths", [])
                if strengths:
                    all_strengths.extend(strengths)
                
                # Collect weaknesses
                weaknesses = analysis.get("weaknesses", [])
                if weaknesses:
                    all_weaknesses.extend(weaknesses)
                
                # Collect red flags
                red_flags = analysis.get("red_flags", [])
                if red_flags:
                    all_red_flags.extend(red_flags)
                
                # Store analysis history
                if analysis:
                    analysis_history.append({
                        "question_id": item.get("question_id"),
                        "question_type": item.get("question_type"),
                        "order_index": item.get("order_index"),
                        "quality": analysis.get("quality") or analysis.get("response_quality"),
                        "alignment_score": analysis.get("alignment_score") or analysis.get("relevance_score"),
                        "strengths": strengths,
                        "weaknesses": weaknesses,
                        "red_flags": red_flags,
                    })
            
            # Deduplicate and merge
            return {
                "strengths": InterviewReportService._merge_lists(None, all_strengths) or [],
                "weaknesses": InterviewReportService._merge_lists(None, all_weaknesses) or [],
                "red_flags": InterviewReportService._merge_lists(None, all_red_flags) or [],
                "analysis_history": analysis_history,
                "total_questions": len(analyses),
                "questions_with_responses": len([a for a in analyses if a.get("response_text")]),
            }
        except Exception as e:
            logger.error("Error aggregating analysis data", error=str(e), interview_id=str(interview_id))
            return {
                "strengths": [],
                "weaknesses": [],
                "red_flags": [],
                "analysis_history": [],
                "total_questions": 0,
                "questions_with_responses": 0,
            }
    
    @staticmethod
    async def finalize_report(interview_id: UUID) -> Dict[str, Any]:
        """
        Finalize interview report when interview completes.
        
        This method:
        1. Aggregates all responses and analyses
        2. Calculates weighted skill_match_score based on all responses
        3. Generates comprehensive recommendation based on all responses
        4. Aggregates all strengths/weaknesses/red_flags
        5. Updates the report with final scores and recommendation
        
        Args:
            interview_id: Interview ID to finalize
            
        Returns:
            Updated report data
        """
        try:
            logger.info("Finalizing interview report", interview_id=str(interview_id))
            
            # Check if report exists
            report_resp = (
                db.service_client.table("interview_reports")
                .select("*")
                .eq("interview_id", str(interview_id))
                .execute()
            )
            
            if not report_resp.data:
                logger.warning("No report found to finalize, creating new one", interview_id=str(interview_id))
                # Create basic report first if it doesn't exist
                # This shouldn't happen normally, but handle gracefully
                return {}
            
            existing = report_resp.data[0]
            
            # Aggregate all analysis data
            aggregated = await InterviewReportService._aggregate_all_analysis_data(interview_id)
            
            # Calculate weighted skill match score
            weighted_score = await InterviewReportService._calculate_weighted_skill_match_score(interview_id)
            
            # Derive comprehensive recommendation
            comprehensive_rec = await InterviewReportService._derive_comprehensive_recommendation(interview_id)
            
            # Update report
            update_data = InterviewReportUpdate(
                strengths=aggregated["strengths"] or None,
                weaknesses=aggregated["weaknesses"] or None,
                red_flags=aggregated["red_flags"] or None,
                skill_match_score=weighted_score,
                hiring_recommendation=comprehensive_rec,
            )
            
            # Update full_report with analysis history
            existing_full_report = existing.get("full_report", {})
            existing_full_report["analysis_history"] = aggregated["analysis_history"]
            existing_full_report["finalized_at"] = str(datetime.utcnow().isoformat())
            existing_full_report["aggregation_metadata"] = {
                "total_questions": aggregated["total_questions"],
                "questions_with_responses": aggregated["questions_with_responses"],
                "score_calculation_method": "weighted_average",
            }
            update_data.full_report = existing_full_report
            
            # Generate comprehensive recommendation justification
            update_data.recommendation_justification = (
                InterviewReportService._generate_recommendation_justification(
                    comprehensive_rec,
                    weighted_score,
                    aggregated["strengths"],
                    aggregated["weaknesses"],
                    aggregated["red_flags"],
                )
            )
            
            # Ensure experience level is set
            if not existing.get("experience_level"):
                exp_level = await InterviewReportService._determine_experience_level(interview_id)
                if exp_level:
                    update_data.experience_level = exp_level
            
            # Update the report
            resp = (
                db.service_client.table("interview_reports")
                .update(update_data.model_dump(mode="json", exclude_unset=True))
                .eq("interview_id", str(interview_id))
                .execute()
            )
            
            updated_report = (resp.data or [existing])[0]
            
            logger.info(
                "Interview report finalized",
                interview_id=str(interview_id),
                skill_match_score=float(weighted_score) if weighted_score else None,
                hiring_recommendation=comprehensive_rec,
                total_questions=aggregated["total_questions"],
            )
            
            return updated_report
            
        except Exception as e:
            logger.error(
                "Error finalizing interview report",
                error=str(e),
                interview_id=str(interview_id),
                exc_info=True
            )
            # Don't fail interview completion if report finalization fails
            return {}

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


