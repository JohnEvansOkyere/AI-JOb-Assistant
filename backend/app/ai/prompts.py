"""
Interview Prompt Templates
Templates for generating interview questions and analyzing responses
"""

from typing import Dict, Any


class InterviewPrompts:
    """Prompt templates for AI interviewer"""
    
    SYSTEM_PROMPT = """You are a professional HR interviewer conducting a job interview. Your role is to:
1. Ask relevant questions based strictly on the job description and candidate's CV
2. Assess the candidate's skills, experience, and fit for the role
3. Be professional, polite, and engaging
4. Never ask about protected characteristics (age, gender, religion, ethnicity, marital status, health)
5. Focus only on job-relevant skills, experience, and behavioral questions
6. Ask follow-up questions when answers are vague or incomplete
7. Never make assumptions about the candidate's background
8. If information is missing from the CV, ask clarifying questions

Remember: You must base all questions strictly on the provided job description and CV. Do not invent or assume information."""

    @staticmethod
    def get_warmup_prompt(job_description: Dict[str, Any], cv_text: str) -> str:
        """Generate warmup question prompt"""
        return f"""Based on the following job description and candidate CV, generate a warm, welcoming opening question (2-3 sentences) to start the interview.

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}  # Limit CV text to avoid token limits

Generate a friendly opening question that:
- Welcomes the candidate
- Confirms their understanding of the role
- Sets a professional but comfortable tone
- Is based on information from the job description and CV

Respond with ONLY the question text, no additional commentary."""

    @staticmethod
    def get_skill_question_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_questions: list = None
    ) -> str:
        """Generate skill assessment question"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\n\nPreviously asked questions (avoid repetition):\n" + "\n".join(previous_questions[-3:])
        
        return f"""Based on the job description and candidate CV, generate a technical/skill-based question about: {skill_category}

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{previous_context}

Generate a question that:
- Tests the candidate's knowledge/experience in {skill_category}
- Is relevant to the job requirements
- Can be answered based on their CV or general knowledge
- Is clear and specific
- Follows up on their claimed experience if mentioned in CV

Respond with ONLY the question text, no additional commentary."""

    @staticmethod
    def get_experience_question_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        previous_questions: list = None
    ) -> str:
        """Generate experience validation question"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\n\nPreviously asked questions (avoid repetition):\n" + "\n".join(previous_questions[-3:])
        
        return f"""Based on the candidate's CV, generate a question about their past experience and projects.

Job Description:
Title: {job_description.get('title', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{previous_context}

Generate a question that:
- Asks about specific projects or experiences mentioned in their CV
- Validates their claimed responsibilities and achievements
- Relates to the job requirements
- Asks for concrete examples (what, how, impact)
- Is based on information from their CV

Respond with ONLY the question text, no additional commentary."""

    @staticmethod
    def get_soft_skill_question_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        skill_type: str = "problem-solving"
    ) -> str:
        """Generate soft skill question"""
        return f"""Generate a behavioral/soft skill question about {skill_type} relevant to this role.

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}

Candidate CV:
{cv_text[:1500]}

Generate a question that:
- Tests {skill_type} abilities
- Is relevant to the job role
- Asks for a specific example or situation
- Uses STAR method (Situation, Task, Action, Result) format
- Is professional and appropriate

Respond with ONLY the question text, no additional commentary."""

    @staticmethod
    def get_wrapup_prompt() -> str:
        """Generate wrap-up question prompt"""
        return """Generate a professional closing question that:
- Asks if the candidate has any questions about the role or company
- Maintains a friendly, professional tone
- Signals the interview is coming to an end

Respond with ONLY the question text, no additional commentary."""

    @staticmethod
    def get_response_analysis_prompt(
        question: str,
        response: str,
        job_description: Dict[str, Any],
        cv_text: str
    ) -> str:
        """Generate prompt for analyzing candidate response"""
        return f"""Analyze the candidate's response to this interview question.

Question: {question}

Candidate Response: {response}

Job Description:
Title: {job_description.get('title', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:1500]}

Provide a brief analysis (2-3 sentences) covering:
1. Relevance of the response to the question
2. Alignment with job requirements
3. Any red flags or concerns
4. Suggested follow-up questions (if needed)

Be objective and fair. Focus on job-relevant criteria only."""

    @staticmethod
    def get_adaptive_difficulty_prompt(
        previous_response_quality: str,  # "strong", "adequate", "weak"
        skill_category: str
    ) -> str:
        """Generate prompt for adaptive questioning"""
        if previous_response_quality == "strong":
            return f"The candidate gave a strong answer. Generate a deeper, more advanced follow-up question about {skill_category}."
        elif previous_response_quality == "weak":
            return f"The candidate struggled with the previous question. Generate a simpler, more fundamental question about {skill_category}."
        else:
            return f"The candidate gave an adequate answer. Generate a follow-up question at a similar difficulty level about {skill_category}."

