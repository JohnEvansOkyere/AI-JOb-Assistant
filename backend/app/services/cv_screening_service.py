"""
CV Screening Service
AI-powered CV screening and matching against job descriptions
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.ai.providers import AIProviderFactory
from app.ai.providers_wrapper import LoggedAIProvider
from app.ai.prompts import InterviewPrompts
from app.database import db
from app.models.cv_screening import CVScreeningResult, CVScreeningResultCreate
from app.config import settings
import structlog
import json

logger = structlog.get_logger()


class CVScreeningService:
    """Service for screening CVs against job descriptions"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """Initialize screening service"""
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.provider_name = provider_name or settings.primary_ai_provider
        self.prompts = InterviewPrompts()
    
    def _get_provider_for_call(
        self,
        recruiter_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        feature_name: str = "cv_screening"
    ):
        """Get provider (logged or regular) based on context"""
        if recruiter_id or job_description_id:
            # Use logged provider with context
            return LoggedAIProvider(self.provider, self.provider_name), {
                "recruiter_id": recruiter_id,
                "interview_id": None,
                "job_description_id": job_description_id,
                "candidate_id": candidate_id,
                "feature_name": feature_name
            }
        else:
            # Use regular provider (backwards compatible)
            return self.provider, {}
    
    async def screen_cv(
        self,
        cv_text: str,
        job_description: Dict[str, Any],
        cv_structured: Optional[Dict[str, Any]] = None,
        recruiter_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Screen a CV against a job description
        
        Args:
            cv_text: CV text content
            job_description: Job description data
            cv_structured: Optional structured CV data
            recruiter_id: Optional recruiter ID for cost tracking
            job_description_id: Optional job description ID for cost tracking
            candidate_id: Optional candidate ID for cost tracking
        
        Returns:
            Screening result dictionary
        """
        try:
            # Generate screening prompt
            prompt = self._generate_screening_prompt(cv_text, job_description)
            
            # Get provider with cost tracking if context available
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="cv_screening"
            )
            
            # Get AI analysis
            if isinstance(provider, LoggedAIProvider):
                analysis_text = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=1000,
                    temperature=0.5,
                    **context
                )
            else:
                analysis_text = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=1000,
                    temperature=0.5
                )
            
            # Parse and structure results
            result = self._parse_screening_result(analysis_text, cv_text, job_description)
            
            logger.info("CV screened", match_score=float(result["match_score"]))
            return result
            
        except Exception as e:
            logger.error("Error screening CV", error=str(e))
            # Return default result on error
            return {
                "match_score": Decimal("50.0"),
                "skill_match_score": Decimal("50.0"),
                "experience_match_score": Decimal("50.0"),
                "qualification_match_score": Decimal("50.0"),
                "strengths": [],
                "gaps": ["Unable to complete screening"],
                "recommendation": "maybe_qualified",
                "screening_notes": f"Screening error: {str(e)}",
                "screening_details": {}
            }
    
    def _generate_screening_prompt(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> str:
        """Generate screening analysis prompt"""
        return f"""Analyze this candidate's CV against the job description and provide a detailed screening assessment.

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}
Experience Level: {job_description.get('experience_level', 'N/A')}

Candidate CV:
{cv_text[:3000]}

Provide a structured analysis in the following format:

MATCH_SCORE: [0-100] (overall match percentage)
SKILL_MATCH: [0-100] (skill alignment)
EXPERIENCE_MATCH: [0-100] (experience alignment)
QUALIFICATION_MATCH: [0-100] (qualification alignment)

STRENGTHS:
- [List matched strengths, one per line]

GAPS:
- [List missing skills/experience, one per line]

RECOMMENDATION: [qualified / maybe_qualified / not_qualified]

NOTES:
[Brief summary of the screening assessment]

Focus on:
- Technical skills match
- Experience level match
- Qualification requirements
- Overall fit for the role
- Be objective and fair
- Only consider job-relevant criteria"""
    
    def _parse_screening_result(
        self,
        analysis_text: str,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI screening analysis into structured format"""
        result = {
            "match_score": Decimal("50.0"),
            "skill_match_score": Decimal("50.0"),
            "experience_match_score": Decimal("50.0"),
            "qualification_match_score": Decimal("50.0"),
            "strengths": [],
            "gaps": [],
            "recommendation": "maybe_qualified",
            "screening_notes": "",
            "screening_details": {}
        }
        
        try:
            lines = analysis_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse scores
                if 'MATCH_SCORE:' in line.upper():
                    score = self._extract_number(line)
                    if score:
                        result["match_score"] = Decimal(str(score))
                elif 'SKILL_MATCH:' in line.upper():
                    score = self._extract_number(line)
                    if score:
                        result["skill_match_score"] = Decimal(str(score))
                elif 'EXPERIENCE_MATCH:' in line.upper():
                    score = self._extract_number(line)
                    if score:
                        result["experience_match_score"] = Decimal(str(score))
                elif 'QUALIFICATION_MATCH:' in line.upper():
                    score = self._extract_number(line)
                    if score:
                        result["qualification_match_score"] = Decimal(str(score))
                
                # Parse sections
                elif line.upper().startswith('STRENGTHS:'):
                    current_section = 'strengths'
                elif line.upper().startswith('GAPS:'):
                    current_section = 'gaps'
                elif line.upper().startswith('RECOMMENDATION:'):
                    rec = line.split(':', 1)[1].strip().lower()
                    if 'qualified' in rec and 'not' not in rec:
                        result["recommendation"] = "qualified"
                    elif 'not_qualified' in rec or 'not qualified' in rec:
                        result["recommendation"] = "not_qualified"
                    else:
                        result["recommendation"] = "maybe_qualified"
                elif line.upper().startswith('NOTES:'):
                    current_section = 'notes'
                    result["screening_notes"] = line.split(':', 1)[1].strip() if ':' in line else ""
                elif current_section == 'strengths' and line.startswith('-'):
                    result["strengths"].append(line[1:].strip())
                elif current_section == 'gaps' and line.startswith('-'):
                    result["gaps"].append(line[1:].strip())
                elif current_section == 'notes':
                    result["screening_notes"] += " " + line
            
            # Store full analysis in details
            result["screening_details"] = {
                "raw_analysis": analysis_text,
                "cv_length": len(cv_text),
                "job_title": job_description.get('title')
            }
            
        except Exception as e:
            logger.error("Error parsing screening result", error=str(e))
            result["screening_notes"] = f"Parsing error: {str(e)}"
        
        return result
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        return None
    
    def _convert_decimal_to_float(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        result = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, dict):
                result[key] = self._convert_decimal_to_float(value)
            elif isinstance(value, list):
                result[key] = [
                    self._convert_decimal_to_float(item) if isinstance(item, dict) else (float(item) if isinstance(item, Decimal) else item)
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    async def screen_application(
        self,
        application_id: UUID,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Screen an application and store results
        
        Args:
            application_id: Application ID
            cv_text: CV text content
            job_description: Job description data
        
        Returns:
            Screening result
        """
        try:
            # Get context for cost tracking
            from app.services.ai_usage_context import get_application_context
            context = await get_application_context(application_id)
            
            # Check if screening result already exists
            existing = db.service_client.table("cv_screening_results").select("*").eq("application_id", str(application_id)).execute()
            
            # Perform screening with context for cost tracking
            screening_result = await self.screen_cv(
                cv_text,
                job_description,
                recruiter_id=context.get("recruiter_id"),
                job_description_id=context.get("job_description_id"),
                candidate_id=context.get("candidate_id")
            )
            
            # Convert Decimal to float for JSON serialization
            screening_result_serializable = self._convert_decimal_to_float(screening_result)
            
            if existing.data:
                logger.info("Screening result already exists, updating", application_id=str(application_id))
                # Update existing result (remove application_id from update data)
                update_data = {k: v for k, v in screening_result_serializable.items() if k != "application_id"}
                response = db.service_client.table("cv_screening_results").update(
                    update_data
                ).eq("application_id", str(application_id)).execute()
            else:
                # Store new result in database
                # Use serializable version (already converted to float)
                # Pass directly to Supabase to avoid Pydantic converting back to Decimal
                # Explicitly generate UUID for id column (Supabase client doesn't trigger DEFAULT)
                from uuid import uuid4
                insert_data = {
                    "id": str(uuid4()),
                    "application_id": str(application_id),
                    **screening_result_serializable
                }
                
                response = db.service_client.table("cv_screening_results").insert(
                    insert_data
                ).execute()
            
            # Update application status based on recommendation
            recommendation = screening_result.get("recommendation", "maybe_qualified")
            if recommendation == "qualified":
                new_status = "qualified"
            elif recommendation == "not_qualified":
                new_status = "rejected"
            else:
                new_status = "screening"  # maybe_qualified stays in screening for manual review
            
            db.service_client.table("job_applications").update({
                "status": new_status,
                "screened_at": datetime.utcnow().isoformat()
            }).eq("id", str(application_id)).execute()
            
            logger.info("Application screened", application_id=str(application_id), match_score=float(screening_result["match_score"]))
            
            # Return serializable version
            # Ensure response data is also serializable (in case Supabase returns Decimal)
            if response.data and response.data[0]:
                return self._convert_decimal_to_float(response.data[0])
            return screening_result_serializable
            
        except Exception as e:
            logger.error("Error screening application", error=str(e), application_id=str(application_id), exc_info=True)
            raise
    
    async def batch_screen_applications(
        self,
        job_description_id: UUID,
        application_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Screen multiple applications for a job
        
        Args:
            job_description_id: Job description ID
            application_ids: List of application IDs to screen
        
        Returns:
            List of screening results
        """
        try:
            # Get job description
            job = db.service_client.table("job_descriptions").select("*").eq("id", str(job_description_id)).execute()
            if not job.data:
                raise ValueError("Job description not found")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
            
            job_description = job.data[0]
            results = []
            
            # Get applications with CVs
            applications = db.service_client.table("job_applications").select("*, cvs(*)").in_("id", [str(aid) for aid in application_ids]).execute()
            
            for app in applications.data or []:
                cv_id = app.get("cv_id")
                if not cv_id:
                    continue
                
                # Get CV text
                cv = db.service_client.table("cvs").select("parsed_text").eq("id", str(cv_id)).execute()
                if not cv.data or not cv.data[0].get("parsed_text"):
                    continue
                
                cv_text = cv.data[0]["parsed_text"]
                
                # Screen
                result = await self.screen_application(
                    UUID(app["id"]),
                    cv_text,
                    job_description
                )
                results.append(result)
            
            logger.info("Batch screening completed", job_id=str(job_description_id), count=len(results))
            return results
            
        except Exception as e:
            logger.error("Error in batch screening", error=str(e))
            raise

