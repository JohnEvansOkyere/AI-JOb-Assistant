"""
CV Detailed Analyzer Service
Comprehensive CV analysis similar to Resume Worded
Analyzes CVs across 20+ criteria including formatting, structure, 
experience quality, skills match, and ATS compatibility.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from app.ai.providers import AIProviderFactory
from app.database import db
from app.models.cv_detailed_screening import (
    CVFormatAnalysis,
    CVStructureAnalysis,
    CVExperienceAnalysis,
    CVEducationAnalysis,
    CVSkillsAnalysis,
    CVLanguageAnalysis,
    CVATSCompatibility,
    CVImpactAnalysis,
    CVDetailedScreeningCreate,
)
import structlog

logger = structlog.get_logger()


# Common action verbs for CV analysis
STRONG_ACTION_VERBS = [
    'achieved', 'administered', 'analyzed', 'built', 'collaborated',
    'conducted', 'created', 'delivered', 'designed', 'developed',
    'directed', 'drove', 'engineered', 'established', 'executed',
    'expanded', 'generated', 'grew', 'implemented', 'improved',
    'increased', 'initiated', 'innovated', 'launched', 'led',
    'managed', 'maximized', 'negotiated', 'optimized', 'orchestrated',
    'organized', 'pioneered', 'planned', 'produced', 'reduced',
    'resolved', 'restructured', 'revamped', 'scaled', 'secured',
    'spearheaded', 'streamlined', 'strengthened', 'succeeded',
    'supervised', 'transformed', 'unified', 'upgraded'
]

# Weak/filler words to avoid
FILLER_WORDS = [
    'very', 'really', 'basically', 'actually', 'literally',
    'just', 'simply', 'effectively', 'successfully', 'skillfully',
    'various', 'several', 'many', 'some', 'etc'
]

# Personal pronouns to avoid
PERSONAL_PRONOUNS = ['i', 'me', 'my', 'mine', 'myself', 'we', 'our', 'ours']

# Common CV sections
EXPECTED_SECTIONS = [
    'contact', 'summary', 'objective', 'experience', 'work',
    'education', 'skills', 'projects', 'certifications',
    'languages', 'interests', 'references'
]

# Unnecessary sections (usually should be removed)
UNNECESSARY_SECTIONS = ['references', 'photo', 'objective', 'hobbies']


class CVDetailedAnalyzer:
    """Comprehensive CV analyzer with 20+ screening criteria"""
    
    def __init__(self, provider_name: Optional[str] = None):
        """Initialize analyzer with AI provider"""
        self.provider = AIProviderFactory.create_provider(provider_name)
    
    async def analyze_cv(
        self,
        cv_text: str,
        job_description: Dict[str, Any],
        cv_id: UUID,
        application_id: UUID
    ) -> CVDetailedScreeningCreate:
        """
        Perform comprehensive CV analysis
        
        Args:
            cv_text: Raw CV text content
            job_description: Job description data
            cv_id: CV ID
            application_id: Application ID
            
        Returns:
            CVDetailedScreeningCreate with all analysis results
        """
        logger.info("Starting detailed CV analysis", application_id=str(application_id))
        
        try:
            # Run all analyses
            format_analysis = self._analyze_formatting(cv_text)
            structure_analysis = self._analyze_structure(cv_text)
            experience_analysis = await self._analyze_experience(cv_text, job_description)
            education_analysis = self._analyze_education(cv_text, job_description)
            skills_analysis = await self._analyze_skills(cv_text, job_description)
            language_analysis = self._analyze_language(cv_text)
            ats_analysis = self._analyze_ats_compatibility(cv_text, job_description)
            impact_analysis = await self._analyze_impact(cv_text, job_description)
            
            # Calculate job match score with AI
            job_match_score = await self._calculate_job_match(cv_text, job_description)
            
            # Calculate overall score (weighted average)
            overall_score = self._calculate_overall_score(
                format_analysis.overall_score,
                structure_analysis.overall_score,
                experience_analysis.overall_score,
                education_analysis.overall_score,
                skills_analysis.overall_score,
                language_analysis.overall_score,
                ats_analysis.overall_score,
                impact_analysis.overall_score,
                job_match_score
            )
            
            # Compile top strengths and issues
            top_strengths = self._compile_strengths(
                format_analysis, structure_analysis, experience_analysis,
                education_analysis, skills_analysis, ats_analysis, impact_analysis
            )
            
            critical_issues = self._compile_issues(
                format_analysis, structure_analysis, experience_analysis,
                education_analysis, skills_analysis, language_analysis,
                ats_analysis, impact_analysis
            )
            
            improvement_suggestions = self._compile_suggestions(
                format_analysis, structure_analysis, experience_analysis,
                education_analysis, skills_analysis, language_analysis,
                ats_analysis, impact_analysis
            )
            
            # Determine recommendation
            recommendation, reason = self._determine_recommendation(
                overall_score, job_match_score, critical_issues
            )
            
            result = CVDetailedScreeningCreate(
                application_id=application_id,
                cv_id=cv_id,
                overall_score=overall_score,
                format_score=format_analysis.overall_score,
                structure_score=structure_analysis.overall_score,
                experience_score=experience_analysis.overall_score,
                education_score=education_analysis.overall_score,
                skills_score=skills_analysis.overall_score,
                language_score=language_analysis.overall_score,
                ats_score=ats_analysis.overall_score,
                impact_score=impact_analysis.overall_score,
                job_match_score=job_match_score,
                format_analysis=format_analysis,
                structure_analysis=structure_analysis,
                experience_analysis=experience_analysis,
                education_analysis=education_analysis,
                skills_analysis=skills_analysis,
                language_analysis=language_analysis,
                ats_analysis=ats_analysis,
                impact_analysis=impact_analysis,
                top_strengths=top_strengths[:5],
                critical_issues=critical_issues[:5],
                improvement_suggestions=improvement_suggestions[:10],
                recommendation=recommendation,
                recommendation_reason=reason,
                analysis_version="1.0"
            )
            
            logger.info(
                "CV analysis completed",
                application_id=str(application_id),
                overall_score=float(overall_score)
            )
            
            return result
            
        except Exception as e:
            logger.error("Error in CV analysis", error=str(e), exc_info=True)
            # Return default analysis on error
            return self._create_default_analysis(application_id, cv_id, str(e))
    
    def _analyze_formatting(self, cv_text: str) -> CVFormatAnalysis:
        """Analyze CV formatting quality"""
        issues = []
        suggestions = []
        
        lines = cv_text.split('\n')
        total_lines = len(lines)
        word_count = len(cv_text.split())
        
        # Consistency score (check for consistent patterns)
        consistency_score = Decimal("75")  # Default good
        
        # Template simplicity (no complex formatting detected in text)
        template_simplicity = Decimal("80")
        
        # Font readability (assumed readable if text extracted)
        font_readability = Decimal("85")
        
        # Page length score
        if word_count < 200:
            page_length_score = Decimal("40")
            issues.append("CV appears too short (less than 200 words)")
            suggestions.append("Add more detail about your experiences and achievements")
        elif word_count > 1500:
            page_length_score = Decimal("60")
            issues.append("CV may be too long (over 1500 words)")
            suggestions.append("Consider condensing to focus on most relevant experiences")
        elif word_count > 800:
            page_length_score = Decimal("75")
        else:
            page_length_score = Decimal("90")
        
        # White space score
        empty_lines = sum(1 for line in lines if not line.strip())
        white_space_ratio = empty_lines / max(total_lines, 1)
        if white_space_ratio < 0.1:
            white_space_score = Decimal("60")
            issues.append("CV appears dense with insufficient white space")
            suggestions.append("Add spacing between sections for better readability")
        elif white_space_ratio > 0.4:
            white_space_score = Decimal("70")
            issues.append("CV has too much white space")
        else:
            white_space_score = Decimal("85")
        
        # Calculate overall format score
        overall_score = (
            consistency_score * Decimal("0.2") +
            template_simplicity * Decimal("0.2") +
            font_readability * Decimal("0.2") +
            page_length_score * Decimal("0.2") +
            white_space_score * Decimal("0.2")
        )
        
        return CVFormatAnalysis(
            overall_score=overall_score,
            consistency_score=consistency_score,
            template_simplicity=template_simplicity,
            font_readability=font_readability,
            page_length_score=page_length_score,
            white_space_score=white_space_score,
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_structure(self, cv_text: str) -> CVStructureAnalysis:
        """Analyze CV structure and organization"""
        issues = []
        suggestions = []
        detected_sections = []
        missing_sections = []
        unnecessary_found = []
        
        cv_lower = cv_text.lower()
        
        # Detect sections
        section_patterns = {
            'contact': r'(email|phone|address|contact)',
            'experience': r'(experience|work history|employment|career)',
            'education': r'(education|academic|qualification|degree)',
            'skills': r'(skills|competencies|expertise|technical)',
            'summary': r'(summary|profile|about|overview)',
            'objective': r'(objective|goal|seeking)',
            'projects': r'(projects|portfolio)',
            'certifications': r'(certifications|licenses|credentials)',
            'references': r'(references|referees)',
        }
        
        for section, pattern in section_patterns.items():
            if re.search(pattern, cv_lower):
                detected_sections.append(section)
                if section in UNNECESSARY_SECTIONS:
                    unnecessary_found.append(section)
        
        # Check for essential sections
        essential = ['contact', 'experience', 'education', 'skills']
        for section in essential:
            if section not in detected_sections:
                missing_sections.append(section)
        
        # Section order score
        section_order_score = Decimal("80")
        if 'experience' not in detected_sections:
            section_order_score = Decimal("50")
            issues.append("Work experience section not clearly identified")
        
        # Contact info score
        contact_patterns = [r'[\w\.-]+@[\w\.-]+', r'\+?\d[\d\s\-]{8,}']
        has_email = bool(re.search(contact_patterns[0], cv_text))
        has_phone = bool(re.search(contact_patterns[1], cv_text))
        
        if has_email and has_phone:
            contact_info_score = Decimal("100")
        elif has_email:
            contact_info_score = Decimal("75")
            issues.append("Phone number not found")
            suggestions.append("Add a contact phone number")
        elif has_phone:
            contact_info_score = Decimal("60")
            issues.append("Email address not found")
            suggestions.append("Add a professional email address")
        else:
            contact_info_score = Decimal("30")
            issues.append("Contact information (email/phone) not found")
            suggestions.append("Add email and phone number at the top of your CV")
        
        # Handle unnecessary sections
        has_unnecessary = len(unnecessary_found) > 0
        if has_unnecessary:
            for section in unnecessary_found:
                if section == 'references':
                    issues.append("References section is unnecessary")
                    suggestions.append("Remove 'References available upon request' - employers will ask if needed")
                elif section == 'objective':
                    issues.append("Objective section is outdated")
                    suggestions.append("Replace Objective with a brief professional Summary")
        
        # Missing sections
        for section in missing_sections:
            issues.append(f"Missing {section.capitalize()} section")
        
        # Calculate overall structure score
        base_score = Decimal("70")
        if missing_sections:
            base_score -= Decimal(str(len(missing_sections) * 10))
        if unnecessary_found:
            base_score -= Decimal(str(len(unnecessary_found) * 5))
        
        overall_score = (
            section_order_score * Decimal("0.3") +
            contact_info_score * Decimal("0.3") +
            max(base_score, Decimal("20")) * Decimal("0.4")
        )
        
        return CVStructureAnalysis(
            overall_score=min(overall_score, Decimal("100")),
            section_order_score=section_order_score,
            contact_info_score=contact_info_score,
            has_unnecessary_sections=has_unnecessary,
            unnecessary_sections=unnecessary_found,
            missing_sections=missing_sections,
            detected_sections=detected_sections,
            issues=issues,
            suggestions=suggestions
        )
    
    async def _analyze_experience(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> CVExperienceAnalysis:
        """Analyze work experience section quality"""
        issues = []
        suggestions = []
        weak_bullets = []
        strong_bullets = []
        
        # Extract bullet points (lines starting with - or •)
        bullet_pattern = r'^[\s]*[-•*]\s*(.+)$'
        bullets = re.findall(bullet_pattern, cv_text, re.MULTILINE)
        
        # Also check numbered points and regular lines in experience section
        lines = cv_text.split('\n')
        bullet_count = len(bullets)
        
        # Analyze action verbs
        action_verb_count = 0
        quantified_count = 0
        
        for bullet in bullets:
            bullet_lower = bullet.lower().strip()
            first_word = bullet_lower.split()[0] if bullet_lower.split() else ""
            
            # Check for action verbs
            if any(verb in first_word for verb in STRONG_ACTION_VERBS):
                action_verb_count += 1
                strong_bullets.append(bullet[:100])
            else:
                if len(bullet) > 20:  # Only flag substantial bullets
                    weak_bullets.append(bullet[:100])
            
            # Check for quantification (numbers, percentages, dollar amounts)
            if re.search(r'\d+%|\$[\d,]+|\d+\s*(people|team|members|users|clients)', bullet_lower):
                quantified_count += 1
        
        # Calculate scores
        if bullet_count > 0:
            action_verbs_score = Decimal(str(min(100, (action_verb_count / bullet_count) * 100)))
            quantification_score = Decimal(str(min(100, (quantified_count / bullet_count) * 100)))
        else:
            action_verbs_score = Decimal("50")
            quantification_score = Decimal("40")
            issues.append("No clear bullet points found in experience section")
            suggestions.append("Use bullet points to highlight your achievements")
        
        # Accomplishment orientation (use AI for deeper analysis)
        accomplishment_score = await self._ai_analyze_accomplishments(cv_text)
        
        # Relevance to job
        job_requirements = job_description.get('requirements', '')
        job_title = job_description.get('title', '')
        relevance_score = await self._ai_analyze_relevance(cv_text, job_requirements, job_title)
        
        # Keyword match
        keywords = self._extract_job_keywords(job_description)
        found_keywords = []
        missing_keywords = []
        
        cv_lower = cv_text.lower()
        for keyword in keywords:
            if keyword.lower() in cv_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        if keywords:
            keyword_score = Decimal(str(min(100, (len(found_keywords) / len(keywords)) * 100)))
        else:
            keyword_score = Decimal("70")
        
        # Check chronological order (simplified)
        year_pattern = r'\b(19|20)\d{2}\b'
        years = [int(y) for y in re.findall(year_pattern, cv_text)]
        chronological = all(years[i] >= years[i+1] for i in range(len(years)-1)) if len(years) > 1 else True
        
        # Generate issues and suggestions
        if action_verbs_score < 60:
            issues.append("Many bullet points don't start with strong action verbs")
            suggestions.append("Start each bullet point with action verbs like 'Developed', 'Managed', 'Achieved'")
        
        if quantification_score < 50:
            issues.append("Achievements are not quantified with numbers")
            suggestions.append("Add metrics like '15%', '$50K', 'team of 5' to demonstrate impact")
        
        if missing_keywords:
            issues.append(f"Missing {len(missing_keywords)} key terms from job description")
            suggestions.append(f"Consider adding relevant keywords: {', '.join(missing_keywords[:5])}")
        
        # Calculate overall experience score (most important section - weighted)
        overall_score = (
            action_verbs_score * Decimal("0.25") +
            quantification_score * Decimal("0.25") +
            accomplishment_score * Decimal("0.20") +
            relevance_score * Decimal("0.15") +
            keyword_score * Decimal("0.15")
        )
        
        return CVExperienceAnalysis(
            overall_score=overall_score,
            action_verbs_score=action_verbs_score,
            quantification_score=quantification_score,
            accomplishment_orientation_score=accomplishment_score,
            relevance_score=relevance_score,
            keyword_match_score=keyword_score,
            chronological_order=chronological,
            bullet_count=bullet_count,
            quantified_bullets=quantified_count,
            action_verb_bullets=action_verb_count,
            weak_bullets=weak_bullets[:5],
            strong_bullets=strong_bullets[:5],
            missing_keywords=missing_keywords[:10],
            found_keywords=found_keywords,
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_education(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> CVEducationAnalysis:
        """Analyze education section"""
        issues = []
        suggestions = []
        
        cv_lower = cv_text.lower()
        
        # Detect degree patterns
        degree_patterns = [
            r"(bachelor'?s?|b\.?s\.?|b\.?a\.?|b\.?sc\.?)",
            r"(master'?s?|m\.?s\.?|m\.?a\.?|m\.?sc\.?|mba)",
            r"(ph\.?d\.?|doctorate|doctoral)",
            r"(associate'?s?|a\.?s\.?|a\.?a\.?)",
            r"(diploma|certificate)"
        ]
        
        degrees_found = []
        for pattern in degree_patterns:
            matches = re.findall(pattern, cv_lower)
            degrees_found.extend(matches)
        
        # Detect institutions (basic heuristic)
        institution_patterns = r'(university|college|institute|school|academy)'
        institutions = re.findall(institution_patterns, cv_lower)
        
        # Check for GPA
        gpa_pattern = r'(gpa|grade point|cgpa)[:\s]*(\d+\.?\d*)'
        gpa_match = re.search(gpa_pattern, cv_lower)
        has_gpa = gpa_match is not None
        gpa_value = gpa_match.group(2) if gpa_match else None
        
        # Calculate scores
        if degrees_found:
            completeness_score = Decimal("80")
        elif institutions:
            completeness_score = Decimal("60")
            issues.append("Degree not clearly specified")
            suggestions.append("Clearly state your degree (e.g., B.S. in Computer Science)")
        else:
            completeness_score = Decimal("40")
            issues.append("Education section not clearly identified")
            suggestions.append("Add your educational background with institution, degree, and graduation year")
        
        # Relevance to job
        job_requirements = job_description.get('requirements', '').lower()
        if any(d in job_requirements for d in ['bachelor', 'master', 'degree', 'education']):
            if degrees_found:
                relevance_score = Decimal("85")
            else:
                relevance_score = Decimal("50")
                issues.append("Job requires specific education level - ensure this is clearly stated")
        else:
            relevance_score = Decimal("75")
        
        # Overall education score
        overall_score = (
            completeness_score * Decimal("0.6") +
            relevance_score * Decimal("0.4")
        )
        
        return CVEducationAnalysis(
            overall_score=overall_score,
            completeness_score=completeness_score,
            relevance_score=relevance_score,
            has_gpa=has_gpa,
            gpa_value=gpa_value,
            institutions=list(set(institutions))[:5],
            degrees=list(set(degrees_found))[:5],
            issues=issues,
            suggestions=suggestions
        )
    
    async def _analyze_skills(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> CVSkillsAnalysis:
        """Analyze skills section"""
        issues = []
        suggestions = []
        
        # Use AI to extract skills
        skills_data = await self._ai_extract_skills(cv_text, job_description)
        
        technical_skills = skills_data.get('technical', [])
        soft_skills = skills_data.get('soft', [])
        matched_skills = skills_data.get('matched', [])
        missing_skills = skills_data.get('missing', [])
        
        # Calculate scores
        if technical_skills:
            technical_score = Decimal("80")
        else:
            technical_score = Decimal("50")
            issues.append("No technical skills clearly identified")
            suggestions.append("List your technical skills (programming languages, tools, platforms)")
        
        if soft_skills:
            soft_score = Decimal("75")
        else:
            soft_score = Decimal("60")
        
        # Job match score
        total_required = len(matched_skills) + len(missing_skills)
        if total_required > 0:
            skill_match_score = Decimal(str((len(matched_skills) / total_required) * 100))
        else:
            skill_match_score = Decimal("70")
        
        if missing_skills:
            issues.append(f"Missing {len(missing_skills)} skills mentioned in job description")
            suggestions.append(f"Consider highlighting if you have: {', '.join(missing_skills[:5])}")
        
        overall_score = (
            technical_score * Decimal("0.35") +
            soft_score * Decimal("0.20") +
            skill_match_score * Decimal("0.45")
        )
        
        return CVSkillsAnalysis(
            overall_score=overall_score,
            technical_skills_score=technical_score,
            soft_skills_score=soft_score,
            skill_match_score=skill_match_score,
            technical_skills=technical_skills,
            soft_skills=soft_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_language(self, cv_text: str) -> CVLanguageAnalysis:
        """Analyze writing quality and language"""
        issues = []
        suggestions = []
        detected_issues = []
        filler_words_found = []
        
        cv_lower = cv_text.lower()
        words = cv_text.split()
        
        # Check for personal pronouns
        pronoun_count = sum(1 for word in words if word.lower() in PERSONAL_PRONOUNS)
        pronoun_ratio = pronoun_count / max(len(words), 1)
        
        if pronoun_ratio > 0.02:
            no_pronouns_score = Decimal("50")
            issues.append("Personal pronouns (I, me, my) found in CV")
            suggestions.append("Remove personal pronouns - instead of 'I managed', use 'Managed'")
        else:
            no_pronouns_score = Decimal("90")
        
        # Check for filler words
        for word in FILLER_WORDS:
            if re.search(rf'\b{word}\b', cv_lower):
                filler_words_found.append(word)
        
        if filler_words_found:
            no_filler_score = Decimal(str(max(50, 100 - len(filler_words_found) * 10)))
            issues.append(f"Filler words found: {', '.join(filler_words_found[:5])}")
            suggestions.append("Remove vague words like 'various', 'several', 'effectively'")
        else:
            no_filler_score = Decimal("90")
        
        # Tense consistency (simplified check)
        past_tense_indicators = len(re.findall(r'\b\w+ed\b', cv_lower))
        present_tense_indicators = len(re.findall(r'\b(manage|develop|create|lead|work)s?\b', cv_lower))
        
        if past_tense_indicators > present_tense_indicators:
            tense_score = Decimal("85")
        else:
            tense_score = Decimal("70")
            suggestions.append("Use past tense consistently (e.g., 'Managed', 'Developed')")
        
        # Grammar score (simplified - would need NLP for proper analysis)
        grammar_score = Decimal("80")
        spelling_score = Decimal("80")
        
        # Overall language score
        overall_score = (
            grammar_score * Decimal("0.25") +
            spelling_score * Decimal("0.15") +
            tense_score * Decimal("0.20") +
            no_pronouns_score * Decimal("0.20") +
            no_filler_score * Decimal("0.20")
        )
        
        return CVLanguageAnalysis(
            overall_score=overall_score,
            grammar_score=grammar_score,
            spelling_score=spelling_score,
            tense_consistency_score=tense_score,
            no_pronouns_score=no_pronouns_score,
            no_filler_words_score=no_filler_score,
            detected_issues=detected_issues,
            filler_words_found=filler_words_found,
            issues=issues,
            suggestions=suggestions
        )
    
    def _analyze_ats_compatibility(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> CVATSCompatibility:
        """Analyze ATS (Applicant Tracking System) compatibility"""
        issues = []
        suggestions = []
        parsing_issues = []
        
        # Check for parsability issues
        
        # Special characters that might cause issues
        special_chars = re.findall(r'[^\x00-\x7F]+', cv_text)
        if special_chars:
            parsing_issues.append("Non-ASCII characters detected")
            suggestions.append("Use standard ASCII characters for maximum ATS compatibility")
        
        # Check for structured format (headers, sections)
        has_clear_sections = len(re.findall(r'\n\s*[A-Z][A-Za-z\s]+[:\n]', cv_text)) >= 3
        
        if has_clear_sections:
            parsability_score = Decimal("85")
        else:
            parsability_score = Decimal("65")
            issues.append("CV structure may not be clearly parsable by ATS")
            suggestions.append("Use clear section headers (EXPERIENCE, EDUCATION, SKILLS)")
        
        # Keyword optimization
        keywords = self._extract_job_keywords(job_description)
        cv_lower = cv_text.lower()
        matched = sum(1 for k in keywords if k.lower() in cv_lower)
        
        if keywords:
            keyword_score = Decimal(str(min(100, (matched / len(keywords)) * 100)))
        else:
            keyword_score = Decimal("70")
        
        if keyword_score < 60:
            issues.append("CV may not pass ATS keyword filters")
            suggestions.append("Include more keywords from the job description")
        
        # Format compatibility (text-based CV is ATS-friendly)
        format_score = Decimal("85")
        
        # Check for tables/columns (might cause ATS issues)
        if re.search(r'\|\s*\||\t{2,}', cv_text):
            format_score = Decimal("60")
            parsing_issues.append("Table-like formatting detected")
            suggestions.append("Avoid using tables - use simple bullet points")
        
        ats_friendly = parsability_score >= 70 and keyword_score >= 50
        
        overall_score = (
            parsability_score * Decimal("0.35") +
            keyword_score * Decimal("0.40") +
            format_score * Decimal("0.25")
        )
        
        return CVATSCompatibility(
            overall_score=overall_score,
            parsability_score=parsability_score,
            keyword_optimization_score=keyword_score,
            format_compatibility=format_score,
            ats_friendly=ats_friendly,
            potential_parsing_issues=parsing_issues,
            issues=issues,
            suggestions=suggestions
        )
    
    async def _analyze_impact(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> CVImpactAnalysis:
        """Analyze overall impact and effectiveness"""
        issues = []
        suggestions = []
        
        # Brevity score
        word_count = len(cv_text.split())
        if 300 <= word_count <= 800:
            brevity_score = Decimal("90")
        elif word_count < 300:
            brevity_score = Decimal("60")
            issues.append("CV appears too brief")
        elif word_count > 1200:
            brevity_score = Decimal("60")
            issues.append("CV may be too long")
            suggestions.append("Condense to most relevant and impactful information")
        else:
            brevity_score = Decimal("75")
        
        # Use AI for clarity and professionalism analysis
        impact_data = await self._ai_analyze_overall_impact(cv_text, job_description)
        
        clarity_score = Decimal(str(impact_data.get('clarity', 70)))
        professionalism_score = Decimal(str(impact_data.get('professionalism', 75)))
        uniqueness_score = Decimal(str(impact_data.get('uniqueness', 65)))
        
        # Add AI-generated suggestions
        ai_suggestions = impact_data.get('suggestions', [])
        suggestions.extend(ai_suggestions[:3])
        
        overall_score = (
            brevity_score * Decimal("0.25") +
            clarity_score * Decimal("0.25") +
            professionalism_score * Decimal("0.30") +
            uniqueness_score * Decimal("0.20")
        )
        
        return CVImpactAnalysis(
            overall_score=overall_score,
            brevity_score=brevity_score,
            clarity_score=clarity_score,
            professionalism_score=professionalism_score,
            uniqueness_score=uniqueness_score,
            issues=issues,
            suggestions=suggestions
        )
    
    # AI-assisted analysis methods
    
    async def _ai_analyze_accomplishments(self, cv_text: str) -> Decimal:
        """Use AI to analyze accomplishment orientation"""
        try:
            prompt = f"""Analyze this CV and rate how well it focuses on accomplishments vs responsibilities.
            
CV Text:
{cv_text[:2000]}

Rate from 0-100 where:
- 0-40: Mostly lists job duties/responsibilities
- 41-70: Mix of responsibilities and achievements
- 71-100: Focuses on specific accomplishments with measurable impact

Return ONLY a number between 0 and 100."""
            
            response = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt="You are a CV analysis expert. Return only a numeric score.",
                max_tokens=50,
                temperature=0.3
            )
            
            score = int(re.search(r'\d+', response).group())
            return Decimal(str(min(100, max(0, score))))
        except:
            return Decimal("60")
    
    async def _ai_analyze_relevance(
        self,
        cv_text: str,
        job_requirements: str,
        job_title: str
    ) -> Decimal:
        """Use AI to analyze relevance to job"""
        try:
            prompt = f"""Rate how relevant this CV is for the job position.

Job Title: {job_title}
Job Requirements: {job_requirements[:500]}

CV Text:
{cv_text[:2000]}

Rate from 0-100 where:
- 0-40: Not relevant to the job
- 41-70: Somewhat relevant, has some matching experience
- 71-100: Highly relevant, experience closely matches requirements

Return ONLY a number between 0 and 100."""
            
            response = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt="You are a recruiting expert. Return only a numeric score.",
                max_tokens=50,
                temperature=0.3
            )
            
            score = int(re.search(r'\d+', response).group())
            return Decimal(str(min(100, max(0, score))))
        except:
            return Decimal("60")
    
    async def _ai_extract_skills(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Use AI to extract and categorize skills"""
        try:
            job_req = job_description.get('requirements', '')
            prompt = f"""Extract skills from this CV and compare with job requirements.

CV Text:
{cv_text[:2000]}

Job Requirements:
{job_req[:500]}

Return a JSON object with:
{{
    "technical": ["list of technical skills found in CV"],
    "soft": ["list of soft skills found in CV"],
    "matched": ["skills that match job requirements"],
    "missing": ["required skills not found in CV"]
}}

Return ONLY the JSON object, no other text."""
            
            response = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt="You are a skills analysis expert. Return only valid JSON.",
                max_tokens=500,
                temperature=0.3
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"technical": [], "soft": [], "matched": [], "missing": []}
        except Exception as e:
            logger.error("Error extracting skills", error=str(e))
            return {"technical": [], "soft": [], "matched": [], "missing": []}
    
    async def _ai_analyze_overall_impact(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI for overall impact analysis"""
        try:
            prompt = f"""Analyze this CV for overall impact and effectiveness.

CV Text:
{cv_text[:2000]}

Job Title: {job_description.get('title', 'N/A')}

Return a JSON object with scores (0-100) and suggestions:
{{
    "clarity": <score for how clear and easy to understand>,
    "professionalism": <score for professional presentation>,
    "uniqueness": <score for standing out from other candidates>,
    "suggestions": ["top 3 suggestions to improve impact"]
}}

Return ONLY the JSON object."""
            
            response = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt="You are a CV expert. Return only valid JSON.",
                max_tokens=300,
                temperature=0.3
            )
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            return {"clarity": 70, "professionalism": 75, "uniqueness": 65, "suggestions": []}
        except:
            return {"clarity": 70, "professionalism": 75, "uniqueness": 65, "suggestions": []}
    
    async def _calculate_job_match(
        self,
        cv_text: str,
        job_description: Dict[str, Any]
    ) -> Decimal:
        """Calculate overall job match score using AI"""
        try:
            prompt = f"""Rate how well this candidate matches the job requirements.

Job Title: {job_description.get('title', 'N/A')}
Job Description: {job_description.get('description', '')[:500]}
Requirements: {job_description.get('requirements', '')[:500]}

CV Text:
{cv_text[:2000]}

Consider:
- Skills match
- Experience level match
- Education requirements
- Industry relevance

Rate from 0-100. Return ONLY a number."""
            
            response = await self.provider.generate_completion(
                prompt=prompt,
                system_prompt="You are a recruiting expert. Return only a numeric score.",
                max_tokens=50,
                temperature=0.3
            )
            
            score = int(re.search(r'\d+', response).group())
            return Decimal(str(min(100, max(0, score))))
        except:
            return Decimal("60")
    
    # Helper methods
    
    def _extract_job_keywords(self, job_description: Dict[str, Any]) -> List[str]:
        """Extract important keywords from job description"""
        text = f"{job_description.get('title', '')} {job_description.get('description', '')} {job_description.get('requirements', '')}"
        
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b[A-Za-z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter common words and get unique keywords
        common_words = {'the', 'and', 'for', 'with', 'you', 'will', 'are', 'this', 'that', 'have', 'your'}
        keywords = [w for w in words if w.lower() not in common_words and len(w) > 3]
        
        # Return unique keywords (limit to 20)
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k.lower() not in seen:
                seen.add(k.lower())
                unique_keywords.append(k)
        
        return unique_keywords[:20]
    
    def _calculate_overall_score(self, *scores) -> Decimal:
        """Calculate weighted overall score"""
        weights = [
            Decimal("0.08"),   # format
            Decimal("0.08"),   # structure
            Decimal("0.25"),   # experience (most important)
            Decimal("0.08"),   # education
            Decimal("0.12"),   # skills
            Decimal("0.08"),   # language
            Decimal("0.10"),   # ATS
            Decimal("0.08"),   # impact
            Decimal("0.13"),   # job match
        ]
        
        total = sum(score * weight for score, weight in zip(scores, weights))
        return min(Decimal("100"), max(Decimal("0"), total))
    
    def _compile_strengths(self, *analyses) -> List[str]:
        """Compile top strengths from all analyses"""
        strengths = []
        
        for analysis in analyses:
            if hasattr(analysis, 'overall_score') and analysis.overall_score >= 75:
                section_name = type(analysis).__name__.replace('CV', '').replace('Analysis', '')
                strengths.append(f"Strong {section_name.lower()} section")
        
        # Add specific strengths
        for analysis in analyses:
            if hasattr(analysis, 'strong_bullets') and analysis.strong_bullets:
                strengths.append("Uses strong action verbs in experience")
            if hasattr(analysis, 'quantified_bullets') and analysis.quantified_bullets > 3:
                strengths.append("Quantifies achievements with metrics")
            if hasattr(analysis, 'matched_skills') and len(analysis.matched_skills) > 5:
                strengths.append("Skills closely match job requirements")
            if hasattr(analysis, 'ats_friendly') and analysis.ats_friendly:
                strengths.append("ATS-friendly format")
        
        return list(set(strengths))
    
    def _compile_issues(self, *analyses) -> List[str]:
        """Compile critical issues from all analyses"""
        issues = []
        for analysis in analyses:
            if hasattr(analysis, 'issues'):
                issues.extend(analysis.issues)
        return issues
    
    def _compile_suggestions(self, *analyses) -> List[str]:
        """Compile improvement suggestions from all analyses"""
        suggestions = []
        for analysis in analyses:
            if hasattr(analysis, 'suggestions'):
                suggestions.extend(analysis.suggestions)
        return list(set(suggestions))
    
    def _determine_recommendation(
        self,
        overall_score: Decimal,
        job_match_score: Decimal,
        issues: List[str]
    ) -> Tuple[str, str]:
        """Determine hiring recommendation"""
        critical_issue_count = len([i for i in issues if 'not found' in i.lower() or 'missing' in i.lower()])
        
        if overall_score >= 75 and job_match_score >= 70:
            return "qualified", "Strong CV with good job match. Recommended for interview."
        elif overall_score >= 60 and job_match_score >= 55:
            return "maybe_qualified", "CV has potential but could be improved. Consider for interview."
        elif critical_issue_count > 3:
            return "not_qualified", "Multiple critical issues found. CV needs significant improvement."
        else:
            return "maybe_qualified", "CV requires manual review due to mixed signals."
    
    def _create_default_analysis(
        self,
        application_id: UUID,
        cv_id: UUID,
        error_message: str
    ) -> CVDetailedScreeningCreate:
        """Create default analysis on error"""
        return CVDetailedScreeningCreate(
            application_id=application_id,
            cv_id=cv_id,
            overall_score=Decimal("50"),
            format_score=Decimal("50"),
            structure_score=Decimal("50"),
            experience_score=Decimal("50"),
            education_score=Decimal("50"),
            skills_score=Decimal("50"),
            language_score=Decimal("50"),
            ats_score=Decimal("50"),
            impact_score=Decimal("50"),
            job_match_score=Decimal("50"),
            top_strengths=[],
            critical_issues=[f"Analysis error: {error_message}"],
            improvement_suggestions=["Manual review recommended"],
            recommendation="maybe_qualified",
            recommendation_reason="Automated analysis failed - manual review required"
        )
    
    async def save_analysis(
        self,
        analysis: CVDetailedScreeningCreate
    ) -> Dict[str, Any]:
        """Save detailed analysis to database"""
        try:
            # Convert to dict for database
            data = {
                "id": str(uuid4()),
                "application_id": str(analysis.application_id),
                "cv_id": str(analysis.cv_id),
                "overall_score": float(analysis.overall_score),
                "format_score": float(analysis.format_score),
                "structure_score": float(analysis.structure_score),
                "experience_score": float(analysis.experience_score),
                "education_score": float(analysis.education_score),
                "skills_score": float(analysis.skills_score),
                "language_score": float(analysis.language_score),
                "ats_score": float(analysis.ats_score),
                "impact_score": float(analysis.impact_score),
                "job_match_score": float(analysis.job_match_score),
                "format_analysis": analysis.format_analysis.model_dump(mode='json') if analysis.format_analysis else {},
                "structure_analysis": analysis.structure_analysis.model_dump(mode='json') if analysis.structure_analysis else {},
                "experience_analysis": analysis.experience_analysis.model_dump(mode='json') if analysis.experience_analysis else {},
                "education_analysis": analysis.education_analysis.model_dump(mode='json') if analysis.education_analysis else {},
                "skills_analysis": analysis.skills_analysis.model_dump(mode='json') if analysis.skills_analysis else {},
                "language_analysis": analysis.language_analysis.model_dump(mode='json') if analysis.language_analysis else {},
                "ats_analysis": analysis.ats_analysis.model_dump(mode='json') if analysis.ats_analysis else {},
                "impact_analysis": analysis.impact_analysis.model_dump(mode='json') if analysis.impact_analysis else {},
                "top_strengths": analysis.top_strengths,
                "critical_issues": analysis.critical_issues,
                "improvement_suggestions": analysis.improvement_suggestions,
                "recommendation": analysis.recommendation,
                "recommendation_reason": analysis.recommendation_reason,
                "analysis_version": analysis.analysis_version,
            }
            
            # Check if analysis exists
            existing = db.service_client.table("cv_detailed_screening").select("id").eq(
                "application_id", str(analysis.application_id)
            ).execute()
            
            if existing.data:
                # Update existing
                del data["id"]
                response = db.service_client.table("cv_detailed_screening").update(
                    data
                ).eq("application_id", str(analysis.application_id)).execute()
            else:
                # Insert new
                response = db.service_client.table("cv_detailed_screening").insert(data).execute()
            
            logger.info("Detailed CV analysis saved", application_id=str(analysis.application_id))
            
            # Automatically create interview ticket after screening is complete
            # Only create if this is a new analysis (not an update)
            if not existing.data:
                try:
                    await self._create_ticket_after_screening(analysis.application_id)
                except Exception as ticket_error:
                    # Log but don't fail the analysis save if ticket creation fails
                    logger.warning(
                        "Failed to create ticket after screening",
                        application_id=str(analysis.application_id),
                        error=str(ticket_error)
                    )
            
            return response.data[0] if response.data else data
            
        except Exception as e:
            logger.error("Error saving detailed analysis", error=str(e), exc_info=True)
            raise
    
    async def _create_ticket_after_screening(self, application_id: UUID):
        """Create an interview ticket automatically after CV screening is complete"""
        try:
            # Get application details to find candidate_id and job_description_id
            app_response = db.service_client.table("job_applications").select(
                "candidate_id, job_description_id, job_descriptions!inner(recruiter_id)"
            ).eq("id", str(application_id)).execute()
            
            if not app_response.data:
                logger.warning("Application not found for ticket creation", application_id=str(application_id))
                return
            
            app = app_response.data[0]
            candidate_id = app.get("candidate_id")
            job_description_id = app.get("job_description_id")
            recruiter_id = app.get("job_descriptions", {}).get("recruiter_id")
            
            if not all([candidate_id, job_description_id, recruiter_id]):
                logger.warning(
                    "Missing required data for ticket creation",
                    application_id=str(application_id),
                    has_candidate=bool(candidate_id),
                    has_job=bool(job_description_id),
                    has_recruiter=bool(recruiter_id)
                )
                return
            
            # Check if ticket already exists for this candidate and job
            existing_ticket = db.service_client.table("interview_tickets").select("id").eq(
                "candidate_id", str(candidate_id)
            ).eq("job_description_id", str(job_description_id)).eq("is_used", False).execute()
            
            if existing_ticket.data:
                logger.info(
                    "Ticket already exists for this application",
                    application_id=str(application_id),
                    ticket_id=existing_ticket.data[0]["id"]
                )
                return
            
            # Create new ticket using TicketService
            from app.services.ticket_service import TicketService
            ticket = await TicketService.create_ticket(
                candidate_id=UUID(candidate_id),
                job_description_id=UUID(job_description_id),
                created_by=UUID(recruiter_id),
                expires_in_hours=None  # No expiration by default
            )
            
            logger.info(
                "Ticket created automatically after screening",
                application_id=str(application_id),
                ticket_id=ticket["id"],
                ticket_code=ticket["ticket_code"]
            )
            
        except Exception as e:
            logger.error(
                "Error creating ticket after screening",
                application_id=str(application_id),
                error=str(e),
                exc_info=True
            )
            raise

