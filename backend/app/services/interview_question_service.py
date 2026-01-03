"""
Interview Question Service
Enhanced question generation with gap analysis, tiered questions, and multi-source derivation
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from app.database import db
from app.ai.providers_wrapper import LoggedAIProvider
from app.ai.providers import AIProviderFactory
from app.ai.prompts import InterviewPrompts
from app.config import settings
import structlog

logger = structlog.get_logger()


class InterviewQuestionService:
    """Service for generating and managing interview questions with gap analysis"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize question service
        
        Args:
            provider_name: AI provider to use (defaults to primary_ai_provider)
        """
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.provider_name = provider_name or settings.primary_ai_provider
        self.prompts = InterviewPrompts()
    
    async def get_cover_letter_text(self, candidate_id: UUID, job_description_id: UUID) -> Optional[str]:
        """
        Get cover letter text from job application
        
        Args:
            candidate_id: Candidate ID
            job_description_id: Job description ID
        
        Returns:
            Cover letter text or None if not available
        """
        try:
            # Find application by candidate and job
            application_response = (
                db.service_client.table("job_applications")
                .select("cover_letter")
                .eq("candidate_id", str(candidate_id))
                .eq("job_description_id", str(job_description_id))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if application_response.data and application_response.data[0].get("cover_letter"):
                return application_response.data[0]["cover_letter"]
            
            return None
        except Exception as e:
            logger.warning("Failed to fetch cover letter", error=str(e), candidate_id=str(candidate_id), job_id=str(job_description_id))
            return None
    
    async def perform_gap_analysis(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        cover_letter_text: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Perform gap analysis between job requirements and candidate profile
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            cover_letter_text: Optional cover letter text
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Gap analysis dictionary with:
            - required_skills: List of skills from JD
            - candidate_skills: List of skills from CV
            - missing_skills: Skills in JD but not in CV
            - matching_skills: Skills in both
            - cover_letter_insights: Key points from cover letter
        """
        try:
            # Build gap analysis prompt
            cover_letter_section = ""
            if cover_letter_text:
                cover_letter_section = f"""
Cover Letter:
{cover_letter_text[:1500]}
"""
            
            gap_analysis_prompt = f"""Analyze the gap between the job requirements and candidate profile. Extract and compare:

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{cover_letter_section}

Please provide a structured analysis in JSON format:
{{
    "required_skills": ["list of key skills/technologies mentioned in job description"],
    "candidate_skills": ["list of skills/technologies mentioned in CV"],
    "missing_skills": ["skills required in JD but not found in CV"],
    "matching_skills": ["skills that appear in both JD and CV"],
    "experience_gaps": ["experience requirements not clearly demonstrated in CV"],
    "cover_letter_insights": ["key claims, motivations, or points from cover letter"],
    "priority_areas": ["areas that need the most validation in interview"]
}}

Focus on:
- Must-have technical skills
- Required experience levels
- Key responsibilities
- Qualifications and certifications
"""
            
            # Use logged provider if context available
            if recruiter_id or interview_id:
                provider = LoggedAIProvider(self.provider, self.provider_name)
                response = await provider.generate_completion(
                    prompt=gap_analysis_prompt,
                    system_prompt="You are an expert recruiter analyzing job candidate fit. Provide accurate, structured gap analysis in valid JSON format only.",
                    max_tokens=1000,
                    temperature=0.3,
                    recruiter_id=recruiter_id,
                    interview_id=interview_id,
                    job_description_id=job_description_id,
                    candidate_id=candidate_id,
                    feature_name="gap_analysis"
                )
            else:
                response = await self.provider.generate_completion(
                    prompt=gap_analysis_prompt,
                    system_prompt="You are an expert recruiter analyzing job candidate fit. Provide accurate, structured gap analysis in valid JSON format only.",
                    max_tokens=1000,
                    temperature=0.3
                )
            
            # Parse JSON response
            import json
            try:
                # Extract JSON from response (handle markdown code blocks)
                response_clean = response.strip()
                if "```json" in response_clean:
                    response_clean = response_clean.split("```json")[1].split("```")[0].strip()
                elif "```" in response_clean:
                    response_clean = response_clean.split("```")[1].split("```")[0].strip()
                
                gap_analysis = json.loads(response_clean)
                
                logger.info("Gap analysis completed", 
                          interview_id=str(interview_id) if interview_id else None,
                          required_skills_count=len(gap_analysis.get("required_skills", [])),
                          missing_skills_count=len(gap_analysis.get("missing_skills", [])))
                
                return gap_analysis
            except json.JSONDecodeError as e:
                logger.error("Failed to parse gap analysis JSON", error=str(e), response=response[:200])
                # Return fallback analysis
                return {
                    "required_skills": [],
                    "candidate_skills": [],
                    "missing_skills": [],
                    "matching_skills": [],
                    "experience_gaps": [],
                    "cover_letter_insights": [],
                    "priority_areas": []
                }
                
        except Exception as e:
            logger.error("Error performing gap analysis", error=str(e), exc_info=True)
            # Return fallback analysis
            return {
                "required_skills": [],
                "candidate_skills": [],
                "missing_skills": [],
                "matching_skills": [],
                "experience_gaps": [],
                "cover_letter_insights": [],
                "priority_areas": []
            }
    
    async def generate_structured_core_questions(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        cover_letter_text: Optional[str] = None,
        gap_analysis: Optional[Dict[str, Any]] = None,
        num_questions: int = 5,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate structured core questions based on gap analysis
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            cover_letter_text: Optional cover letter text
            gap_analysis: Optional pre-computed gap analysis
            num_questions: Number of core questions to generate (default: 5)
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            List of question dictionaries with priority and category
        """
        try:
            # Perform gap analysis if not provided
            if not gap_analysis:
                gap_analysis = await self.perform_gap_analysis(
                    job_description=job_description,
                    cv_text=cv_text,
                    cover_letter_text=cover_letter_text,
                    recruiter_id=recruiter_id,
                    interview_id=interview_id,
                    job_description_id=job_description_id,
                    candidate_id=candidate_id
                )
            
            # Build comprehensive prompt for structured question generation
            cover_letter_section = ""
            if cover_letter_text:
                cover_letter_section = f"""
Candidate Cover Letter:
{cover_letter_text[:1500]}
"""
            
            gap_summary = f"""
Gap Analysis:
- Required Skills: {', '.join(gap_analysis.get('required_skills', [])[:10])}
- Missing Skills: {', '.join(gap_analysis.get('missing_skills', [])[:5])}
- Matching Skills: {', '.join(gap_analysis.get('matching_skills', [])[:10])}
- Priority Areas: {', '.join(gap_analysis.get('priority_areas', []))}
"""
            
            question_generation_prompt = f"""As an expert HR interviewer, generate {num_questions} structured interview questions for assessing candidate qualification.

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{cover_letter_section}

{gap_summary}

Generate questions that:
1. Question 1 (HIGH PRIORITY): Validate a CRITICAL skill from required_skills that is in matching_skills (verify claimed proficiency)
2. Question 2 (HIGH PRIORITY): Explore experience relevance - how their past experience aligns with job responsibilities
3. Question 3 (HIGH PRIORITY): Probe a missing_skill or experience_gap (assess risk/teachability)
4. Question 4 (MEDIUM PRIORITY): Behavioral/situational question based on job responsibilities
5. Question 5 (MEDIUM PRIORITY): Motivation/fit question (use cover_letter_insights if available)

For each question, provide JSON format:
{{
    "questions": [
        {{
            "question_text": "The actual question text",
            "question_type": "skill_validation|experience|gap_probing|behavioral|motivation",
            "skill_category": "specific skill/area being tested",
            "priority": "high|medium",
            "purpose": "brief explanation of why this question matters"
        }}
    ]
}}

Focus on:
- Validating candidate claims from CV and cover letter
- Assessing qualification against job requirements
- Identifying and addressing gaps
- Ensuring skills alignment
- Understanding motivation and fit

Respond with ONLY valid JSON, no additional commentary."""
            
            # Use logged provider if context available
            if recruiter_id or interview_id:
                provider = LoggedAIProvider(self.provider, self.provider_name)
                response = await provider.generate_completion(
                    prompt=question_generation_prompt,
                    system_prompt="You are an expert HR interviewer. Generate structured, relevant interview questions in valid JSON format only.",
                    max_tokens=1500,
                    temperature=0.7,
                    recruiter_id=recruiter_id,
                    interview_id=interview_id,
                    job_description_id=job_description_id,
                    candidate_id=candidate_id,
                    feature_name="structured_question_generation"
                )
            else:
                response = await self.provider.generate_completion(
                    prompt=question_generation_prompt,
                    system_prompt="You are an expert HR interviewer. Generate structured, relevant interview questions in valid JSON format only.",
                    max_tokens=1500,
                    temperature=0.7
                )
            
            # Parse JSON response
            import json
            try:
                # Extract JSON from response
                response_clean = response.strip()
                if "```json" in response_clean:
                    response_clean = response_clean.split("```json")[1].split("```")[0].strip()
                elif "```" in response_clean:
                    response_clean = response_clean.split("```")[1].split("```")[0].strip()
                
                questions_data = json.loads(response_clean)
                questions = questions_data.get("questions", [])
                
                logger.info("Generated structured core questions", 
                          interview_id=str(interview_id) if interview_id else None,
                          count=len(questions))
                
                return questions
            except json.JSONDecodeError as e:
                logger.error("Failed to parse question JSON", error=str(e), response=response[:200])
                # Return fallback questions
                return self._generate_fallback_questions(job_description, cv_text, num_questions)
                
        except Exception as e:
            logger.error("Error generating structured questions", error=str(e), exc_info=True)
            # Return fallback questions
            return self._generate_fallback_questions(job_description, cv_text, num_questions)
    
    def _generate_fallback_questions(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate fallback questions if AI generation fails"""
        questions = []
        
        # Question 1: Skill validation
        questions.append({
            "question_text": f"Can you tell us about your experience with the key skills required for this {job_description.get('title', 'role')} position?",
            "question_type": "skill_validation",
            "skill_category": "Technical Skills",
            "priority": "high",
            "purpose": "Validate core technical skills"
        })
        
        # Question 2: Experience
        questions.append({
            "question_text": "Can you walk us through one of your most relevant projects and explain your role and contributions?",
            "question_type": "experience",
            "skill_category": None,
            "priority": "high",
            "purpose": "Assess experience relevance"
        })
        
        # Question 3: Behavioral
        questions.append({
            "question_text": "Can you describe a challenging situation you faced in a previous role and how you handled it?",
            "question_type": "behavioral",
            "skill_category": None,
            "priority": "medium",
            "purpose": "Assess problem-solving approach"
        })
        
        # Question 4: Gap probing (if more questions needed)
        if num_questions > 3:
            questions.append({
                "question_text": "Are there any areas mentioned in the job description where you'd like to discuss how your background aligns?",
                "question_type": "gap_probing",
                "skill_category": None,
                "priority": "medium",
                "purpose": "Identify and address gaps"
            })
        
        # Question 5: Motivation
        if num_questions > 4:
            questions.append({
                "question_text": "What interests you most about this role and our organization?",
                "question_type": "motivation",
                "skill_category": None,
                "priority": "medium",
                "purpose": "Assess motivation and fit"
            })
        
        return questions[:num_questions]

