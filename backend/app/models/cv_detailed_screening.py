"""
CV Detailed Screening Model
Comprehensive Pydantic models for detailed CV analysis (Resume Worded style)
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


class CVSectionScore(BaseModel):
    """Score for a specific CV section"""
    score: Decimal = Field(ge=0, le=100)
    max_score: Decimal = Field(default=Decimal("100"))
    feedback: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVFormatAnalysis(BaseModel):
    """Formatting analysis results"""
    overall_score: Decimal = Field(ge=0, le=100)
    consistency_score: Decimal = Field(ge=0, le=100, description="Fonts, dates, alignment, spacing")
    template_simplicity: Decimal = Field(ge=0, le=100, description="Simple, ATS-friendly template")
    font_readability: Decimal = Field(ge=0, le=100, description="Machine-readable fonts")
    page_length_score: Decimal = Field(ge=0, le=100, description="Appropriate length")
    white_space_score: Decimal = Field(ge=0, le=100, description="Margins and spacing")
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVStructureAnalysis(BaseModel):
    """Structure analysis results"""
    overall_score: Decimal = Field(ge=0, le=100)
    section_order_score: Decimal = Field(ge=0, le=100, description="Proper section ordering")
    contact_info_score: Decimal = Field(ge=0, le=100, description="Contact info placement")
    has_unnecessary_sections: bool = Field(default=False)
    unnecessary_sections: List[str] = Field(default_factory=list, description="e.g., photo, references")
    missing_sections: List[str] = Field(default_factory=list)
    detected_sections: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVExperienceAnalysis(BaseModel):
    """Work experience analysis results (most important)"""
    overall_score: Decimal = Field(ge=0, le=100)
    action_verbs_score: Decimal = Field(ge=0, le=100, description="Use of strong action verbs")
    quantification_score: Decimal = Field(ge=0, le=100, description="Quantified achievements")
    accomplishment_orientation_score: Decimal = Field(ge=0, le=100, description="Accomplishments vs responsibilities")
    relevance_score: Decimal = Field(ge=0, le=100, description="Relevance to job")
    keyword_match_score: Decimal = Field(ge=0, le=100, description="ATS keywords match")
    chronological_order: bool = Field(default=True)
    bullet_count: int = Field(default=0)
    quantified_bullets: int = Field(default=0)
    action_verb_bullets: int = Field(default=0)
    weak_bullets: List[str] = Field(default_factory=list)
    strong_bullets: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    found_keywords: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVEducationAnalysis(BaseModel):
    """Education section analysis"""
    overall_score: Decimal = Field(ge=0, le=100)
    completeness_score: Decimal = Field(ge=0, le=100, description="Institution, major, dates")
    relevance_score: Decimal = Field(ge=0, le=100, description="Relevance to job")
    has_gpa: bool = Field(default=False)
    gpa_value: Optional[str] = None
    institutions: List[str] = Field(default_factory=list)
    degrees: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVSkillsAnalysis(BaseModel):
    """Skills section analysis"""
    overall_score: Decimal = Field(ge=0, le=100)
    technical_skills_score: Decimal = Field(ge=0, le=100)
    soft_skills_score: Decimal = Field(ge=0, le=100)
    skill_match_score: Decimal = Field(ge=0, le=100, description="Match with job requirements")
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVLanguageAnalysis(BaseModel):
    """Language and writing quality analysis"""
    overall_score: Decimal = Field(ge=0, le=100)
    grammar_score: Decimal = Field(ge=0, le=100)
    spelling_score: Decimal = Field(ge=0, le=100)
    tense_consistency_score: Decimal = Field(ge=0, le=100, description="Past tense usage")
    no_pronouns_score: Decimal = Field(ge=0, le=100, description="Avoiding I, me, my")
    no_filler_words_score: Decimal = Field(ge=0, le=100)
    detected_issues: List[Dict[str, str]] = Field(default_factory=list)
    filler_words_found: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVATSCompatibility(BaseModel):
    """ATS (Applicant Tracking System) compatibility analysis"""
    overall_score: Decimal = Field(ge=0, le=100)
    parsability_score: Decimal = Field(ge=0, le=100, description="Can be parsed by ATS")
    keyword_optimization_score: Decimal = Field(ge=0, le=100)
    format_compatibility: Decimal = Field(ge=0, le=100)
    ats_friendly: bool = Field(default=True)
    potential_parsing_issues: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVImpactAnalysis(BaseModel):
    """Overall impact and effectiveness analysis"""
    overall_score: Decimal = Field(ge=0, le=100)
    brevity_score: Decimal = Field(ge=0, le=100, description="Conciseness")
    clarity_score: Decimal = Field(ge=0, le=100)
    professionalism_score: Decimal = Field(ge=0, le=100)
    uniqueness_score: Decimal = Field(ge=0, le=100, description="Stands out from others")
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CVDetailedScreeningCreate(BaseModel):
    """Model for creating detailed CV screening result"""
    application_id: UUID
    cv_id: UUID
    
    # Overall scores
    overall_score: Decimal = Field(ge=0, le=100)
    
    # Section scores (0-100)
    format_score: Decimal = Field(ge=0, le=100)
    structure_score: Decimal = Field(ge=0, le=100)
    experience_score: Decimal = Field(ge=0, le=100)
    education_score: Decimal = Field(ge=0, le=100)
    skills_score: Decimal = Field(ge=0, le=100)
    language_score: Decimal = Field(ge=0, le=100)
    ats_score: Decimal = Field(ge=0, le=100)
    impact_score: Decimal = Field(ge=0, le=100)
    
    # Job match score
    job_match_score: Decimal = Field(ge=0, le=100)
    
    # Detailed analysis objects (stored as JSONB)
    format_analysis: Optional[CVFormatAnalysis] = None
    structure_analysis: Optional[CVStructureAnalysis] = None
    experience_analysis: Optional[CVExperienceAnalysis] = None
    education_analysis: Optional[CVEducationAnalysis] = None
    skills_analysis: Optional[CVSkillsAnalysis] = None
    language_analysis: Optional[CVLanguageAnalysis] = None
    ats_analysis: Optional[CVATSCompatibility] = None
    impact_analysis: Optional[CVImpactAnalysis] = None
    
    # Summary
    top_strengths: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    # Hiring recommendation
    recommendation: str = Field(description="qualified, maybe_qualified, not_qualified")
    recommendation_reason: str = Field(default="")
    
    # Metadata
    analysis_version: str = Field(default="1.0")


class CVDetailedScreening(CVDetailedScreeningCreate):
    """Complete detailed CV screening result model"""
    id: UUID
    screened_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CVScreeningSummary(BaseModel):
    """Summary view for dashboard display"""
    id: UUID
    application_id: UUID
    overall_score: Decimal
    format_score: Decimal
    structure_score: Decimal
    experience_score: Decimal
    education_score: Decimal
    skills_score: Decimal
    language_score: Decimal
    ats_score: Decimal
    impact_score: Decimal
    job_match_score: Decimal
    recommendation: str
    top_strengths: List[str]
    critical_issues: List[str]
    screened_at: datetime

