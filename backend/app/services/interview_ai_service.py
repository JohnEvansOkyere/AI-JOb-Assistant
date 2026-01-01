"""
Interview AI Service
Orchestrates AI-powered interview flow
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from app.ai.question_generator import QuestionGenerator
from app.ai.response_analyzer import ResponseAnalyzer
from app.ai.token_tracker import TokenTracker
from app.services.ai_usage_context import get_interview_context
from app.database import db
from app.models.interview_question import InterviewQuestionCreate
from app.models.interview_response import InterviewResponseCreate
import structlog

logger = structlog.get_logger()


class InterviewAIService:
    """Service for AI-powered interview orchestration"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize interview AI service
        
        Args:
            provider_name: AI provider to use
        """
        self.question_generator = QuestionGenerator(provider_name)
        self.response_analyzer = ResponseAnalyzer(provider_name)
        self.token_tracker = TokenTracker()
    
    async def generate_initial_questions(
        self,
        interview_id: UUID,
        job_description: Dict[str, Any],
        cv_text: str,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate initial set of interview questions
        
        Args:
            interview_id: Interview ID
            job_description: Job description data
            cv_text: Candidate CV text
            num_questions: Number of questions to generate
        
        Returns:
            List of question dictionaries
        """
        try:
            # Get context for logging
            context = await get_interview_context(interview_id)
            
            questions = []
            
            # Generate warmup question
            warmup_question = await self.question_generator.generate_warmup_question(
                job_description,
                cv_text,
                recruiter_id=context.get("recruiter_id"),
                interview_id=interview_id,
                job_description_id=context.get("job_description_id"),
                candidate_id=context.get("candidate_id")
            )
            questions.append({
                "question_text": warmup_question,
                "question_type": "warmup",
                "skill_category": None,
                "order_index": 0
            })
            
            # Extract key skills from job description
            key_skills = self._extract_key_skills(job_description)
            
            # Generate skill questions
            for i, skill in enumerate(key_skills[:num_questions - 2], start=1):
                skill_question = await self.question_generator.generate_skill_question(
                    job_description,
                    cv_text,
                    skill,
                    recruiter_id=context.get("recruiter_id"),
                    interview_id=interview_id,
                    job_description_id=context.get("job_description_id"),
                    candidate_id=context.get("candidate_id")
                )
                questions.append({
                    "question_text": skill_question,
                    "question_type": "skill",
                    "skill_category": skill,
                    "order_index": i
                })
            
            # Generate experience question
            experience_question = await self.question_generator.generate_experience_question(
                job_description,
                cv_text,
                recruiter_id=context.get("recruiter_id"),
                interview_id=interview_id,
                job_description_id=context.get("job_description_id"),
                candidate_id=context.get("candidate_id")
            )
            questions.append({
                "question_text": experience_question,
                "question_type": "experience",
                "skill_category": None,
                "order_index": len(questions)
            })
            
            # Store questions in database
            for q in questions:
                question_data = InterviewQuestionCreate(
                    interview_id=interview_id,
                    **q
                )
                # Use JSON mode to ensure UUIDs and datetimes are serializable
                db.service_client.table("interview_questions").insert(
                    question_data.model_dump(mode="json")
                ).execute()
            
            logger.info("Generated initial questions", interview_id=str(interview_id), count=len(questions))
            return questions
            
        except Exception as e:
            logger.error("Error generating initial questions", error=str(e), interview_id=str(interview_id))
            raise
    
    async def process_response(
        self,
        interview_id: UUID,
        question_id: UUID,
        response_text: str,
        job_description: Dict[str, Any],
        cv_text: str,
        response_audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process candidate response and generate analysis
        
        Args:
            interview_id: Interview ID
            question_id: Question ID
            response_text: Candidate's response
            job_description: Job description data
            cv_text: Candidate CV text
            response_audio_path: Optional path to response audio file (for voice mode)
        
        Returns:
            Analysis dictionary
        """
        try:
            # Get the question
            question_response = db.service_client.table("interview_questions").select("*").eq("id", str(question_id)).execute()
            if not question_response.data:
                raise ValueError("Question not found")
            
            question = question_response.data[0]
            
            # Get context for logging
            context = await get_interview_context(interview_id)
            
            # Analyze response
            analysis = await self.response_analyzer.analyze_response(
                question["question_text"],
                response_text,
                job_description,
                cv_text,
                recruiter_id=context.get("recruiter_id"),
                interview_id=interview_id,
                job_description_id=context.get("job_description_id"),
                candidate_id=context.get("candidate_id")
            )
            
            # Store response with audio path if provided
            response_data = InterviewResponseCreate(
                interview_id=interview_id,
                question_id=question_id,
                response_text=response_text,
                response_audio_path=response_audio_path
            )
            db.service_client.table("interview_responses").insert(
                response_data.model_dump(mode="json")
            ).execute()
            
            logger.info("Processed response", interview_id=str(interview_id), question_id=str(question_id), has_audio=bool(response_audio_path))
            return analysis
            
        except Exception as e:
            logger.error("Error processing response", error=str(e))
            raise
    
    async def generate_followup_question(
        self,
        interview_id: UUID,
        job_description: Dict[str, Any],
        cv_text: str,
        previous_question_id: UUID,
        response_quality: str,
        previous_response_text: str = "",
        non_answer_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate follow-up question based on previous response
        
        Args:
            interview_id: Interview ID
            job_description: Job description data
            cv_text: Candidate CV text
            previous_question_id: Previous question ID
            response_quality: Quality of previous response ("strong", "adequate", "weak")
        
        Returns:
            Question dictionary
        """
        try:
            # Get context for logging
            context = await get_interview_context(interview_id)
            
            # Get previous question
            prev_question = db.service_client.table("interview_questions").select("*").eq("id", str(previous_question_id)).execute()
            if not prev_question.data:
                raise ValueError("Previous question not found")
            
            prev_q = prev_question.data[0]
            skill_category = prev_q.get("skill_category")
            previous_question_text = prev_q.get("question_text", "")
            
            # Get the candidate's response to the previous question
            if not previous_response_text:
                response_data = db.service_client.table("interview_responses").select("response_text").eq("question_id", str(previous_question_id)).order("created_at", desc=True).limit(1).execute()
                if response_data.data:
                    previous_response_text = response_data.data[0].get("response_text", "")
            
            # Get all previous questions
            all_questions = db.service_client.table("interview_questions").select("question_text").eq("interview_id", str(interview_id)).execute()
            previous_questions = [q["question_text"] for q in (all_questions.data or [])]
            
            # Generate adaptive question with acknowledgment
            if response_quality == "weak" and skill_category:
                question_text = await self.question_generator.generate_adaptive_question_with_acknowledgment(
                    job_description,
                    cv_text,
                    skill_category,
                    "weak",
                    previous_questions,
                    previous_question_text,
                    previous_response_text,
                    recruiter_id=context.get("recruiter_id"),
                    interview_id=interview_id,
                    job_description_id=context.get("job_description_id"),
                    candidate_id=context.get("candidate_id")
                )
            else:
                # Generate next skill or experience question with acknowledgment
                if skill_category:
                    question_text = await self.question_generator.generate_skill_question_with_acknowledgment(
                        job_description,
                        cv_text,
                        skill_category,
                        previous_questions,
                        previous_question_text,
                        previous_response_text,
                        response_quality,
                        non_answer_type,
                        recruiter_id=context.get("recruiter_id"),
                        interview_id=interview_id,
                        job_description_id=context.get("job_description_id"),
                        candidate_id=context.get("candidate_id")
                    )
                else:
                    question_text = await self.question_generator.generate_experience_question_with_acknowledgment(
                        job_description,
                        cv_text,
                        previous_questions,
                        previous_question_text,
                        previous_response_text,
                        response_quality,
                        non_answer_type,
                        recruiter_id=context.get("recruiter_id"),
                        interview_id=interview_id,
                        job_description_id=context.get("job_description_id"),
                        candidate_id=context.get("candidate_id")
                    )
            
            # Get next order index
            max_order = db.service_client.table("interview_questions").select("order_index").eq("interview_id", str(interview_id)).order("order_index", desc=True).limit(1).execute()
            next_order = (max_order.data[0]["order_index"] + 1) if max_order.data else 0
            
            # Store question
            question_data = InterviewQuestionCreate(
                interview_id=interview_id,
                question_text=question_text,
                question_type="skill" if skill_category else "experience",
                skill_category=skill_category,
                order_index=next_order
            )
            result = db.service_client.table("interview_questions").insert(
                question_data.model_dump(mode="json")
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error("Error generating followup question", error=str(e))
            raise
    
    def _extract_key_skills(self, job_description: Dict[str, Any]) -> List[str]:
        """
        Extract key skills from job description
        
        Args:
            job_description: Job description data
        
        Returns:
            List of key skills
        """
        skills = []
        
        # Extract from requirements
        requirements = job_description.get("requirements", "")
        if requirements:
            # Simple extraction - can be enhanced with NLP
            common_skills = [
                "Python", "JavaScript", "React", "Node.js", "SQL", "PostgreSQL",
                "FastAPI", "Django", "Flask", "AWS", "Docker", "Kubernetes",
                "Machine Learning", "Data Analysis", "Project Management",
                "Communication", "Leadership", "Problem Solving"
            ]
            
            requirements_lower = requirements.lower()
            for skill in common_skills:
                if skill.lower() in requirements_lower:
                    skills.append(skill)
        
        # If no skills found, use generic categories
        if not skills:
            skills = ["Technical Skills", "Problem Solving", "Communication"]
        
        return skills[:5]  # Limit to 5 skills

