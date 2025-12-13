"""
Database Models
Export all Pydantic models
"""

from .user import User, UserCreate, UserUpdate
from .candidate import Candidate, CandidateCreate, CandidateUpdate
from .job_description import JobDescription, JobDescriptionCreate, JobDescriptionUpdate
from .cv import CV, CVCreate, CVUpdate
from .interview_ticket import InterviewTicket, InterviewTicketCreate, InterviewTicketUpdate
from .interview import Interview, InterviewCreate, InterviewUpdate
from .interview_question import InterviewQuestion, InterviewQuestionCreate, InterviewQuestionUpdate
from .interview_response import InterviewResponse, InterviewResponseCreate, InterviewResponseUpdate
from .interview_report import InterviewReport, InterviewReportCreate, InterviewReportUpdate
from .job_application import JobApplication, JobApplicationCreate, JobApplicationUpdate
from .cv_screening import CVScreeningResult, CVScreeningResultCreate

__all__ = [
    # User
    "User",
    "UserCreate",
    "UserUpdate",
    # Candidate
    "Candidate",
    "CandidateCreate",
    "CandidateUpdate",
    # Job Description
    "JobDescription",
    "JobDescriptionCreate",
    "JobDescriptionUpdate",
    # CV
    "CV",
    "CVCreate",
    "CVUpdate",
    # Interview Ticket
    "InterviewTicket",
    "InterviewTicketCreate",
    "InterviewTicketUpdate",
    # Interview
    "Interview",
    "InterviewCreate",
    "InterviewUpdate",
    # Interview Question
    "InterviewQuestion",
    "InterviewQuestionCreate",
    "InterviewQuestionUpdate",
    # Interview Response
    "InterviewResponse",
    "InterviewResponseCreate",
    "InterviewResponseUpdate",
    # Interview Report
    "InterviewReport",
    "InterviewReportCreate",
    "InterviewReportUpdate",
    # Job Application
    "JobApplication",
    "JobApplicationCreate",
    "JobApplicationUpdate",
    # CV Screening
    "CVScreeningResult",
    "CVScreeningResultCreate",
]
