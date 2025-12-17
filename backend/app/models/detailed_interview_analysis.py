"""
Detailed Interview Analysis Models
Pydantic models for comprehensive AI interview analysis
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


class QuestionAnalysis(BaseModel):
    """Analysis for a single question-response pair"""
    question_id: Optional[str] = None
    question_text: str
    response_text: str
    response_length: int = 0
    
    # Quality Assessment
    quality: str = "adequate"  # strong, adequate, weak
    relevance_score: Decimal = Field(default=Decimal("50"), ge=0, le=100)
    depth_score: Decimal = Field(default=Decimal("50"), ge=0, le=100)
    
    # Content Analysis
    key_points: List[str] = Field(default_factory=list)
    missed_opportunities: List[str] = Field(default_factory=list)
    
    # Technical Assessment (if applicable)
    technical_accuracy: Optional[Decimal] = None
    technical_keywords: List[str] = Field(default_factory=list)
    
    # Behavioral Indicators
    sentiment: str = "neutral"
    confidence_level: str = "moderate"
    
    # Notable Elements
    notable_quote: Optional[str] = None
    follow_up_needed: bool = False
    follow_up_reason: Optional[str] = None


class SoftSkillsAnalysis(BaseModel):
    """Detailed soft skills breakdown"""
    leadership: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    teamwork: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    problem_solving: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    adaptability: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    creativity: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    emotional_intelligence: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    time_management: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    conflict_resolution: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})


class CommunicationAnalysis(BaseModel):
    """Detailed communication assessment"""
    clarity: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    articulation: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    confidence: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    listening: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    persuasion: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    
    # Text-specific metrics
    vocabulary_level: str = "professional"  # basic, professional, advanced
    grammar_quality: str = "good"  # poor, acceptable, good, excellent
    response_structure: str = "adequate"  # poor, adequate, well-structured


class TechnicalAnalysis(BaseModel):
    """Technical skills assessment"""
    depth: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    breadth: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    practical_application: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    industry_knowledge: Dict[str, Any] = Field(default_factory=lambda: {"score": 0, "evidence": [], "notes": ""})
    
    # Skill-specific details
    skills_demonstrated: List[str] = Field(default_factory=list)
    skills_missing: List[str] = Field(default_factory=list)
    technical_red_flags: List[str] = Field(default_factory=list)


class SentimentAnalysis(BaseModel):
    """Sentiment and emotional analysis"""
    overall_sentiment: str = "neutral"  # positive, neutral, negative, mixed
    sentiment_score: Decimal = Field(default=Decimal("50"), ge=0, le=100)
    enthusiasm_level: str = "moderate"  # high, moderate, low
    
    # Emotional indicators
    stress_indicators: List[str] = Field(default_factory=list)
    positive_indicators: List[str] = Field(default_factory=list)
    
    # Sentiment breakdown per response
    sentiment_progression: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Key emotional moments
    notable_emotional_moments: List[str] = Field(default_factory=list)


class BehavioralAnalysis(BaseModel):
    """Behavioral and honesty assessment"""
    honesty_indicators: List[str] = Field(default_factory=list)
    consistency_score: Decimal = Field(default=Decimal("70"), ge=0, le=100)
    
    # Red flags
    red_flag_behaviors: List[str] = Field(default_factory=list)
    evasive_responses: List[str] = Field(default_factory=list)
    
    # Positive behaviors
    positive_behaviors: List[str] = Field(default_factory=list)
    
    # STAR method usage (Situation, Task, Action, Result)
    star_responses: int = 0
    uses_concrete_examples: bool = False


class DetailedInterviewAnalysisBase(BaseModel):
    """Base model for detailed interview analysis"""
    # Overall Scores
    overall_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    technical_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    soft_skills_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    communication_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    
    # Detailed Soft Skills Scores
    leadership_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    teamwork_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    problem_solving_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    adaptability_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    creativity_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    emotional_intelligence_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    time_management_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    conflict_resolution_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    
    # Communication Scores
    clarity_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    articulation_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    confidence_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    listening_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    persuasion_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    
    # Technical Scores
    technical_depth_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    technical_breadth_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    practical_application_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    industry_knowledge_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    
    # Sentiment
    overall_sentiment: str = "neutral"
    sentiment_score: Decimal = Field(default=Decimal("50"), ge=0, le=100)
    enthusiasm_level: str = "moderate"
    stress_indicators: List[str] = Field(default_factory=list)
    
    # Behavioral
    honesty_indicators: List[str] = Field(default_factory=list)
    red_flag_behaviors: List[str] = Field(default_factory=list)
    positive_behaviors: List[str] = Field(default_factory=list)
    
    # Detailed Analysis Objects
    soft_skills_analysis: Dict[str, Any] = Field(default_factory=dict)
    technical_analysis: Dict[str, Any] = Field(default_factory=dict)
    communication_analysis: Dict[str, Any] = Field(default_factory=dict)
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict)
    behavioral_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Question-by-Question
    question_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Summary
    key_strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    notable_quotes: List[str] = Field(default_factory=list)
    follow_up_topics: List[str] = Field(default_factory=list)
    
    # Culture & Role Fit
    culture_fit_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    culture_fit_notes: str = ""
    role_fit_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    role_fit_analysis: str = ""
    
    # Recommendation
    recommendation: str = "under_review"
    recommendation_confidence: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    recommendation_summary: str = ""
    detailed_recommendation: str = ""
    
    # Metadata
    total_questions: int = 0
    total_responses: int = 0
    average_response_length: int = 0
    interview_duration_seconds: int = 0


class DetailedInterviewAnalysisCreate(DetailedInterviewAnalysisBase):
    """Model for creating a new detailed interview analysis"""
    interview_id: UUID


class DetailedInterviewAnalysisUpdate(BaseModel):
    """Model for updating detailed interview analysis"""
    overall_score: Optional[Decimal] = None
    technical_score: Optional[Decimal] = None
    soft_skills_score: Optional[Decimal] = None
    communication_score: Optional[Decimal] = None
    
    # Allow updating any field
    leadership_score: Optional[Decimal] = None
    teamwork_score: Optional[Decimal] = None
    problem_solving_score: Optional[Decimal] = None
    adaptability_score: Optional[Decimal] = None
    creativity_score: Optional[Decimal] = None
    emotional_intelligence_score: Optional[Decimal] = None
    time_management_score: Optional[Decimal] = None
    conflict_resolution_score: Optional[Decimal] = None
    
    clarity_score: Optional[Decimal] = None
    articulation_score: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    listening_score: Optional[Decimal] = None
    persuasion_score: Optional[Decimal] = None
    
    technical_depth_score: Optional[Decimal] = None
    technical_breadth_score: Optional[Decimal] = None
    practical_application_score: Optional[Decimal] = None
    industry_knowledge_score: Optional[Decimal] = None
    
    overall_sentiment: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    enthusiasm_level: Optional[str] = None
    
    recommendation: Optional[str] = None
    recommendation_confidence: Optional[Decimal] = None
    recommendation_summary: Optional[str] = None
    detailed_recommendation: Optional[str] = None
    
    soft_skills_analysis: Optional[Dict[str, Any]] = None
    technical_analysis: Optional[Dict[str, Any]] = None
    communication_analysis: Optional[Dict[str, Any]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    behavioral_analysis: Optional[Dict[str, Any]] = None
    question_analyses: Optional[List[Dict[str, Any]]] = None
    
    key_strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    notable_quotes: Optional[List[str]] = None
    follow_up_topics: Optional[List[str]] = None
    
    culture_fit_score: Optional[Decimal] = None
    culture_fit_notes: Optional[str] = None
    role_fit_score: Optional[Decimal] = None
    role_fit_analysis: Optional[str] = None


class DetailedInterviewAnalysis(DetailedInterviewAnalysisBase):
    """Complete detailed interview analysis model"""
    id: UUID
    interview_id: UUID
    analysis_version: str = "1.0"
    analyzed_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

