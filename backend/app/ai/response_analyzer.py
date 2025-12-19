"""
Response Analyzer
Analyzes candidate responses to interview questions
"""

from typing import Dict, Any, Optional
from app.ai.providers import AIProviderFactory
from app.ai.prompts import InterviewPrompts
import structlog

logger = structlog.get_logger()


class ResponseAnalyzer:
    """Service for analyzing candidate responses"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize response analyzer
        
        Args:
            provider_name: AI provider to use
        """
        self.provider = AIProviderFactory.create_provider(provider_name)
        self.prompts = InterviewPrompts()
    
    async def analyze_response(
        self,
        question: str,
        response: str,
        job_description: Dict[str, Any],
        cv_text: str
    ) -> Dict[str, Any]:
        """
        Analyze a candidate's response
        
        Args:
            question: Interview question asked
            response: Candidate's response
            job_description: Job description data
            cv_text: Candidate CV text
        
        Returns:
            Analysis dictionary with:
            - quality: "strong", "adequate", or "weak"
            - relevance_score: 0-100
            - alignment_score: 0-100
            - strengths: List of strengths
            - weaknesses: List of weaknesses
            - red_flags: List of red flags
            - follow_up_suggestions: Suggested follow-up questions
        """
        try:
            prompt = self.prompts.get_response_analysis_prompt(
                question,
                response,
                job_description,
                cv_text
            )
            
            analysis_text = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt=self.prompts.SYSTEM_PROMPT,
                max_tokens=500,
                temperature=0.5
            )
            
            # Parse analysis (basic implementation - can be enhanced)
            return self._parse_analysis(analysis_text, response)
            
        except Exception as e:
            logger.error("Error analyzing response", error=str(e))
            return {
                "quality": "adequate",
                "relevance_score": 50,
                "alignment_score": 50,
                "strengths": [],
                "weaknesses": [],
                "red_flags": [],
                "follow_up_suggestions": []
            }
    
    def detect_non_answer_response(self, response: str) -> Optional[str]:
        """
        Detect if the response indicates the candidate is not ready, confused, or needs help.
        Returns a category if detected, None otherwise.
        
        Categories:
        - "not_ready": Candidate says they're not ready
        - "confused": Candidate is confused or doesn't understand
        - "decline": Candidate declines to answer
        - "need_help": Candidate needs help or clarification
        """
        response_lower = response.lower().strip()
        
        # Patterns indicating "not ready"
        not_ready_patterns = [
            "not ready", "i'm not ready", "im not ready", "not prepared",
            "need more time", "not ready yet", "unprepared", "not ready for",
            "can't do this", "cant do this", "don't want to", "dont want to"
        ]
        
        # Patterns indicating confusion
        confused_patterns = [
            "don't understand", "dont understand", "confused", "not sure what",
            "what do you mean", "can you explain", "i don't know", "i dont know",
            "not clear", "unclear", "what is", "what are"
        ]
        
        # Patterns indicating decline
        decline_patterns = [
            "don't want to answer", "dont want to answer", "prefer not to",
            "rather not", "can't answer", "cant answer", "won't answer", "wont answer",
            "no comment", "skip", "pass"
        ]
        
        # Patterns indicating need for help
        help_patterns = [
            "need help", "can you help", "help me", "don't know how",
            "how do i", "what should i", "need guidance", "need assistance"
        ]
        
        for pattern in not_ready_patterns:
            if pattern in response_lower:
                return "not_ready"
        
        for pattern in confused_patterns:
            if pattern in response_lower:
                return "confused"
        
        for pattern in decline_patterns:
            if pattern in response_lower:
                return "decline"
        
        for pattern in help_patterns:
            if pattern in response_lower:
                return "need_help"
        
        return None

    def _parse_analysis(self, analysis_text: str, response: str) -> Dict[str, Any]:
        """
        Parse AI analysis text into structured format
        
        Args:
            analysis_text: Raw analysis text from AI
            response: Original response (for fallback analysis)
        
        Returns:
            Structured analysis dictionary
        """
        # Check for non-answer responses first
        non_answer_type = self.detect_non_answer_response(response)
        
        # Basic parsing - can be enhanced with structured output
        analysis = {
            "quality": "adequate",
            "relevance_score": 50,
            "alignment_score": 50,
            "strengths": [],
            "weaknesses": [],
            "red_flags": [],
            "follow_up_suggestions": [],
            "non_answer_type": non_answer_type  # Add this to track non-answers
        }
        
        # If it's a non-answer, mark it appropriately
        if non_answer_type:
            analysis["quality"] = "weak"
            analysis["relevance_score"] = 10
            analysis["needs_clarification"] = True
            return analysis
        
        # Simple heuristics based on response length and keywords
        response_lower = response.lower().strip()
        response_length = len(response.split())
        
        # Treat very short or clearly generic answers as weak so we trigger clarification
        short_generic_phrases = {
            "yes", "yeah", "yep", "okay", "ok", "sure",
            "i dont want to talk about it",
        }
        if (
            response_lower in {"no", "nope", "nah"}
            or response_lower in short_generic_phrases
            or response_length <= 8
        ):
            analysis["quality"] = "weak"
            analysis["relevance_score"] = 20
        # Quality assessment
        elif response_length > 50 and any(word in response_lower for word in ["experience", "worked", "implemented", "achieved"]):
            analysis["quality"] = "strong"
            analysis["relevance_score"] = 75
        elif response_length < 20:
            analysis["quality"] = "weak"
            analysis["relevance_score"] = 30
        else:
            analysis["quality"] = "adequate"
            analysis["relevance_score"] = 60
        
        # Extract strengths/weaknesses from analysis text
        if "strong" in analysis_text.lower() or "excellent" in analysis_text.lower():
            analysis["strengths"].append("Clear and detailed response")
        
        if "vague" in analysis_text.lower() or "unclear" in analysis_text.lower():
            analysis["weaknesses"].append("Response lacks detail")
        
        if "inconsistent" in analysis_text.lower() or "contradict" in analysis_text.lower():
            analysis["red_flags"].append("Potential inconsistency with CV")
        
        return analysis
    
    async def assess_response_quality(
        self,
        question: str,
        response: str
    ) -> str:
        """
        Quick assessment of response quality
        
        Args:
            question: Interview question
            response: Candidate response
        
        Returns:
            "strong", "adequate", or "weak"
        """
        try:
            prompt = f"""Assess the quality of this interview response. Respond with ONLY one word: "strong", "adequate", or "weak".

Question: {question}
Response: {response}

Assessment:"""
            
            assessment = await self.provider.generate_completion(
                prompt=prompt,
                max_tokens=10,
                temperature=0.3
            )
            
            assessment = assessment.strip().lower()
            if "strong" in assessment:
                return "strong"
            elif "weak" in assessment:
                return "weak"
            else:
                return "adequate"
                
        except Exception as e:
            logger.error("Error assessing response quality", error=str(e))
            # Fallback: simple heuristic
            if len(response.split()) > 30:
                return "adequate"
            else:
                return "weak"

