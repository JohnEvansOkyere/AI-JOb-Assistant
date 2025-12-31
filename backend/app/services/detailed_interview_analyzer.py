"""
Detailed Interview Analyzer Service
Comprehensive AI-powered analysis of interview performance
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal

from app.ai.providers import AIProviderFactory
from app.ai.providers_wrapper import LoggedAIProvider
from app.ai.interview_analysis_prompts import InterviewAnalysisPrompts
from app.models.detailed_interview_analysis import (
    DetailedInterviewAnalysisCreate,
    DetailedInterviewAnalysisUpdate,
)
from app.database import db
from app.services.ai_usage_context import get_interview_context
from app.config import settings
import structlog

logger = structlog.get_logger()


class DetailedInterviewAnalyzer:
    """Service for comprehensive interview analysis"""

    def __init__(self, provider_name: Optional[str] = None):
        """Initialize the analyzer with AI provider"""
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.provider_name = provider_name or settings.primary_ai_provider
        self.prompts = InterviewAnalysisPrompts()

    async def analyze_interview(self, interview_id: UUID) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a completed interview.
        
        Args:
            interview_id: ID of the interview to analyze
        
        Returns:
            Complete analysis results
        """
        logger.info("Starting detailed interview analysis", interview_id=str(interview_id))

        try:
            # Load interview data
            interview_data = await self._load_interview_data(interview_id)
            if not interview_data:
                raise ValueError(f"Interview {interview_id} not found")

            # Load job description
            job_description = await self._load_job_description(
                interview_data["job_description_id"]
            )

            # Load candidate CV
            cv_text = await self._load_cv_text(interview_data["candidate_id"])

            # Load questions and responses
            qa_pairs = await self._load_questions_and_responses(interview_id)
            
            if not qa_pairs:
                logger.warning("No Q&A pairs found for interview", interview_id=str(interview_id))
                return {"error": "No interview responses found"}

            # Run comprehensive analysis with cost tracking
            analysis = await self._run_comprehensive_analysis(
                interview_data, job_description, cv_text, qa_pairs, interview_id
            )

            # Calculate aggregate scores
            analysis = self._calculate_aggregate_scores(analysis)

            # Store analysis in database
            stored_analysis = await self._store_analysis(interview_id, analysis)

            logger.info(
                "Detailed interview analysis completed",
                interview_id=str(interview_id),
                overall_score=analysis.get("overall_assessment", {}).get("overall_score", 0),
            )

            return stored_analysis

        except Exception as e:
            logger.error(
                "Error in detailed interview analysis",
                interview_id=str(interview_id),
                error=str(e),
            )
            raise

    async def _load_interview_data(self, interview_id: UUID) -> Optional[Dict[str, Any]]:
        """Load interview metadata"""
        result = (
            db.service_client.table("interviews")
            .select("*")
            .eq("id", str(interview_id))
            .execute()
        )
        return result.data[0] if result.data else None

    async def _load_job_description(self, job_id: str) -> Dict[str, Any]:
        """Load job description details"""
        result = (
            db.service_client.table("job_descriptions")
            .select("*")
            .eq("id", str(job_id))
            .execute()
        )
        return result.data[0] if result.data else {}

    async def _load_cv_text(self, candidate_id: str) -> str:
        """Load candidate's CV text"""
        result = (
            db.service_client.table("cvs")
            .select("parsed_text, parsed_json")
            .eq("candidate_id", str(candidate_id))
            .order("uploaded_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if result.data:
            cv = result.data[0]
            if cv.get("parsed_text"):
                return cv["parsed_text"]
            if cv.get("parsed_json"):
                return json.dumps(cv["parsed_json"])
        return "No CV available"

    async def _load_questions_and_responses(
        self, interview_id: UUID
    ) -> List[Dict[str, str]]:
        """Load all questions and responses for the interview"""
        # Load questions
        questions_result = (
            db.service_client.table("interview_questions")
            .select("id, question_text, question_type, order_index")
            .eq("interview_id", str(interview_id))
            .order("order_index")
            .execute()
        )
        
        questions = {q["id"]: q for q in (questions_result.data or [])}
        
        # Load responses
        responses_result = (
            db.service_client.table("interview_responses")
            .select("question_id, response_text")
            .eq("interview_id", str(interview_id))
            .execute()
        )
        
        responses = {r["question_id"]: r for r in (responses_result.data or [])}
        
        # Combine Q&A pairs
        qa_pairs = []
        for q_id, question in questions.items():
            response = responses.get(q_id, {})
            qa_pairs.append({
                "question_id": q_id,
                "question": question.get("question_text", ""),
                "question_type": question.get("question_type", ""),
                "response": response.get("response_text", "No response"),
            })
        
        return qa_pairs

    async def _run_comprehensive_analysis(
        self,
        interview_data: Dict[str, Any],
        job_description: Dict[str, Any],
        cv_text: str,
        qa_pairs: List[Dict[str, str]],
        interview_id: UUID,
    ) -> Dict[str, Any]:
        """Run the main comprehensive analysis using AI"""
        
        # Get context for cost tracking
        context = await get_interview_context(interview_id)
        
        # Format Q&A for prompt
        formatted_qa = [
            {"question": qa["question"], "response": qa["response"]}
            for qa in qa_pairs
        ]
        
        prompt = self.prompts.get_comprehensive_analysis_prompt(
            interview_data, job_description, cv_text, formatted_qa
        )

        # Get provider with cost tracking if context available
        if context.get("recruiter_id") or context.get("interview_id"):
            provider = LoggedAIProvider(self.provider, self.provider_name)
            provider_context = {
                "recruiter_id": context.get("recruiter_id"),
                "interview_id": interview_id,
                "job_description_id": context.get("job_description_id"),
                "candidate_id": context.get("candidate_id"),
                "feature_name": "detailed_interview_analysis"
            }
        else:
            provider = self.provider
            provider_context = {}

        # Try with current provider, fallback to others if API errors occur
        last_error = None
        providers_tried = []
        
        try:
            if isinstance(provider, LoggedAIProvider):
                analysis_text = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.COMPREHENSIVE_ANALYSIS_SYSTEM_PROMPT,
                    max_tokens=4000,
                    temperature=0.4,
                    **provider_context
                )
            else:
                analysis_text = await provider.generate_completion(
                    prompt=prompt,
                    system_prompt=self.prompts.COMPREHENSIVE_ANALYSIS_SYSTEM_PROMPT,
                    max_tokens=4000,
                    temperature=0.4,
                )

            # Parse JSON from response
            analysis = self._parse_json_response(analysis_text)
            
            # Add metadata
            analysis["metadata"] = {
                "total_questions": len(qa_pairs),
                "total_responses": sum(1 for qa in qa_pairs if qa["response"] != "No response"),
                "average_response_length": self._calculate_avg_response_length(qa_pairs),
            }
            
            return analysis

        except Exception as e:
            last_error = e
            error_str = str(e)
            
            # Check if it's an API error that might be provider-specific (400, 401, 403, 429, model errors, etc.)
            is_api_error = any(indicator in error_str for indicator in [
                "400", "401", "403", "429", 
                "Invalid API", "invalid_api_key", "Invalid API Key",
                "model_decommissioned", "model not found", "model_not_found",
                "decommissioned", "not supported", "not found for API"
            ])
            
            if is_api_error:
                logger.warning(
                    "Provider API error detected, trying fallback providers",
                    error=error_str,
                    current_provider=getattr(self.provider, '__class__', {}).__name__ if self.provider else "unknown"
                )
                
                # Get available providers and try in priority order: openai -> grok -> groq -> gemini
                available_providers = AIProviderFactory.get_available_providers()
                priority_order = ["openai", "grok", "groq", "gemini"]
                # Reorder available providers according to priority
                ordered_providers = [p for p in priority_order if p in available_providers]
                
                current_provider_name = None
                
                # Determine current provider name
                provider_class_name = self.provider.__class__.__name__ if self.provider else ""
                if "OpenAI" in provider_class_name:
                    current_provider_name = "openai"
                elif "Grok" in provider_class_name:
                    current_provider_name = "grok"
                elif "Groq" in provider_class_name:
                    current_provider_name = "groq"
                elif "Gemini" in provider_class_name:
                    current_provider_name = "gemini"
                
                # Try other available providers in priority order
                for provider_name in ordered_providers:
                    if provider_name != current_provider_name:
                        try:
                            logger.info(f"Trying fallback provider: {provider_name}")
                            fallback_provider_base = AIProviderFactory.create_provider(provider_name)
                            # Use logged provider for fallback too if context available
                            if isinstance(provider, LoggedAIProvider):
                                fallback_provider = LoggedAIProvider(fallback_provider_base, provider_name)
                            else:
                                fallback_provider = fallback_provider_base
                            self.provider = fallback_provider_base  # Store base for next iteration
                            providers_tried.append(provider_name)
                            
                            if isinstance(fallback_provider, LoggedAIProvider):
                                analysis_text = await fallback_provider.generate_completion(
                                    prompt=prompt,
                                    system_prompt=self.prompts.COMPREHENSIVE_ANALYSIS_SYSTEM_PROMPT,
                                    max_tokens=4000,
                                    temperature=0.4,
                                    **provider_context
                                )
                            else:
                                analysis_text = await fallback_provider.generate_completion(
                                    prompt=prompt,
                                    system_prompt=self.prompts.COMPREHENSIVE_ANALYSIS_SYSTEM_PROMPT,
                                    max_tokens=4000,
                                    temperature=0.4,
                                )
                            
                            # Success with fallback provider
                            logger.info(f"Successfully used fallback provider: {provider_name}")
                            analysis = self._parse_json_response(analysis_text)
                            analysis["metadata"] = {
                                "total_questions": len(qa_pairs),
                                "total_responses": sum(1 for qa in qa_pairs if qa["response"] != "No response"),
                                "average_response_length": self._calculate_avg_response_length(qa_pairs),
                            }
                            return analysis
                            
                        except Exception as fallback_error:
                            logger.warning(
                                f"Fallback provider {provider_name} also failed",
                                error=str(fallback_error)
                            )
                            last_error = fallback_error
                            continue
            
            # All providers failed or it's not an API error - return fallback
            logger.error(
                "AI analysis failed with all providers",
                error=str(last_error),
                providers_tried=providers_tried
            )
            return self._get_fallback_analysis(qa_pairs)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling markdown code blocks"""
        try:
            # Try to extract JSON from markdown code block
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON response", error=str(e))
            # Try to fix common JSON issues
            try:
                # Remove trailing commas
                fixed = re.sub(r",\s*([}\]])", r"\1", json_str)
                return json.loads(fixed)
            except:
                return {}

    def _calculate_avg_response_length(self, qa_pairs: List[Dict[str, str]]) -> int:
        """Calculate average response length in words"""
        total_words = sum(
            len(qa["response"].split()) 
            for qa in qa_pairs 
            if qa["response"] != "No response"
        )
        count = sum(1 for qa in qa_pairs if qa["response"] != "No response")
        return total_words // count if count > 0 else 0

    def _calculate_aggregate_scores(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate scores from detailed analysis"""
        
        # Soft skills aggregate
        soft_skills = analysis.get("soft_skills", {})
        soft_skill_scores = [
            soft_skills.get(skill, {}).get("score", 0)
            for skill in [
                "leadership", "teamwork", "problem_solving", "adaptability",
                "creativity", "emotional_intelligence", "time_management", "conflict_resolution"
            ]
        ]
        if soft_skill_scores:
            analysis.setdefault("overall_assessment", {})["soft_skills_score"] = (
                sum(soft_skill_scores) / len(soft_skill_scores)
            )

        # Communication aggregate
        communication = analysis.get("communication", {})
        comm_scores = [
            communication.get(skill, {}).get("score", 0)
            for skill in ["clarity", "articulation", "confidence", "listening", "persuasion"]
        ]
        if comm_scores:
            analysis.setdefault("overall_assessment", {})["communication_score"] = (
                sum(comm_scores) / len(comm_scores)
            )

        # Technical aggregate
        technical = analysis.get("technical_assessment", {})
        tech_scores = [
            technical.get(skill, {}).get("score", 0)
            for skill in ["depth", "breadth", "practical_application", "industry_knowledge"]
        ]
        if tech_scores:
            analysis.setdefault("overall_assessment", {})["technical_score"] = (
                sum(tech_scores) / len(tech_scores)
            )

        return analysis

    def _get_fallback_analysis(self, qa_pairs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a basic fallback analysis when AI fails"""
        return {
            "overall_assessment": {
                "overall_score": 50,
                "technical_score": 50,
                "soft_skills_score": 50,
                "communication_score": 50,
                "summary": "Analysis could not be completed automatically. Manual review required.",
            },
            "soft_skills": {},
            "communication": {},
            "technical_assessment": {},
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "sentiment_score": 50,
                "enthusiasm_level": "moderate",
            },
            "behavioral_analysis": {},
            "question_by_question": [],
            "culture_fit": {"score": 50, "notes": "Requires manual assessment"},
            "role_fit": {"score": 50, "analysis": "Requires manual assessment"},
            "summary": {
                "key_strengths": [],
                "areas_for_improvement": [],
                "notable_quotes": [],
                "follow_up_topics": [],
            },
            "recommendation": {
                "decision": "under_review",
                "confidence": 0,
                "summary": "Automatic analysis failed. Manual review required.",
                "detailed": "",
            },
            "metadata": {
                "total_questions": len(qa_pairs),
                "total_responses": sum(1 for qa in qa_pairs if qa["response"] != "No response"),
                "average_response_length": self._calculate_avg_response_length(qa_pairs),
            },
        }

    async def _store_analysis(
        self, interview_id: UUID, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store the analysis in the database"""
        
        overall = analysis.get("overall_assessment", {})
        soft_skills = analysis.get("soft_skills", {})
        communication = analysis.get("communication", {})
        technical = analysis.get("technical_assessment", {})
        sentiment = analysis.get("sentiment_analysis", {})
        behavioral = analysis.get("behavioral_analysis", {})
        summary = analysis.get("summary", {})
        culture_fit = analysis.get("culture_fit", {})
        role_fit = analysis.get("role_fit", {})
        recommendation = analysis.get("recommendation", {})
        metadata = analysis.get("metadata", {})

        # Prepare data for storage
        data = {
            "interview_id": str(interview_id),
            
            # Overall scores
            "overall_score": self._safe_decimal(overall.get("overall_score", 0)),
            "technical_score": self._safe_decimal(overall.get("technical_score", 0)),
            "soft_skills_score": self._safe_decimal(overall.get("soft_skills_score", 0)),
            "communication_score": self._safe_decimal(overall.get("communication_score", 0)),
            
            # Soft skills scores
            "leadership_score": self._safe_decimal(soft_skills.get("leadership", {}).get("score", 0)),
            "teamwork_score": self._safe_decimal(soft_skills.get("teamwork", {}).get("score", 0)),
            "problem_solving_score": self._safe_decimal(soft_skills.get("problem_solving", {}).get("score", 0)),
            "adaptability_score": self._safe_decimal(soft_skills.get("adaptability", {}).get("score", 0)),
            "creativity_score": self._safe_decimal(soft_skills.get("creativity", {}).get("score", 0)),
            "emotional_intelligence_score": self._safe_decimal(soft_skills.get("emotional_intelligence", {}).get("score", 0)),
            "time_management_score": self._safe_decimal(soft_skills.get("time_management", {}).get("score", 0)),
            "conflict_resolution_score": self._safe_decimal(soft_skills.get("conflict_resolution", {}).get("score", 0)),
            
            # Communication scores
            "clarity_score": self._safe_decimal(communication.get("clarity", {}).get("score", 0)),
            "articulation_score": self._safe_decimal(communication.get("articulation", {}).get("score", 0)),
            "confidence_score": self._safe_decimal(communication.get("confidence", {}).get("score", 0)),
            "listening_score": self._safe_decimal(communication.get("listening", {}).get("score", 0)),
            "persuasion_score": self._safe_decimal(communication.get("persuasion", {}).get("score", 0)),
            
            # Technical scores
            "technical_depth_score": self._safe_decimal(technical.get("depth", {}).get("score", 0)),
            "technical_breadth_score": self._safe_decimal(technical.get("breadth", {}).get("score", 0)),
            "practical_application_score": self._safe_decimal(technical.get("practical_application", {}).get("score", 0)),
            "industry_knowledge_score": self._safe_decimal(technical.get("industry_knowledge", {}).get("score", 0)),
            
            # Sentiment
            "overall_sentiment": sentiment.get("overall_sentiment", "neutral"),
            "sentiment_score": self._safe_decimal(sentiment.get("sentiment_score", 50)),
            "enthusiasm_level": sentiment.get("enthusiasm_level", "moderate"),
            "stress_indicators": sentiment.get("stress_indicators", []),
            
            # Behavioral
            "honesty_indicators": behavioral.get("honesty_indicators", []),
            "red_flag_behaviors": behavioral.get("red_flag_behaviors", []),
            "positive_behaviors": behavioral.get("positive_behaviors", []),
            
            # Detailed analysis JSON
            "soft_skills_analysis": soft_skills,
            "technical_analysis": technical,
            "communication_analysis": communication,
            "sentiment_analysis": sentiment,
            "behavioral_analysis": behavioral,
            "question_analyses": analysis.get("question_by_question", []),
            
            # Summary
            "key_strengths": summary.get("key_strengths", []),
            "areas_for_improvement": summary.get("areas_for_improvement", []),
            "notable_quotes": summary.get("notable_quotes", []),
            "follow_up_topics": summary.get("follow_up_topics", []),
            
            # Culture & Role fit
            "culture_fit_score": self._safe_decimal(culture_fit.get("score", 0)),
            "culture_fit_notes": culture_fit.get("notes", ""),
            "role_fit_score": self._safe_decimal(role_fit.get("score", 0)),
            "role_fit_analysis": role_fit.get("analysis", ""),
            
            # Recommendation
            "recommendation": recommendation.get("decision", "under_review"),
            "recommendation_confidence": self._safe_decimal(recommendation.get("confidence", 0)),
            "recommendation_summary": recommendation.get("summary", ""),
            "detailed_recommendation": recommendation.get("detailed", ""),
            
            # Metadata
            "total_questions": metadata.get("total_questions", 0),
            "total_responses": metadata.get("total_responses", 0),
            "average_response_length": metadata.get("average_response_length", 0),
        }

        # Check if analysis already exists
        existing = (
            db.service_client.table("detailed_interview_analysis")
            .select("id")
            .eq("interview_id", str(interview_id))
            .execute()
        )

        if existing.data:
            # Update existing
            result = (
                db.service_client.table("detailed_interview_analysis")
                .update(data)
                .eq("interview_id", str(interview_id))
                .execute()
            )
        else:
            # Insert new
            result = (
                db.service_client.table("detailed_interview_analysis")
                .insert(data)
                .execute()
            )

        return result.data[0] if result.data else data

    def _safe_decimal(self, value: Any) -> float:
        """Safely convert value to float for database storage"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    async def get_analysis(self, interview_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve stored analysis for an interview"""
        result = (
            db.service_client.table("detailed_interview_analysis")
            .select("*")
            .eq("interview_id", str(interview_id))
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_analysis_summary(self, interview_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a summary of the analysis for display"""
        analysis = await self.get_analysis(interview_id)
        if not analysis:
            return None

        return {
            "interview_id": analysis["interview_id"],
            "overall_score": analysis["overall_score"],
            "technical_score": analysis["technical_score"],
            "soft_skills_score": analysis["soft_skills_score"],
            "communication_score": analysis["communication_score"],
            "recommendation": analysis["recommendation"],
            "recommendation_summary": analysis["recommendation_summary"],
            "key_strengths": analysis["key_strengths"],
            "areas_for_improvement": analysis["areas_for_improvement"],
            "sentiment": analysis["overall_sentiment"],
            "enthusiasm": analysis["enthusiasm_level"],
            "analyzed_at": analysis["analyzed_at"],
        }

