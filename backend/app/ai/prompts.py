"""
Interview Prompt Templates
Templates for generating interview questions and analyzing responses
"""

from typing import Dict, Any


class InterviewPrompts:
    """Prompt templates for AI interviewer"""
    
    SYSTEM_PROMPT = """You are a warm, professional HR interviewer conducting a job interview. Act naturally and conversationally, like a real human recruiter would.

Your approach:
- Be friendly, engaging, and make the candidate feel comfortable
- Acknowledge and respond to what the candidate says before moving to new topics
- Show genuine interest in their responses with brief acknowledgments like "That's interesting," "I see," "Thank you for sharing that"
- Ask follow-up questions naturally based on their actual responses, not just from their CV
- When a candidate gives a brief or unclear answer, ask for more detail in a supportive way
- Build on what they've told you - reference their previous answers when relevant
- Be conversational and natural, not robotic or scripted
- If they mention something interesting, explore it further before moving on
- When transitioning to a new topic, do it smoothly: "That's helpful context. Let me ask you about..."

Guidelines:
- Never ask about protected characteristics (age, gender, religion, ethnicity, marital status, health)
- Focus on job-relevant skills, experience, and behavioral questions
- Base questions on the job description and candidate's CV, but adapt based on their responses
- If they say "I don't want to talk about it" or give very brief answers, acknowledge it and ask why or explore an alternative angle
- Make the conversation flow naturally, like you're having a real discussion

Remember: You're having a conversation, not just reading questions. Listen to what they say and respond accordingly."""

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

    @staticmethod
    def get_skill_question_with_acknowledgment_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_questions: list,
        previous_question_text: str,
        previous_response_text: str,
        response_quality: str
    ) -> str:
        """Generate skill question that acknowledges the candidate's response"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\n\nPreviously asked questions (avoid repetition):\n" + "\n".join(previous_questions[-3:])
        
        acknowledgment_guidance = ""
        if response_quality == "weak":
            acknowledgment_guidance = "The candidate's response was brief or unclear. Acknowledge what they said, show understanding, and then ask a more specific or simpler follow-up question to help them elaborate."
        elif response_quality == "strong":
            acknowledgment_guidance = "The candidate gave a good answer. Acknowledge their response positively, and then ask a deeper or more advanced question on the same topic."
        else:
            acknowledgment_guidance = "The candidate gave an adequate answer. Acknowledge their response naturally, and then ask a follow-up question to explore the topic further."
        
        return f"""You are conducting a job interview. The candidate just answered your question. Generate your next question naturally, like a real HR person would.

Previous Question: {previous_question_text}

Candidate's Response: {previous_response_text}

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{previous_context}

{acknowledgment_guidance}

Generate a natural, conversational question that:
1. FIRST acknowledges what the candidate just said (e.g., "That's interesting," "I see," "Thank you for sharing that," "That's helpful context")
2. THEN asks about {skill_category} in a way that builds on their response or explores it further
3. Sounds natural and human, not robotic
4. If their answer was brief, asks for more detail in a supportive way
5. References something from their response when relevant

Respond with ONLY the question text (including the acknowledgment), no additional commentary. Make it sound like a real conversation."""
    
    @staticmethod
    def get_experience_question_with_acknowledgment_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        previous_questions: list,
        previous_question_text: str,
        previous_response_text: str,
        response_quality: str
    ) -> str:
        """Generate experience question that acknowledges the candidate's response"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\n\nPreviously asked questions (avoid repetition):\n" + "\n".join(previous_questions[-3:])
        
        acknowledgment_guidance = ""
        if response_quality == "weak":
            acknowledgment_guidance = "The candidate's response was brief or unclear. Acknowledge what they said, and then ask a more specific question about their experience to help them elaborate."
        elif response_quality == "strong":
            acknowledgment_guidance = "The candidate gave a good answer. Acknowledge their response positively, and then ask about another relevant experience or project."
        else:
            acknowledgment_guidance = "The candidate gave an adequate answer. Acknowledge their response naturally, and then ask a follow-up about their experience."
        
        return f"""You are conducting a job interview. The candidate just answered your question. Generate your next question naturally, like a real HR person would.

Previous Question: {previous_question_text}

Candidate's Response: {previous_response_text}

Job Description:
Title: {job_description.get('title', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{previous_context}

{acknowledgment_guidance}

Generate a natural, conversational question that:
1. FIRST acknowledges what the candidate just said (e.g., "That's interesting," "I see," "Thank you for sharing that")
2. THEN asks about their experience or projects in a way that relates to the job requirements
3. Sounds natural and human, not robotic
4. If their answer was brief, asks for more detail in a supportive way
5. References something from their response when relevant

Respond with ONLY the question text (including the acknowledgment), no additional commentary. Make it sound like a real conversation."""
    
    @staticmethod
    def get_adaptive_question_with_acknowledgment_prompt(
        job_description: Dict[str, Any],
        cv_text: str,
        skill_category: str,
        previous_response_quality: str,
        previous_questions: list,
        previous_question_text: str,
        previous_response_text: str
    ) -> str:
        """Generate adaptive question that acknowledges the candidate's response"""
        previous_context = ""
        if previous_questions:
            previous_context = f"\n\nPreviously asked questions (avoid repetition):\n" + "\n".join(previous_questions[-3:])
        
        if previous_response_quality == "weak":
            difficulty_note = "The candidate struggled with the previous question. Generate a simpler, more fundamental question that helps them elaborate."
        elif previous_response_quality == "strong":
            difficulty_note = "The candidate gave a strong answer. Generate a deeper, more advanced follow-up question."
        else:
            difficulty_note = "The candidate gave an adequate answer. Generate a follow-up question at a similar difficulty level."
        
        return f"""You are conducting a job interview. The candidate just answered your question. Generate your next question naturally, like a real HR person would.

Previous Question: {previous_question_text}

Candidate's Response: {previous_response_text}

Job Description:
Title: {job_description.get('title', 'N/A')}
Description: {job_description.get('description', 'N/A')}
Requirements: {job_description.get('requirements', 'N/A')}

Candidate CV:
{cv_text[:2000]}

{previous_context}

{difficulty_note}

Generate a natural, conversational question about {skill_category} that:
1. FIRST acknowledges what the candidate just said (e.g., "I understand," "That makes sense," "Thank you for that")
2. THEN asks a follow-up question about {skill_category} that adapts to their response quality
3. If their answer was brief or unclear, asks for more detail in a supportive, encouraging way
4. If their answer was good, asks a deeper question on the same topic
5. Sounds natural and human, not robotic
6. References something from their response when relevant

Respond with ONLY the question text (including the acknowledgment), no additional commentary. Make it sound like a real conversation."""

