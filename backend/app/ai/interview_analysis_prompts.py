"""
Interview Analysis Prompts
Comprehensive prompts for deep interview analysis including soft skills,
technical assessment, sentiment analysis, and behavioral evaluation.
"""

from typing import Dict, Any, List


class InterviewAnalysisPrompts:
    """Prompts for comprehensive interview analysis"""

    COMPREHENSIVE_ANALYSIS_SYSTEM_PROMPT = """You are an expert interview analyst with deep expertise in:
- Human resources and talent acquisition
- Behavioral psychology and assessment
- Technical skill evaluation
- Communication analysis
- Sentiment and emotional intelligence assessment

Your role is to provide comprehensive, objective, and actionable analysis of interview responses.
Always support your assessments with specific evidence from the responses.
Be fair, unbiased, and focus on job-relevant competencies.
"""

    @staticmethod
    def get_comprehensive_analysis_prompt(
        interview_data: Dict[str, Any],
        job_description: Dict[str, Any],
        cv_text: str,
        questions_and_responses: List[Dict[str, str]]
    ) -> str:
        """
        Generate prompt for comprehensive interview analysis.
        
        Args:
            interview_data: Interview metadata
            job_description: Job requirements and description
            cv_text: Candidate's CV text
            questions_and_responses: List of Q&A pairs
        
        Returns:
            Comprehensive analysis prompt
        """
        qa_text = ""
        for i, qa in enumerate(questions_and_responses, 1):
            qa_text += f"""
--- Question {i} ---
Q: {qa.get('question', 'N/A')}
A: {qa.get('response', 'No response')}
"""

        job_title = job_description.get('title', 'Unknown Position')
        job_requirements = job_description.get('requirements', '')
        job_responsibilities = job_description.get('responsibilities', '')
        required_skills = job_description.get('required_skills', [])
        
        if isinstance(required_skills, list):
            required_skills = ', '.join(required_skills)

        return f"""Analyze this complete interview transcript and provide a comprehensive assessment.

## JOB DETAILS
**Position:** {job_title}
**Requirements:** {job_requirements}
**Responsibilities:** {job_responsibilities}
**Required Skills:** {required_skills}

## CANDIDATE CV SUMMARY
{cv_text[:2000]}

## INTERVIEW TRANSCRIPT
{qa_text}

## ANALYSIS REQUIRED

Provide a detailed analysis in the following JSON format. Be thorough and evidence-based:

```json
{{
    "overall_assessment": {{
        "overall_score": <0-100>,
        "technical_score": <0-100>,
        "soft_skills_score": <0-100>,
        "communication_score": <0-100>,
        "summary": "<2-3 sentence overall summary>"
    }},
    
    "soft_skills": {{
        "leadership": {{
            "score": <0-100>,
            "evidence": ["<specific examples from responses>"],
            "notes": "<assessment notes>"
        }},
        "teamwork": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "problem_solving": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "adaptability": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "creativity": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "emotional_intelligence": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "time_management": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }},
        "conflict_resolution": {{
            "score": <0-100>,
            "evidence": ["<specific examples>"],
            "notes": "<assessment notes>"
        }}
    }},
    
    "communication": {{
        "clarity": {{
            "score": <0-100>,
            "evidence": ["<examples of clear/unclear communication>"],
            "notes": "<assessment>"
        }},
        "articulation": {{
            "score": <0-100>,
            "evidence": ["<examples>"],
            "notes": "<how well they express ideas>"
        }},
        "confidence": {{
            "score": <0-100>,
            "evidence": ["<indicators of confidence level>"],
            "notes": "<assessment>"
        }},
        "listening": {{
            "score": <0-100>,
            "evidence": ["<how well they addressed the actual questions>"],
            "notes": "<assessment>"
        }},
        "persuasion": {{
            "score": <0-100>,
            "evidence": ["<ability to make compelling arguments>"],
            "notes": "<assessment>"
        }},
        "vocabulary_level": "<basic/professional/advanced>",
        "grammar_quality": "<poor/acceptable/good/excellent>",
        "response_structure": "<poor/adequate/well-structured>"
    }},
    
    "technical_assessment": {{
        "depth": {{
            "score": <0-100>,
            "evidence": ["<technical depth demonstrated>"],
            "notes": "<assessment>"
        }},
        "breadth": {{
            "score": <0-100>,
            "evidence": ["<range of technical knowledge>"],
            "notes": "<assessment>"
        }},
        "practical_application": {{
            "score": <0-100>,
            "evidence": ["<real-world application examples>"],
            "notes": "<assessment>"
        }},
        "industry_knowledge": {{
            "score": <0-100>,
            "evidence": ["<industry awareness demonstrated>"],
            "notes": "<assessment>"
        }},
        "skills_demonstrated": ["<list of skills shown>"],
        "skills_missing": ["<expected skills not demonstrated>"],
        "technical_red_flags": ["<any technical concerns>"]
    }},
    
    "sentiment_analysis": {{
        "overall_sentiment": "<positive/neutral/negative/mixed>",
        "sentiment_score": <0-100, where 50 is neutral>,
        "enthusiasm_level": "<high/moderate/low>",
        "stress_indicators": ["<any signs of stress or discomfort>"],
        "positive_indicators": ["<signs of positivity and engagement>"],
        "sentiment_progression": [
            {{"question": 1, "sentiment": "<pos/neu/neg>", "note": "<brief note>"}},
            ...
        ],
        "notable_emotional_moments": ["<significant emotional indicators>"]
    }},
    
    "behavioral_analysis": {{
        "honesty_indicators": ["<signs of honest, authentic responses>"],
        "consistency_score": <0-100>,
        "red_flag_behaviors": ["<concerning behaviors or responses>"],
        "evasive_responses": ["<any questions dodged or deflected>"],
        "positive_behaviors": ["<noteworthy positive behaviors>"],
        "star_responses": <number of STAR-formatted responses>,
        "uses_concrete_examples": <true/false>
    }},
    
    "question_by_question": [
        {{
            "question_number": 1,
            "question_text": "<question>",
            "quality": "<strong/adequate/weak>",
            "relevance_score": <0-100>,
            "depth_score": <0-100>,
            "key_points": ["<main points from response>"],
            "missed_opportunities": ["<what they could have mentioned>"],
            "sentiment": "<positive/neutral/negative>",
            "confidence_level": "<high/moderate/low>",
            "notable_quote": "<most significant quote if any>",
            "follow_up_needed": <true/false>,
            "follow_up_reason": "<why follow-up would be valuable>"
        }},
        ...
    ],
    
    "culture_fit": {{
        "score": <0-100>,
        "notes": "<assessment of how they'd fit the company culture>",
        "positive_indicators": ["<cultural fit positives>"],
        "potential_concerns": ["<cultural fit concerns>"]
    }},
    
    "role_fit": {{
        "score": <0-100>,
        "analysis": "<detailed role fit assessment>",
        "matching_qualifications": ["<qualifications that match the role>"],
        "gaps": ["<areas where they fall short for the role>"]
    }},
    
    "summary": {{
        "key_strengths": ["<top 5 strengths>"],
        "areas_for_improvement": ["<top 5 areas to improve>"],
        "notable_quotes": ["<3-5 memorable quotes from the interview>"],
        "follow_up_topics": ["<topics worth exploring in future interviews>"]
    }},
    
    "recommendation": {{
        "decision": "<strong_hire/hire/maybe/no_hire>",
        "confidence": <0-100>,
        "summary": "<one paragraph recommendation summary>",
        "detailed": "<detailed recommendation with reasoning>"
    }}
}}
```

Provide your analysis now. Be objective, thorough, and base all assessments on evidence from the transcript."""

    @staticmethod
    def get_single_response_analysis_prompt(
        question: str,
        response: str,
        job_description: Dict[str, Any],
        response_number: int,
        total_responses: int
    ) -> str:
        """
        Generate prompt for analyzing a single response during the interview.
        
        Args:
            question: The interview question
            response: Candidate's response
            job_description: Job details
            response_number: Which response this is
            total_responses: Expected total responses
        
        Returns:
            Single response analysis prompt
        """
        job_title = job_description.get('title', 'Unknown Position')
        
        return f"""Analyze this interview response (Response {response_number} of {total_responses}).

**Position:** {job_title}

**Question:** {question}

**Response:** {response}

Provide a quick assessment in JSON format:

```json
{{
    "quality": "<strong/adequate/weak>",
    "relevance_score": <0-100>,
    "alignment_score": <0-100>,
    "key_points": ["<main points covered>"],
    "strengths": ["<response strengths>"],
    "weaknesses": ["<response weaknesses>"],
    "red_flags": ["<any concerns>"],
    "sentiment": "<positive/neutral/negative>",
    "confidence_level": "<high/moderate/low>",
    "technical_accuracy": <0-100 if technical question, null otherwise>,
    "follow_up_suggestions": ["<potential follow-up questions>"],
    "notable_quote": "<most notable part of response or null>"
}}
```

Be concise but thorough."""

    @staticmethod
    def get_sentiment_analysis_prompt(responses: List[str]) -> str:
        """
        Generate prompt for sentiment analysis across all responses.
        
        Args:
            responses: List of candidate responses
        
        Returns:
            Sentiment analysis prompt
        """
        responses_text = "\n".join([f"Response {i+1}: {r}" for i, r in enumerate(responses)])
        
        return f"""Analyze the sentiment and emotional tone across these interview responses:

{responses_text}

Provide sentiment analysis in JSON format:

```json
{{
    "overall_sentiment": "<positive/neutral/negative/mixed>",
    "sentiment_score": <0-100, 50 is neutral>,
    "enthusiasm_level": "<high/moderate/low>",
    "confidence_trajectory": "<increasing/stable/decreasing>",
    "stress_indicators": ["<any stress signs>"],
    "positive_indicators": ["<positive emotional signs>"],
    "per_response_sentiment": [
        {{"response": 1, "sentiment": "<pos/neu/neg>", "score": <0-100>}},
        ...
    ],
    "emotional_summary": "<brief summary of emotional state throughout interview>"
}}
```"""

    @staticmethod
    def get_soft_skills_deep_dive_prompt(
        questions_and_responses: List[Dict[str, str]],
        job_description: Dict[str, Any]
    ) -> str:
        """
        Generate prompt for deep soft skills analysis.
        
        Args:
            questions_and_responses: Q&A pairs
            job_description: Job details
        
        Returns:
            Soft skills analysis prompt
        """
        qa_text = "\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['response']}"
            for i, qa in enumerate(questions_and_responses)
        ])
        
        required_skills = job_description.get('soft_skills', [])
        if isinstance(required_skills, list):
            required_skills = ', '.join(required_skills)
        
        return f"""Perform a deep analysis of soft skills demonstrated in this interview.

**Required Soft Skills for Role:** {required_skills}

**Interview Transcript:**
{qa_text}

Analyze each soft skill in detail. For each, provide:
1. Score (0-100)
2. Specific evidence from responses
3. Behavioral indicators
4. Comparison to role requirements

Output JSON format:

```json
{{
    "leadership": {{
        "score": <0-100>,
        "evidence": ["<specific quotes/examples>"],
        "behavioral_indicators": ["<observed leadership behaviors>"],
        "meets_role_requirements": <true/false>,
        "development_areas": ["<areas for growth>"]
    }},
    "teamwork": {{...}},
    "problem_solving": {{...}},
    "adaptability": {{...}},
    "creativity": {{...}},
    "emotional_intelligence": {{...}},
    "time_management": {{...}},
    "conflict_resolution": {{...}},
    "overall_soft_skills_score": <0-100>,
    "top_soft_skill": "<strongest soft skill>",
    "weakest_soft_skill": "<needs most development>",
    "soft_skills_summary": "<paragraph summary>"
}}
```"""

    @staticmethod
    def get_technical_deep_dive_prompt(
        questions_and_responses: List[Dict[str, str]],
        job_description: Dict[str, Any],
        cv_text: str
    ) -> str:
        """
        Generate prompt for deep technical analysis.
        
        Args:
            questions_and_responses: Q&A pairs
            job_description: Job details
            cv_text: Candidate's CV
        
        Returns:
            Technical analysis prompt
        """
        qa_text = "\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['response']}"
            for i, qa in enumerate(questions_and_responses)
        ])
        
        required_skills = job_description.get('required_skills', [])
        if isinstance(required_skills, list):
            required_skills = ', '.join(required_skills)
        
        return f"""Perform a deep technical skills analysis for this interview.

**Position:** {job_description.get('title', 'Unknown')}
**Required Technical Skills:** {required_skills}

**Candidate CV Summary:**
{cv_text[:1500]}

**Interview Transcript:**
{qa_text}

Analyze technical competency in detail:

```json
{{
    "technical_depth": {{
        "score": <0-100>,
        "evidence": ["<examples of deep technical knowledge>"],
        "areas_of_expertise": ["<demonstrated expert areas>"],
        "knowledge_gaps": ["<areas lacking depth>"]
    }},
    "technical_breadth": {{
        "score": <0-100>,
        "evidence": ["<range of technologies/concepts mentioned>"],
        "cross_functional_knowledge": ["<interdisciplinary knowledge shown>"]
    }},
    "practical_application": {{
        "score": <0-100>,
        "evidence": ["<real-world implementation examples>"],
        "project_examples": ["<specific projects mentioned>"],
        "hands_on_experience": "<assessment of practical experience>"
    }},
    "industry_knowledge": {{
        "score": <0-100>,
        "evidence": ["<industry awareness demonstrated>"],
        "current_trends_awareness": <true/false>,
        "competitive_landscape_understanding": <true/false>
    }},
    "skills_matrix": {{
        "demonstrated": ["<skills clearly shown>"],
        "claimed_not_demonstrated": ["<CV skills not shown in interview>"],
        "missing_required": ["<required skills not shown>"],
        "bonus_skills": ["<extra valuable skills>"]
    }},
    "technical_communication": {{
        "can_explain_complex_topics": <true/false>,
        "uses_appropriate_terminology": <true/false>,
        "avoids_buzzword_overuse": <true/false>
    }},
    "technical_red_flags": ["<any technical concerns>"],
    "overall_technical_score": <0-100>,
    "technical_summary": "<paragraph assessment of technical capability>"
}}
```"""

    @staticmethod
    def get_final_recommendation_prompt(
        analysis_summary: Dict[str, Any],
        job_description: Dict[str, Any]
    ) -> str:
        """
        Generate prompt for final hiring recommendation.
        
        Args:
            analysis_summary: Summary of all analyses
            job_description: Job details
        
        Returns:
            Recommendation prompt
        """
        return f"""Based on the following interview analysis, provide a final hiring recommendation.

**Position:** {job_description.get('title', 'Unknown')}
**Experience Level Required:** {job_description.get('experience_level', 'Not specified')}

**Analysis Summary:**
- Overall Score: {analysis_summary.get('overall_score', 'N/A')}
- Technical Score: {analysis_summary.get('technical_score', 'N/A')}
- Soft Skills Score: {analysis_summary.get('soft_skills_score', 'N/A')}
- Communication Score: {analysis_summary.get('communication_score', 'N/A')}
- Culture Fit Score: {analysis_summary.get('culture_fit_score', 'N/A')}
- Role Fit Score: {analysis_summary.get('role_fit_score', 'N/A')}

**Key Strengths:** {', '.join(analysis_summary.get('key_strengths', []))}
**Areas for Improvement:** {', '.join(analysis_summary.get('areas_for_improvement', []))}
**Red Flags:** {', '.join(analysis_summary.get('red_flags', []))}

Provide your final recommendation:

```json
{{
    "decision": "<strong_hire/hire/maybe/no_hire>",
    "confidence": <0-100>,
    "summary": "<one clear paragraph explaining the recommendation>",
    "detailed_reasoning": "<detailed multi-paragraph analysis supporting the decision>",
    "next_steps": ["<recommended next steps for this candidate>"],
    "interview_suggestions": ["<topics for follow-up interviews if applicable>"],
    "onboarding_considerations": ["<things to consider if hired>"]
}}
```

Be decisive and clear in your recommendation."""

