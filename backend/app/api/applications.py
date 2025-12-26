"""
Job Applications API Routes
Public application submission and recruiter management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request, BackgroundTasks
from typing import Optional, List
from uuid import UUID
from app.schemas.common import Response
from app.models.job_application import JobApplication, JobApplicationCreate
from app.services.application_service import ApplicationService
from app.services.application_form_service import ApplicationFormService
from app.services.cv_screening_service import CVScreeningService
from app.services.cv_parser import CVParser
from app.services.email_service import EmailService
from app.models.application_form import ApplicationFormResponseCreate
from app.utils.auth import get_current_user_id
from app.utils.rate_limit import rate_limit_public
from app.utils.file_validation import validate_cv_file, sanitize_filename
from app.utils.input_validation import validate_email_address, validate_phone_number, sanitize_text_input
from app.config import settings
from app.database import db
import structlog
import aiofiles
import os
import tempfile

logger = structlog.get_logger()

router = APIRouter(prefix="/applications", tags=["applications"])


async def send_application_confirmation_email(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    job_id: UUID,
    recruiter_id: UUID,
    application_id: UUID
):
    """
    Send automated confirmation email to candidate after application submission
    Uses custom template from database if available, otherwise uses default template
    
    Args:
        candidate_email: Candidate's email address
        candidate_name: Candidate's full name
        job_title: Job position title
        job_id: Job description ID
        recruiter_id: Recruiter/company ID
        application_id: Application ID
    """
    try:
        # Get company branding for personalized email
        branding = await EmailService.get_company_branding(recruiter_id)
        company_name = branding.get("company_name", "Our Company") if branding else "Our Company"
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        # Get job details for more context
        try:
            job_response = db.service_client.table("job_descriptions").select("title").eq("id", str(job_id)).execute()
            if job_response.data:
                job_title = job_response.data[0].get("title", job_title)
        except Exception as e:
            logger.warning("Could not fetch job details for email", error=str(e))
        
        # Try to get custom template from database
        custom_template = await EmailService.get_email_template(recruiter_id, "application_received")
        
        if custom_template:
            # Use custom template from database
            template_html = custom_template.get("body_html", "")
            template_subject = custom_template.get("subject", f"Application Received: {job_title} - {company_name}")
            template_body_text = custom_template.get("body_text")
            
            # Prepare variables for Jinja2 template rendering
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
                "job_id": str(job_id),
                "application_id": str(application_id),
            }
            
            # Render template with variables
            body_html = EmailService.render_template(template_html, template_variables)
            subject = EmailService.render_template(template_subject, template_variables)
            
            # Render plain text if provided
            if template_body_text:
                body_text = EmailService.render_template(template_body_text, template_variables)
            else:
                # Generate plain text from HTML
                import re
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ')
            
            logger.info(
                "Using custom application confirmation template",
                template_id=str(custom_template.get("id")),
                recruiter_id=str(recruiter_id)
            )
        else:
            # Use default template (fallback)
            default_template_html = """
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Application Received</h1>
            </div>
            
            <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
                
                <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
                
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
                    <p style="margin: 0; font-size: 15px; color: #1f2937;">
                        <strong>✓ We have successfully received your application and CV.</strong>
                    </p>
                </div>
                
                <p style="font-size: 16px;">Our hiring team will carefully review your application and qualifications. We appreciate the time and effort you put into your application.</p>
                
                <p style="font-size: 16px;"><strong>What happens next?</strong></p>
                <ul style="font-size: 15px; color: #4b5563;">
                    <li>Our team will review your application and CV</li>
                    <li>If your profile matches our requirements, we will contact you via email</li>
                    <li>We aim to respond to all applicants within 5-7 business days</li>
                </ul>
                
                <p style="font-size: 16px;">We understand that waiting can be challenging, and we appreciate your patience as we carefully consider each application.</p>
                
                <div style="margin: 30px 0; padding: 20px; background-color: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0; font-size: 14px; color: #92400e;">
                        <strong>💡 Tip:</strong> Please check your email regularly, including your spam folder, as we may contact you regarding next steps.
                    </p>
                </div>
                
                <p style="font-size: 16px;">If you have any questions about your application or the position, please don't hesitate to reach out to us.</p>
                
                <p style="font-size: 16px; margin-bottom: 0;">
                    Best regards,<br>
                    <strong>The Hiring Team</strong><br>
                    <span style="color: {{primary_color}};">{{company_name}}</span>
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
                <p style="margin: 5px 0;">This is an automated confirmation email. Please do not reply to this message.</p>
                <p style="margin: 5px 0;">If you need to contact us, please use the contact information provided in the job posting.</p>
            </div>
        </div>
        """
            
            default_body_text = """
Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}}.

We have successfully received your application and CV. Our hiring team will carefully review your application and qualifications.

What happens next?
- Our team will review your application and CV
- If your profile matches our requirements, we will contact you via email
- We aim to respond to all applicants within 5-7 business days

We understand that waiting can be challenging, and we appreciate your patience as we carefully consider each application.

If you have any questions about your application or the position, please don't hesitate to reach out to us.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated confirmation email. Please do not reply to this message.
        """
            
            # Prepare variables for default template
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
            }
            
            # Render default template
            body_html = EmailService.render_template(default_template_html, template_variables)
            body_text = EmailService.render_template(default_body_text, template_variables)
            subject = f"Application Received: {job_title} - {company_name}"
            
            logger.info("Using default application confirmation template", recruiter_id=str(recruiter_id))
        
        # Send email using EmailService
        await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            job_description_id=job_id,
            application_id=application_id,
        )
        
        logger.info(
            "Application confirmation email sent",
            candidate_email=candidate_email,
            job_id=str(job_id),
            application_id=str(application_id),
            used_custom_template=custom_template is not None
        )
        
    except Exception as e:
        # Log error but don't fail the application submission
        logger.error(
            "Failed to send application confirmation email",
            error=str(e),
            candidate_email=candidate_email,
            job_id=str(job_id),
            application_id=str(application_id),
            exc_info=True
        )
        # Don't raise exception - email failure shouldn't break application submission


async def send_cv_rejection_email(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    job_id: UUID,
    recruiter_id: UUID,
    application_id: UUID
):
    """
    Send CV rejection email to candidate who applied but was not selected for interview
    Uses custom template from database if available, otherwise uses default template
    
    Args:
        candidate_email: Candidate's email address
        candidate_name: Candidate's full name
        job_title: Job position title
        job_id: Job description ID
        recruiter_id: Recruiter/company ID
        application_id: Application ID
    """
    try:
        # Get company branding for personalized email
        branding = await EmailService.get_company_branding(recruiter_id)
        company_name = branding.get("company_name", "Our Company") if branding else "Our Company"
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        # Try to get custom template from database
        custom_template = await EmailService.get_email_template(recruiter_id, "cv_rejection")
        
        if custom_template:
            # Use custom template from database
            template_html = custom_template.get("body_html", "")
            template_subject = custom_template.get("subject", f"Update on Your Application: {job_title}")
            template_body_text = custom_template.get("body_text")
            
            # Prepare variables for Jinja2 template rendering
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
                "job_id": str(job_id),
                "application_id": str(application_id),
            }
            
            # Render template with variables
            body_html = EmailService.render_template(template_html, template_variables)
            subject = EmailService.render_template(template_subject, template_variables)
            
            # Render plain text if provided
            if template_body_text:
                body_text = EmailService.render_template(template_body_text, template_variables)
            else:
                # Generate plain text from HTML
                import re
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ')
            
            logger.info(
                "Using custom CV rejection template",
                template_id=str(custom_template.get("id")),
                recruiter_id=str(recruiter_id)
            )
        else:
            # Use default template (fallback)
            default_template_html = """
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Update on Your Application</h1>
            </div>
            
            <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
                
                <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> and for taking the time to submit your application and CV.</p>
                
                <p style="font-size: 16px;">We genuinely appreciate the time and effort you invested in your application. We received many qualified applications, and after careful review, we have decided to move forward with candidates whose experience more closely aligns with the specific requirements of this role.</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
                    <p style="margin: 0; font-size: 15px; color: #1e40af;">
                        <strong>Please know that this decision in no way diminishes the value of your qualifications and experience.</strong> We recognize that you have rich experience and valuable skills that would be an asset to many organizations.
                    </p>
                </div>
                
                <p style="font-size: 16px;">We encourage you to continue pursuing opportunities that match your career goals. Your profile may be a perfect fit for future openings, and we hope you'll consider applying again when you see a position that aligns with your expertise.</p>
                
                <p style="font-size: 16px;">We wish you all the best in your job search and future career endeavors.</p>
                
                <p style="font-size: 16px; margin-bottom: 0;">
                    Best regards,<br>
                    <strong>The Hiring Team</strong><br>
                    <span style="color: {{primary_color}};">{{company_name}}</span>
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
                <p style="margin: 5px 0;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
        """
            
            default_body_text = """
Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}} and for taking the time to submit your application and CV.

We genuinely appreciate the time and effort you invested in your application. We received many qualified applications, and after careful review, we have decided to move forward with candidates whose experience more closely aligns with the specific requirements of this role.

Please know that this decision in no way diminishes the value of your qualifications and experience. We recognize that you have rich experience and valuable skills that would be an asset to many organizations.

We encourage you to continue pursuing opportunities that match your career goals. Your profile may be a perfect fit for future openings, and we hope you'll consider applying again when you see a position that aligns with your expertise.

We wish you all the best in your job search and future career endeavors.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated message. Please do not reply to this email.
        """
            
            # Prepare variables for default template
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
            }
            
            # Render default template
            body_html = EmailService.render_template(default_template_html, template_variables)
            body_text = EmailService.render_template(default_body_text, template_variables)
            subject = f"Update on Your Application: {job_title} - {company_name}"
            
            logger.info("Using default CV rejection template", recruiter_id=str(recruiter_id))
        
        # Send email using EmailService
        await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            job_description_id=job_id,
            application_id=application_id,
        )
        
        logger.info(
            "CV rejection email sent",
            candidate_email=candidate_email,
            job_id=str(job_id),
            application_id=str(application_id),
            used_custom_template=custom_template is not None
        )
        
    except Exception as e:
        logger.error(
            "Failed to send CV rejection email",
            error=str(e),
            candidate_email=candidate_email,
            job_id=str(job_id),
            application_id=str(application_id),
            exc_info=True
        )
        # Don't raise exception - email failure shouldn't break the process


async def send_interview_rejection_email(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    job_id: UUID,
    recruiter_id: UUID,
    interview_id: UUID,
    interview_date: Optional[str] = None
):
    """
    Send interview rejection email to candidate who completed interview but was not selected
    Uses custom template from database if available, otherwise uses default template
    
    Args:
        candidate_email: Candidate's email address
        candidate_name: Candidate's full name
        job_title: Job position title
        job_id: Job description ID
        recruiter_id: Recruiter/company ID
        interview_id: Interview ID
        interview_date: Optional interview date string
    """
    try:
        # Get company branding for personalized email
        branding = await EmailService.get_company_branding(recruiter_id)
        company_name = branding.get("company_name", "Our Company") if branding else "Our Company"
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        # Try to get custom template from database
        custom_template = await EmailService.get_email_template(recruiter_id, "interview_rejection")
        
        if custom_template:
            # Use custom template from database
            template_html = custom_template.get("body_html", "")
            template_subject = custom_template.get("subject", f"Update on Your Interview: {job_title}")
            template_body_text = custom_template.get("body_text")
            
            # Prepare variables for Jinja2 template rendering
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
                "job_id": str(job_id),
                "interview_id": str(interview_id),
                "interview_date": interview_date or "recently",
            }
            
            # Render template with variables
            body_html = EmailService.render_template(template_html, template_variables)
            subject = EmailService.render_template(template_subject, template_variables)
            
            # Render plain text if provided
            if template_body_text:
                body_text = EmailService.render_template(template_body_text, template_variables)
            else:
                # Generate plain text from HTML
                import re
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ')
            
            logger.info(
                "Using custom interview rejection template",
                template_id=str(custom_template.get("id")),
                recruiter_id=str(recruiter_id)
            )
        else:
            # Use default template (fallback)
            default_template_html = """
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Update on Your Interview</h1>
            </div>
            
            <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
                
                <p style="font-size: 16px;">Thank you for your continued interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> and for taking the time to participate in our interview process.</p>
                
                <p style="font-size: 16px;">We genuinely appreciate the time and effort you dedicated throughout the interview process. It was a pleasure learning more about your background, skills, and career aspirations.</p>
                
                <p style="font-size: 16px;">After careful consideration and thorough evaluation of all candidates, we have made the difficult decision to move forward with another candidate whose qualifications more closely align with the specific needs of this role at this time.</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
                    <p style="margin: 0; font-size: 15px; color: #1e40af;">
                        <strong>This decision was not an easy one, and we want you to know that your qualifications and interview performance were impressive.</strong> Unfortunately, we can only select one candidate for this position.
                    </p>
                </div>
                
                <p style="font-size: 16px;">We hope you understand, and we encourage you to continue pursuing opportunities that align with your career goals. We believe your skills and experience will be valuable assets to the right organization.</p>
                
                <p style="font-size: 16px;">We wish you the very best in your future endeavors and thank you again for your interest in {{company_name}}.</p>
                
                <p style="font-size: 16px; margin-bottom: 0;">
                    Best regards,<br>
                    <strong>The Hiring Team</strong><br>
                    <span style="color: {{primary_color}};">{{company_name}}</span>
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
                <p style="margin: 5px 0;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
        """
            
            default_body_text = """
Dear {{candidate_name}},

Thank you for your continued interest in the {{job_title}} position at {{company_name}} and for taking the time to participate in our interview process.

We genuinely appreciate the time and effort you dedicated throughout the interview process. It was a pleasure learning more about your background, skills, and career aspirations.

After careful consideration and thorough evaluation of all candidates, we have made the difficult decision to move forward with another candidate whose qualifications more closely align with the specific needs of this role at this time.

This decision was not an easy one, and we want you to know that your qualifications and interview performance were impressive. Unfortunately, we can only select one candidate for this position.

We hope you understand, and we encourage you to continue pursuing opportunities that align with your career goals. We believe your skills and experience will be valuable assets to the right organization.

We wish you the very best in your future endeavors and thank you again for your interest in {{company_name}}.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated message. Please do not reply to this email.
        """
            
            # Prepare variables for default template
            template_variables = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "primary_color": primary_color,
                "interview_date": interview_date or "recently",
            }
            
            # Render default template
            body_html = EmailService.render_template(default_template_html, template_variables)
            body_text = EmailService.render_template(default_body_text, template_variables)
            subject = f"Update on Your Interview: {job_title} - {company_name}"
            
            logger.info("Using default interview rejection template", recruiter_id=str(recruiter_id))
        
        # Send email using EmailService
        await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            job_description_id=job_id,
            interview_id=interview_id,
        )
        
        logger.info(
            "Interview rejection email sent",
            candidate_email=candidate_email,
            job_id=str(job_id),
            interview_id=str(interview_id),
            used_custom_template=custom_template is not None
        )
        
    except Exception as e:
        logger.error(
            "Failed to send interview rejection email",
            error=str(e),
            candidate_email=candidate_email,
            job_id=str(job_id),
            interview_id=str(interview_id),
            exc_info=True
        )
        # Don't raise exception - email failure shouldn't break the process


@router.post("/apply", response_model=Response[JobApplication], status_code=status.HTTP_201_CREATED)
@rate_limit_public()  # Limit: 20 requests per hour per IP (prevents spam applications)
async def apply_for_job(
    request: Request,
    background_tasks: BackgroundTasks,
    job_description_id: UUID = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    phone: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(None),
    cv_file: UploadFile = File(...),
    custom_fields: Optional[str] = Form(None)  # JSON string of custom field responses
):
    """
    Apply for a job (public endpoint, no auth required)
    
    Args:
        job_description_id: Job description ID
        email: Candidate email
        full_name: Candidate full name
        phone: Optional phone number
        cover_letter: Optional cover letter
        cv_file: CV file (PDF, DOCX, or TXT)
    
    Returns:
        Created application
    """
    try:
        # Verify job exists and is active
        job = db.service_client.table("job_descriptions").select("*").eq("id", str(job_description_id)).eq("is_active", True).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not active"
            )
        
        # Validate and sanitize inputs
        try:
            validated_email = validate_email_address(email)
            validated_phone = validate_phone_number(phone) if phone else None
            sanitized_full_name = sanitize_text_input(full_name, max_length=200)
            sanitized_cover_letter = sanitize_text_input(cover_letter, max_length=5000) if cover_letter else None
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        # Validate and sanitize file
        safe_filename, expected_file_size, validated_mime_type = validate_cv_file(cv_file)
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{job_description_id}_{safe_filename}")
        
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await cv_file.read()
            await out_file.write(content)
        
        # Verify actual file size matches expected
        file_size = os.path.getsize(temp_file_path)
        if file_size > expected_file_size and expected_file_size > 0:
            # Re-validate with actual size
            from app.utils.file_validation import validate_file_size, MAX_CV_FILE_SIZE
            validate_file_size(file_size, MAX_CV_FILE_SIZE, "CV")
        
        mime_type = validated_mime_type
        
        # Upload to Supabase Storage (use sanitized filename)
        storage_path = f"applications/{job_description_id}/{safe_filename}"
        bucket_name = getattr(settings, 'supabase_storage_bucket_cvs', 'cvs')
        
        try:
            with open(temp_file_path, 'rb') as f:
                # Use the same bucket as CVs
                db.service_client.storage.from_(bucket_name).upload(
                    storage_path,
                    f.read(),
                    file_options={"content-type": mime_type}
                )
        except Exception as e:
            error_str = str(e)
            
            # Handle duplicate file gracefully (409 Conflict)
            if "409" in error_str or "duplicate" in error_str.lower() or "already exists" in error_str.lower():
                logger.info(
                    "CV file already exists in storage, using existing file",
                    storage_path=storage_path,
                    bucket=bucket_name,
                )
                # File already exists, continue with the existing file
                # No need to raise an error - we'll use the existing file path
            elif "bucket not found" in error_str.lower() or "404" in error_str:
                # For real errors, clean up the temp file before raising
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                logger.error("Error uploading CV - bucket not found", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Storage bucket '{bucket_name}' not found. Please create the bucket in Supabase Storage. See documentation for setup instructions.",
                )
            else:
                # For other upload errors, clean up and surface the error
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                logger.error("Error uploading CV", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload CV: {error_str}",
                )
        
        # Parse CV
        try:
            parsed_text = CVParser.parse_file(temp_file_path, mime_type)
        except Exception as e:
            logger.warning("Error parsing CV", error=str(e))
            parsed_text = ""
        
        # Clean up temp file (only if it still exists)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Create application (use validated inputs)
        application_data = JobApplicationCreate(
            job_description_id=job_description_id,
            email=validated_email,
            full_name=sanitized_full_name,
            phone=validated_phone,
            cover_letter=sanitized_cover_letter
        )
        
        application = await ApplicationService.create_application(
            application_data=application_data,
            cv_file_name=safe_filename,
            cv_file_path=storage_path,
            cv_file_size=file_size,
            cv_mime_type=mime_type,
            cv_text=parsed_text
        )
        
        # Save custom form field responses if provided
        if custom_fields:
            try:
                import json
                custom_data = json.loads(custom_fields)
                responses = []
                for key, value in custom_data.items():
                    # Handle different value types
                    if value is None:
                        field_value = ""
                    elif isinstance(value, list):
                        # For checkbox fields (arrays), convert to JSON string
                        field_value = json.dumps(value)
                    elif isinstance(value, (dict, bool)):
                        # For complex types, convert to JSON string
                        field_value = json.dumps(value)
                    else:
                        # For simple types, convert to string
                        field_value = str(value)
                    
                    responses.append(
                        ApplicationFormResponseCreate(
                            application_id=UUID(application["id"]),
                            field_key=key,
                            field_value=field_value
                        )
                    )
                
                if responses:
                    await ApplicationFormService.save_form_responses(responses)
            except Exception as e:
                logger.warning("Error saving custom form responses", error=str(e), exc_info=True)
                # Don't fail the application if custom fields fail
        
        # Send automated confirmation email to candidate (background task)
        background_tasks.add_task(
            send_application_confirmation_email,
            candidate_email=validated_email,
            candidate_name=sanitized_full_name,
            job_title=job.data[0].get("title", "the position"),
            job_id=job_description_id,
            recruiter_id=UUID(job.data[0].get("recruiter_id")),
            application_id=UUID(application["id"])
        )
        
        return Response(
            success=True,
            message="Application submitted successfully",
            data=application
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating application", error=str(e), exc_info=True)
        # Provide more detailed error message
        error_detail = str(e)
        if "could not find the table" in error_detail.lower():
            error_detail = "Database tables not found. Please run migrations."
        elif "RLS" in error_detail or "row-level security" in error_detail.lower():
            error_detail = "Database access error. Please check RLS policies."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {error_detail}"
        )


@router.get("", response_model=Response[List[dict]])
async def list_all_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all applications for the recruiter (across all jobs)
    
    Args:
        status: Optional status filter
        recruiter_id: Current user ID
    
    Returns:
        List of applications with job and candidate details
    """
    try:
        # Get all job IDs for this recruiter
        jobs = db.service_client.table("job_descriptions").select("id").eq("recruiter_id", str(recruiter_id)).execute()
        job_ids = [job["id"] for job in (jobs.data or [])]
        
        logger.info("Fetching applications", recruiter_id=str(recruiter_id), job_count=len(job_ids), job_ids=job_ids[:3] if job_ids else [])
        
        if not job_ids:
            return Response(
                success=True,
                message="No applications found",
                data=[]
            )
        
        # Get all applications for these jobs
        # Fetch applications first - Applications page reads from job_applications table
        query = db.service_client.table("job_applications").select("*").in_("job_description_id", job_ids)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("applied_at", desc=True)
        applications_response = query.execute()
        applications_data = applications_response.data or []
        
        logger.info("Found applications in job_applications table", 
                   application_count=len(applications_data),
                   job_ids=job_ids[:3] if job_ids else [])
        
        if not applications_data:
            logger.warning("No applications found in job_applications table", 
                          recruiter_id=str(recruiter_id),
                          job_ids=job_ids,
                          note="This means applications were not created when candidates submitted forms")
            return Response(
                success=True,
                message="Applications retrieved successfully",
                data=[]
            )
        
        # Get related data separately
        candidate_ids = list(set(app.get("candidate_id") for app in applications_data if app.get("candidate_id")))
        application_ids = [app.get("id") for app in applications_data if app.get("id")]
        
        # Fetch candidates
        candidates_data = {}
        if candidate_ids:
            candidates_response = db.service_client.table("candidates").select("*").in_("id", candidate_ids).execute()
            for candidate in (candidates_response.data or []):
                candidates_data[candidate["id"]] = candidate
        
        # Fetch job details
        job_details = {}
        if job_ids:
            jobs_response = db.service_client.table("job_descriptions").select("id, title").in_("id", job_ids).execute()
            for job in (jobs_response.data or []):
                job_details[job["id"]] = job
        
        # Fetch screening results
        screening_results = {}
        if application_ids:
            screening_response = db.service_client.table("cv_screening_results").select("*").in_("application_id", application_ids).execute()
            for screening in (screening_response.data or []):
                screening_results[screening["application_id"]] = screening
        
        # Combine data
        enriched_applications = []
        for app in applications_data:
            candidate_id = app.get("candidate_id")
            job_id = app.get("job_description_id")
            app_id = app.get("id")
            
            enriched_app = {
                **app,
                "candidates": candidates_data.get(candidate_id),
                "job_descriptions": job_details.get(job_id),
                "cv_screening_results": screening_results.get(app_id)
            }
            enriched_applications.append(enriched_app)
        
        return Response(
            success=True,
            message="Applications retrieved successfully",
            data=enriched_applications
        )
    except Exception as e:
        logger.error("Error listing all applications", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{application_id}", response_model=Response[dict])
async def get_application(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a single application by ID
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Application with candidate and job details
    """
    try:
        # Get application with related data
        result = db.service_client.table("job_applications").select(
            "*, candidates(id, full_name, email, phone), job_descriptions(id, title, recruiter_id)"
        ).eq("id", str(application_id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        application = result.data[0]
        
        # Verify recruiter owns the job
        job_data = application.get("job_descriptions", {})
        if job_data.get("recruiter_id") != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application"
            )
        
        return Response(
            success=True,
            message="Application retrieved successfully",
            data=application
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting application", error=str(e), application_id=str(application_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/job/{job_description_id}", response_model=Response[List[dict]])
async def list_applications(
    job_description_id: UUID,
    application_status: Optional[str] = Query(None, description="Filter by status", alias="status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List applications for a job (recruiter only)
    
    Args:
        job_description_id: Job description ID
        application_status: Optional status filter (aliased as 'status' in query)
        recruiter_id: Current user ID
    
    Returns:
        List of applications
    """
    try:
        applications = await ApplicationService.list_applications_for_job(
            job_description_id=job_description_id,
            recruiter_id=recruiter_id,
            status=application_status
        )
        return Response(
            success=True,
            message="Applications retrieved successfully",
            data=applications
        )
    except Exception as e:
        logger.error("Error listing applications", error=str(e), job_id=str(job_description_id), recruiter_id=str(recruiter_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{application_id}/screen", response_model=Response[dict])
async def screen_application(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Screen a single application (recruiter only)
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID
    
    Returns:
        Screening result
    """
    try:
        # Verify access
        app = await ApplicationService.get_application(application_id)
        job = db.service_client.table("job_descriptions").select("*").eq("id", app["job_description_id"]).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Get CV text
        cv = db.service_client.table("cvs").select("parsed_text").eq("id", app["cv_id"]).execute()
        if not cv.data or not cv.data[0].get("parsed_text"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV not found or not parsed"
            )
        
        cv_text = cv.data[0]["parsed_text"]
        job_description = job.data[0]
        
        # Screen
        screening_service = CVScreeningService()
        result = await screening_service.screen_application(
            application_id=application_id,
            cv_text=cv_text,
            job_description=job_description
        )
        
        return Response(
            success=True,
            message="Application screened successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error screening application", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/job/{job_description_id}/screen-all", response_model=Response[dict])
async def screen_all_applications(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Screen all pending applications for a job (recruiter only)
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID
    
    Returns:
        Screening summary
    """
    try:
        # Verify access
        job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get pending applications
        applications = db.service_client.table("job_applications").select("id").eq("job_description_id", str(job_description_id)).eq("status", "pending").execute()
        
        if not applications.data:
            return Response(
                success=True,
                message="No pending applications to screen",
                data={"screened": 0}
            )
        
        application_ids = [UUID(app["id"]) for app in applications.data]
        
        # Batch screen
        screening_service = CVScreeningService()
        results = await screening_service.batch_screen_applications(
            job_description_id=job_description_id,
            application_ids=application_ids
        )
        
        # Count qualified
        qualified_count = sum(1 for r in results if r.get("recommendation") == "qualified")
        
        return Response(
            success=True,
            message=f"Screened {len(results)} applications",
            data={
                "screened": len(results),
                "qualified": qualified_count,
                "maybe_qualified": sum(1 for r in results if r.get("recommendation") == "maybe_qualified"),
                "not_qualified": sum(1 for r in results if r.get("recommendation") == "not_qualified")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in batch screening", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{application_id}/screening", response_model=Response[dict])
async def get_screening_result(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get screening result for an application (recruiter only)
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID
    
    Returns:
        Screening result
    """
    try:
        # Verify access
        app = await ApplicationService.get_application(application_id)
        job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", app["job_description_id"]).execute()
        if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Get screening result
        screening = db.service_client.table("cv_screening_results").select("*").eq("application_id", str(application_id)).execute()
        
        if not screening.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screening result not found"
            )
        
        return Response(
            success=True,
            message="Screening result retrieved successfully",
            data=screening.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching screening result", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{application_id}/status", response_model=Response[JobApplication])
async def update_application_status(
    application_id: UUID,
    status: str = Query(..., description="New status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update application status (recruiter only)
    
    Args:
        application_id: Application ID
        status: New status
        recruiter_id: Current user ID
    
    Returns:
        Updated application
    """
    try:
        application = await ApplicationService.update_application_status(
            application_id=application_id,
            status=status,
            recruiter_id=recruiter_id
        )
        return Response(
            success=True,
            message="Application status updated successfully",
            data=application
        )
    except Exception as e:
        logger.error("Error updating application status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

