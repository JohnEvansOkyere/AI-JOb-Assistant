"""
Follow-Up Email Service
Handles automatic follow-up emails for candidates who haven't heard back
after 14 days (reassurance) and 30 days (auto-rejection)
"""

from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from app.database import db
from app.services.email_service import EmailService
from app.config import settings
import structlog

logger = structlog.get_logger()


class FollowupEmailService:
    """Service for sending automatic follow-up emails to candidates"""

    @staticmethod
    async def find_14day_candidates() -> List[Dict[str, Any]]:
        """
        Find candidates who applied 14-16 days ago and qualify for reassurance email
        
        Returns:
            List of application dictionaries with candidate and job details
        """
        try:
            # Calculate date range (using configured days, with 2-day buffer to avoid duplicates)
            now = datetime.utcnow()
            days = settings.followup_reassurance_days
            from_date = now - timedelta(days=days + 2)
            to_date = now - timedelta(days=days)
            
            logger.info(
                "Finding 14-day candidates",
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat()
            )
            
            # Get applications in date range with active jobs
            applications_response = db.service_client.table("job_applications").select(
                "id, candidate_id, job_description_id, applied_at, status"
            ).gte("applied_at", from_date.isoformat()).lte("applied_at", to_date.isoformat()).execute()
            
            if not applications_response.data:
                logger.info("No applications found in 14-day range")
                return []
            
            applications = applications_response.data
            
            # Get job details and filter for active jobs
            job_ids = [app["job_description_id"] for app in applications]
            jobs_response = db.service_client.table("job_descriptions").select(
                "id, recruiter_id, hiring_status, title"
            ).in_("id", job_ids).eq("hiring_status", "active").execute()
            
            active_job_ids = {job["id"] for job in (jobs_response.data or [])}
            jobs_dict = {job["id"]: job for job in (jobs_response.data or [])}
            
            # Filter applications for active jobs and pending/screening status
            qualified_applications = [
                app for app in applications
                if app["job_description_id"] in active_job_ids
                and app["status"] in ("pending", "screening")
            ]
            
            if not qualified_applications:
                logger.info("No qualified applications after filtering for active jobs")
                return []
            
            # Get candidate IDs
            candidate_ids = [app["candidate_id"] for app in qualified_applications]
            
            # Check for completed interviews
            interviews_response = db.service_client.table("interviews").select(
                "candidate_id"
            ).in_("candidate_id", candidate_ids).eq("status", "completed").execute()
            
            candidates_with_interviews = {
                interview["candidate_id"] 
                for interview in (interviews_response.data or [])
            }
            
            # Check for already sent emails (rejection, reassurance, acceptance)
            # We need to join with email_templates to check template_type
            sent_emails_response = db.service_client.table("sent_emails").select(
                "candidate_id, template_id, application_id"
            ).in_("candidate_id", candidate_ids).execute()
            
            # Get template IDs to check their types
            template_ids = [
                email.get("template_id") 
                for email in (sent_emails_response.data or [])
                if email.get("template_id")
            ]
            
            excluded_template_types = {
                "reassurance_14day",
                "cv_rejection",
                "interview_rejection",
                "auto_timeout_rejection",
                "acceptance"
            }
            
            if template_ids:
                templates_response = db.service_client.table("email_templates").select(
                    "id, template_type"
                ).in_("id", template_ids).in_("template_type", list(excluded_template_types)).execute()
                
                excluded_template_ids = {
                    template["id"] 
                    for template in (templates_response.data or [])
                }
                
                # Find candidates who received excluded email types
                candidates_with_excluded_emails = {
                    email["candidate_id"]
                    for email in (sent_emails_response.data or [])
                    if email.get("template_id") in excluded_template_ids
                    and email.get("application_id") in [app["id"] for app in qualified_applications]
                }
            else:
                candidates_with_excluded_emails = set()
            
            # Filter out candidates with interviews or excluded emails
            final_applications = []
            for app in qualified_applications:
                if app["candidate_id"] not in candidates_with_interviews:
                    if app["candidate_id"] not in candidates_with_excluded_emails:
                        final_applications.append(app)
            
            # Get candidate details
            candidates_response = db.service_client.table("candidates").select(
                "id, email, full_name"
            ).in_("id", [app["candidate_id"] for app in final_applications]).execute()
            
            candidates_dict = {
                candidate["id"]: candidate 
                for candidate in (candidates_response.data or [])
            }
            
            # Build result with all needed data
            result = []
            for app in final_applications:
                candidate = candidates_dict.get(app["candidate_id"])
                job = jobs_dict.get(app["job_description_id"])
                
                if candidate and job:
                    result.append({
                        "application": app,
                        "candidate": candidate,
                        "job": job
                    })
            
            logger.info(
                "Found 14-day candidates",
                total_applications=len(applications),
                qualified=len(result)
            )
            
            return result
            
        except Exception as e:
            logger.error("Error finding 14-day candidates", error=str(e), exc_info=True)
            return []

    @staticmethod
    async def find_30day_candidates() -> List[Dict[str, Any]]:
        """
        Find candidates who applied 30-32 days ago and qualify for auto-rejection email
        
        Returns:
            List of application dictionaries with candidate and job details
        """
        try:
            # Calculate date range (using configured days, with 2-day buffer to avoid duplicates)
            now = datetime.utcnow()
            days = settings.followup_rejection_days
            from_date = now - timedelta(days=days + 2)
            to_date = now - timedelta(days=days)
            
            logger.info(
                "Finding 30-day candidates",
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat()
            )
            
            # Get applications in date range with active jobs
            applications_response = db.service_client.table("job_applications").select(
                "id, candidate_id, job_description_id, applied_at, status"
            ).gte("applied_at", from_date.isoformat()).lte("applied_at", to_date.isoformat()).execute()
            
            if not applications_response.data:
                logger.info("No applications found in 30-day range")
                return []
            
            applications = applications_response.data
            
            # Get job details and filter for active jobs
            job_ids = [app["job_description_id"] for app in applications]
            jobs_response = db.service_client.table("job_descriptions").select(
                "id, recruiter_id, hiring_status, title"
            ).in_("id", job_ids).eq("hiring_status", "active").execute()
            
            active_job_ids = {job["id"] for job in (jobs_response.data or [])}
            jobs_dict = {job["id"]: job for job in (jobs_response.data or [])}
            
            # Filter applications for active jobs and pending/screening status
            qualified_applications = [
                app for app in applications
                if app["job_description_id"] in active_job_ids
                and app["status"] in ("pending", "screening")
            ]
            
            if not qualified_applications:
                logger.info("No qualified applications after filtering for active jobs")
                return []
            
            # Get candidate IDs
            candidate_ids = [app["candidate_id"] for app in qualified_applications]
            
            # Check for completed interviews
            interviews_response = db.service_client.table("interviews").select(
                "candidate_id"
            ).in_("candidate_id", candidate_ids).eq("status", "completed").execute()
            
            candidates_with_interviews = {
                interview["candidate_id"] 
                for interview in (interviews_response.data or [])
            }
            
            # Check for already sent emails (rejection, acceptance - but allow reassurance_14day)
            sent_emails_response = db.service_client.table("sent_emails").select(
                "candidate_id, template_id, application_id"
            ).in_("candidate_id", candidate_ids).execute()
            
            # Get template IDs to check their types
            template_ids = [
                email.get("template_id") 
                for email in (sent_emails_response.data or [])
                if email.get("template_id")
            ]
            
            # For 30-day, exclude rejection/acceptance but allow reassurance_14day
            excluded_template_types = {
                "cv_rejection",
                "interview_rejection",
                "auto_timeout_rejection",
                "acceptance"
            }
            
            if template_ids:
                templates_response = db.service_client.table("email_templates").select(
                    "id, template_type"
                ).in_("id", template_ids).in_("template_type", list(excluded_template_types)).execute()
                
                excluded_template_ids = {
                    template["id"] 
                    for template in (templates_response.data or [])
                }
                
                # Find candidates who received excluded email types
                candidates_with_excluded_emails = {
                    email["candidate_id"]
                    for email in (sent_emails_response.data or [])
                    if email.get("template_id") in excluded_template_ids
                    and email.get("application_id") in [app["id"] for app in qualified_applications]
                }
            else:
                candidates_with_excluded_emails = set()
            
            # Filter out candidates with interviews or excluded emails
            final_applications = []
            for app in qualified_applications:
                if app["candidate_id"] not in candidates_with_interviews:
                    if app["candidate_id"] not in candidates_with_excluded_emails:
                        final_applications.append(app)
            
            # Get candidate details
            candidates_response = db.service_client.table("candidates").select(
                "id, email, full_name"
            ).in_("id", [app["candidate_id"] for app in final_applications]).execute()
            
            candidates_dict = {
                candidate["id"]: candidate 
                for candidate in (candidates_response.data or [])
            }
            
            # Build result with all needed data
            result = []
            for app in final_applications:
                candidate = candidates_dict.get(app["candidate_id"])
                job = jobs_dict.get(app["job_description_id"])
                
                if candidate and job:
                    result.append({
                        "application": app,
                        "candidate": candidate,
                        "job": job
                    })
            
            logger.info(
                "Found 30-day candidates",
                total_applications=len(applications),
                qualified=len(result)
            )
            
            return result
            
        except Exception as e:
            logger.error("Error finding 30-day candidates", error=str(e), exc_info=True)
            return []

    @staticmethod
    async def send_14day_reassurance(data: Dict[str, Any]) -> bool:
        """
        Send 14-day reassurance email to a candidate
        
        Args:
            data: Dictionary with 'application', 'candidate', and 'job' keys
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            application = data["application"]
            candidate = data["candidate"]
            job = data["job"]
            recruiter_id = UUID(job["recruiter_id"])
            application_id = UUID(application["id"])
            candidate_id = UUID(candidate["id"])
            job_id = UUID(job["id"])
            
            # Get or create template
            template = await EmailService.get_email_template(
                recruiter_id,
                "reassurance_14day"
            )
            
            if not template:
                logger.warning(
                    "No reassurance_14day template found, skipping",
                    recruiter_id=str(recruiter_id),
                    application_id=str(application_id)
                )
                return False
            
            # Get branding
            branding = await EmailService.get_company_branding(recruiter_id)
            company_name = branding.get("company_name", "Our Company") if branding else "Our Company"
            primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
            
            # Prepare variables
            template_variables = {
                "candidate_name": candidate.get("full_name", "Candidate"),
                "job_title": job.get("title", "the position"),
                "company_name": company_name,
                "primary_color": primary_color
            }
            
            # Render template
            subject = EmailService.render_template(template["subject"], template_variables)
            body_html = EmailService.render_template(template["body_html"], template_variables)
            body_text = EmailService.render_template(template.get("body_text", ""), template_variables) if template.get("body_text") else None
            
            # Send email
            await EmailService.send_email(
                recruiter_id=recruiter_id,
                recipient_email=candidate["email"],
                recipient_name=candidate.get("full_name", "Candidate"),
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                template_id=UUID(template["id"]),
                application_id=application_id,
                candidate_id=candidate_id,
                job_description_id=job_id
            )
            
            logger.info(
                "14-day reassurance email sent",
                application_id=str(application_id),
                candidate_email=candidate["email"]
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send 14-day reassurance email",
                application_id=str(application.get("id", "unknown")),
                error=str(e),
                exc_info=True
            )
            return False

    @staticmethod
    async def send_30day_rejection(data: Dict[str, Any]) -> bool:
        """
        Send 30-day auto-rejection email to a candidate
        
        Args:
            data: Dictionary with 'application', 'candidate', and 'job' keys
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            application = data["application"]
            candidate = data["candidate"]
            job = data["job"]
            recruiter_id = UUID(job["recruiter_id"])
            application_id = UUID(application["id"])
            candidate_id = UUID(candidate["id"])
            job_id = UUID(job["id"])
            
            # Get or create template
            template = await EmailService.get_email_template(
                recruiter_id,
                "auto_timeout_rejection"
            )
            
            if not template:
                logger.warning(
                    "No auto_timeout_rejection template found, skipping",
                    recruiter_id=str(recruiter_id),
                    application_id=str(application_id)
                )
                return False
            
            # Get branding
            branding = await EmailService.get_company_branding(recruiter_id)
            company_name = branding.get("company_name", "Our Company") if branding else "Our Company"
            primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
            
            # Prepare variables
            template_variables = {
                "candidate_name": candidate.get("full_name", "Candidate"),
                "job_title": job.get("title", "the position"),
                "company_name": company_name,
                "primary_color": primary_color
            }
            
            # Render template
            subject = EmailService.render_template(template["subject"], template_variables)
            body_html = EmailService.render_template(template["body_html"], template_variables)
            body_text = EmailService.render_template(template.get("body_text", ""), template_variables) if template.get("body_text") else None
            
            # Send email
            await EmailService.send_email(
                recruiter_id=recruiter_id,
                recipient_email=candidate["email"],
                recipient_name=candidate.get("full_name", "Candidate"),
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                template_id=UUID(template["id"]),
                application_id=application_id,
                candidate_id=candidate_id,
                job_description_id=job_id
            )
            
            logger.info(
                "30-day auto-rejection email sent",
                application_id=str(application_id),
                candidate_email=candidate["email"]
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send 30-day rejection email",
                application_id=str(application.get("id", "unknown")),
                error=str(e),
                exc_info=True
            )
            return False

    @staticmethod
    async def process_daily_followups():
        """
        Main function to process all follow-up emails for the day
        Called by scheduler daily at configured time (default: 9 AM)
        """
        if not settings.followup_emails_enabled:
            logger.info("Follow-up emails are disabled, skipping")
            return
        
        start_time = datetime.utcnow()
        logger.info("Starting daily follow-up email check")
        
        # Process 14-day reassurance emails
        candidates_14day = await FollowupEmailService.find_14day_candidates()
        
        sent_14day = 0
        failed_14day = 0
        
        for data in candidates_14day:
            try:
                success = await FollowupEmailService.send_14day_reassurance(data)
                if success:
                    sent_14day += 1
                else:
                    failed_14day += 1
            except Exception as e:
                failed_14day += 1
                logger.error(
                    "Error sending 14-day email",
                    application_id=str(data.get("application", {}).get("id", "unknown")),
                    error=str(e)
                )
        
        # Process 30-day auto-rejection emails
        candidates_30day = await FollowupEmailService.find_30day_candidates()
        
        sent_30day = 0
        failed_30day = 0
        
        for data in candidates_30day:
            try:
                success = await FollowupEmailService.send_30day_rejection(data)
                if success:
                    sent_30day += 1
                else:
                    failed_30day += 1
            except Exception as e:
                failed_30day += 1
                logger.error(
                    "Error sending 30-day email",
                    application_id=str(data.get("application", {}).get("id", "unknown")),
                    error=str(e)
                )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(
            "Daily follow-up emails completed",
            sent_14day=sent_14day,
            failed_14day=failed_14day,
            total_14day=len(candidates_14day),
            sent_30day=sent_30day,
            failed_30day=failed_30day,
            total_30day=len(candidates_30day),
            execution_time_seconds=execution_time
        )
    
