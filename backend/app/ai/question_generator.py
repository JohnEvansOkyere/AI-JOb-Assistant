"""
Question Generator
Generates interview questions based on job description and CV
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from app.ai.providers import AIProviderFactory
from app.ai.providers_wrapper import LoggedAIProvider
from app.ai.prompts import InterviewPrompts
from app.config import settings
import structlog

logger = structlog.get_logger()


class QuestionGenerator:
    """Service for generating interview questions"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize question generator
        
        Args:
            provider_name: AI provider to use (defaults to primary_ai_provider)
        """
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.provider_name = provider_name or settings.primary_ai_provider
        self.prompts = InterviewPrompts()
    
    def _get_provider_for_call(
        self,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        feature_name: str = "question_generation"
    ):
        """Get provider (logged or regular) based on context"""
        if recruiter_id or interview_id:
            # Use logged provider with context
            return LoggedAIProvider(self.provider, self.provider_name), {
                "recruiter_id": recruiter_id,
                "interview_id": interview_id,
                "job_description_id": job_description_id,
                "candidate_id": candidate_id,
                "feature_name": feature_name
            }
        else:
            # Use regular provider (backwards compatible)
            return self.provider, {}
    
    async def generate_warmup_question(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate warmup question
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text
        """
        try:
            prompt = self.prompts.get_warmup_prompt(job_description, cv_text)
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=200,
                    temperature=0.8,
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=200,
                    temperature=0.8
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating warmup question", error=str(e))
            # Fallback question
            return "Thank you for taking the time to interview with us today. Can you start by telling us what interests you most about this role?"
    
    async def generate_skill_question(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_questions: Optional[List[str]] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate skill assessment question
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            skill_category: Skill/requirement to test
            previous_questions: List of previously asked questions
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text
        """
        try:
            prompt = self.prompts.get_skill_question_prompt(
                job_description,
                cv_text,
                skill_category,
                previous_questions or []
            )
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.7,
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.7
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating skill question", error=str(e), skill=skill_category)
            # Fallback question
            return f"Can you tell us about your experience with {skill_category}?"
    
    async def generate_experience_question(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        previous_questions: Optional[List[str]] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate experience validation question
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            previous_questions: List of previously asked questions
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text
        """
        try:
            prompt = self.prompts.get_experience_question_prompt(
                job_description,
                cv_text,
                previous_questions or []
            )
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.7,
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.7
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating experience question", error=str(e))
            # Fallback question
            return "Can you walk us through one of your most relevant projects and explain your role and contributions?"
    
    async def generate_soft_skill_question(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        skill_type: str = "problem-solving"
    ) -> str:
        """
        Generate soft skill question
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            skill_type: Type of soft skill to test
        
        Returns:
            Generated question text
        """
        try:
            prompt = self.prompts.get_soft_skill_question_prompt(
                job_description,
                cv_text,
                skill_type
            )
            question = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt=self.prompts.SYSTEM_PROMPT,
                max_tokens=300,
                temperature=0.7
            )
            return question.strip()
        except Exception as e:
            logger.error("Error generating soft skill question", error=str(e))
            # Fallback question
            return f"Can you describe a situation where you had to demonstrate {skill_type}? What was the outcome?"
    
    async def generate_wrapup_question(self) -> str:
        """
        Generate wrap-up question
        
        Returns:
            Generated question text
        """
        try:
            prompt = self.prompts.get_wrapup_prompt()
            question = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt=self.prompts.SYSTEM_PROMPT,
                max_tokens=150,
                temperature=0.8
            )
            return question.strip()
        except Exception as e:
            logger.error("Error generating wrapup question", error=str(e))
            # Fallback question
            return "Do you have any questions for us about the role or the company?"
    
    async def generate_adaptive_question(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_response_quality: str,  # "strong", "adequate", "weak"
        previous_questions: Optional[List[str]] = None
    ) -> str:
        """
        Generate adaptive question based on previous response quality
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            skill_category: Skill category
            previous_response_quality: Quality of previous response
            previous_questions: List of previously asked questions
        
        Returns:
            Generated question text
        """
        try:
            if previous_response_quality == "strong":
                # Ask deeper question
                return await self.generate_skill_question(
                    job_description,
                    cv_text,
                    skill_category,
                    previous_questions
                )
            elif previous_response_quality == "weak":
                # Ask simpler question
                prompt = self.prompts.get_adaptive_difficulty_prompt("weak", skill_category)
                question = await self.provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=250,
                    temperature=0.7
                )
                return question.strip()
            else:
                # Continue at same level
                return await self.generate_skill_question(
                    job_description,
                    cv_text,
                    skill_category,
                    previous_questions
                )
        except Exception as e:
            logger.error("Error generating adaptive question", error=str(e))
            return await self.generate_skill_question(job_description, cv_text, skill_category, previous_questions)
    
    async def generate_skill_question_with_acknowledgment(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_questions: Optional[List[str]],
        previous_question_text: str,
        previous_response_text: str,
        response_quality: str,
        non_answer_type: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate skill question that acknowledges the candidate's previous response
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            skill_category: Skill category
            previous_questions: List of previously asked questions
            previous_question_text: The previous question that was asked
            previous_response_text: The candidate's response to the previous question
            response_quality: Quality of previous response
            non_answer_type: Type of non-answer if detected ("not_ready", "confused", "decline", "need_help")
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text with acknowledgment
        """
        try:
            prompt = self.prompts.get_skill_question_with_acknowledgment_prompt(
                job_description,
                cv_text,
                skill_category,
                previous_questions or [],
                previous_question_text,
                previous_response_text,
                response_quality,
                non_answer_type
            )
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8,  # Higher temperature for more natural conversation
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8  # Higher temperature for more natural conversation
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating skill question with acknowledgment", error=str(e))
            # Fallback: simple acknowledgment + question
            return f"Thank you for that. Can you tell us more about your experience with {skill_category}?"

    async def generate_experience_question_with_acknowledgment(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        previous_questions: Optional[List[str]],
        previous_question_text: str,
        previous_response_text: str,
        response_quality: str,
        non_answer_type: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate experience question that acknowledges the candidate's previous response
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            previous_questions: List of previously asked questions
            previous_question_text: The previous question that was asked
            previous_response_text: The candidate's response to the previous question
            response_quality: Quality of previous response
            non_answer_type: Type of non-answer if detected ("not_ready", "confused", "decline", "need_help")
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text with acknowledgment
        """
        try:
            prompt = self.prompts.get_experience_question_with_acknowledgment_prompt(
                job_description,
                cv_text,
                previous_questions or [],
                previous_question_text,
                previous_response_text,
                response_quality,
                non_answer_type
            )
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8,
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating experience question with acknowledgment", error=str(e))
            # Fallback
            return "That's helpful context. Can you walk us through one of your most relevant projects and explain your role and contributions?"

    async def generate_adaptive_question_with_acknowledgment(
        self,
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_response_quality: str,
        previous_questions: Optional[List[str]],
        previous_question_text: str,
        previous_response_text: str,
        recruiter_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None
    ) -> str:
        """
        Generate adaptive question that acknowledges the candidate's previous response
        
        Args:
            job_description: Job description data
            cv_text: Candidate CV text
            skill_category: Skill category
            previous_response_quality: Quality of previous response
            previous_questions: List of previously asked questions
            previous_question_text: The previous question that was asked
            previous_response_text: The candidate's response to the previous question
            recruiter_id: Optional recruiter ID for logging
            interview_id: Optional interview ID for logging
            job_description_id: Optional job description ID for logging
            candidate_id: Optional candidate ID for logging
        
        Returns:
            Generated question text with acknowledgment
        """
        try:
            prompt = self.prompts.get_adaptive_question_with_acknowledgment_prompt(
                job_description,
                cv_text,
                skill_category,
                previous_response_quality,
                previous_questions or [],
                previous_question_text,
                previous_response_text
            )
            provider, context = self._get_provider_for_call(
                recruiter_id=recruiter_id,
                interview_id=interview_id,
                job_description_id=job_description_id,
                candidate_id=candidate_id,
                feature_name="question_generation"
            )
            
            if isinstance(provider, LoggedAIProvider):
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8,
                    **context
                )
            else:
                question = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.SYSTEM_PROMPT,
                    max_tokens=300,
                    temperature=0.8
                )
            return question.strip()
        except Exception as e:
            logger.error("Error generating adaptive question with acknowledgment", error=str(e))
            # Fallback
            return f"I appreciate your response. Let me ask you a bit more about {skill_category} - can you share a specific example?"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return self.provider.get_token_count(text)

