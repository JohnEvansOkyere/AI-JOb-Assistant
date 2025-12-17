"""
Email API Routes
Handles email composition, sending, templates, and branding
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Body, BackgroundTasks
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.schemas.common import Response
from app.services.email_service import EmailService
from app.services.ticket_service import TicketService
from app.utils.auth import get_current_user_id, get_current_user
from app.config import settings
from app.database import db
import structlog
import base64

logger = structlog.get_logger()

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_email(
    request: Request,
    recipient_email: str = Form(...),
    subject: str = Form(...),
    body_html: str = Form(...),
    recipient_name: Optional[str] = Form(None),
    candidate_id: Optional[UUID] = Form(None),
    job_description_id: Optional[UUID] = Form(None),
    interview_ticket_id: Optional[UUID] = Form(None),
    application_id: Optional[UUID] = Form(None),
    branding_id: Optional[UUID] = Form(None),
    template_id: Optional[UUID] = Form(None),
    from_email: Optional[str] = Form(None),  # Frontend configurable
    from_name: Optional[str] = Form(None),   # Frontend configurable
    email_provider: Optional[str] = Form(None),  # "resend" or "smtp"
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Send a custom email with company branding
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        body_html: HTML email body
        recipient_name: Optional recipient name
        candidate_id: Optional candidate ID
        job_description_id: Optional job ID
        interview_ticket_id: Optional ticket ID
        application_id: Optional application ID
        branding_id: Optional branding ID (uses default if not provided)
        template_id: Optional template ID used
        from_email: Sender email address (if None, uses default from settings)
        from_name: Sender name (if None, uses default from settings)
        email_provider: "resend" or "smtp" (if None, uses default from settings)
        recruiter_id: Current recruiter ID
    
    Returns:
        Email sending result
    """
    try:
        result = await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=recipient_email,
            subject=subject,
            body_html=body_html,
            template_id=template_id,
            branding_id=branding_id,
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            interview_ticket_id=interview_ticket_id,
            application_id=application_id,
            recipient_name=recipient_name,
            from_email=from_email,
            from_name=from_name,
            email_provider=email_provider,
        )
        
        return Response(
            success=True,
            message="Email sent successfully",
            data=result
        )
    except Exception as e:
        logger.error("Error sending email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/send-ticket/{ticket_id}")
async def send_ticket_email(
    request: Request,
    ticket_id: UUID,
    from_email: Optional[str] = Form(None),  # Frontend configurable
    from_name: Optional[str] = Form(None),   # Frontend configurable
    email_provider: Optional[str] = Form(None),  # "resend" or "smtp"
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Send interview ticket email to candidate
    
    Args:
        ticket_id: Interview ticket ID
        recruiter_id: Current recruiter ID
    
    Returns:
        Email sending result
    """
    try:
        # Get ticket details
        ticket_response = db.service_client.table("interview_tickets").select(
            "*, job_descriptions(title, id), candidates(email, full_name, id)"
        ).eq("id", str(ticket_id)).execute()
        
        if not ticket_response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_response.data[0]
        job = ticket.get("job_descriptions", {})
        candidate = ticket.get("candidates", {})
        
        if not candidate.get("email"):
            raise HTTPException(status_code=400, detail="Candidate email not found")
        
        # Generate interview link
        from app.config import settings
        base_url = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:3000"
        interview_link = f"{base_url}/interview/job/{job.get('id')}"
        
        result = await EmailService.send_ticket_email(
            recruiter_id=recruiter_id,
            candidate_id=UUID(candidate["id"]),
            ticket_code=ticket["code"],
            interview_link=interview_link,
            job_title=job.get("title", "Interview"),
            candidate_name=candidate.get("full_name", "Candidate"),
            candidate_email=candidate["email"],
            ticket_id=ticket_id,
            job_description_id=UUID(job["id"]),
            expires_in_hours=ticket.get("expires_in_hours"),
            from_email=from_email,
            from_name=from_name,
            email_provider=email_provider,
        )
        
        return Response(
            success=True,
            message="Ticket email sent successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending ticket email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send ticket email: {str(e)}"
        )


@router.post("/preview-interview-invitation")
async def preview_interview_invitation(
    request: Request,
    candidate_id: UUID = Body(...),
    job_description_id: UUID = Body(...),
    ticket_code: Optional[str] = Body(None),
    interview_link: Optional[str] = Body(None),
    expires_in_hours: Optional[int] = Body(None),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Preview interview invitation email template without sending
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        ticket_code: Optional ticket code (will be generated if not provided)
        interview_link: Optional interview link (will be generated if not provided)
        expires_in_hours: Optional expiration hours
        recruiter_id: Current recruiter ID
    
    Returns:
        Preview HTML of the email
    """
    try:
        # Get candidate and job details
        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(candidate_id)).execute()
        job_response = db.service_client.table("job_descriptions").select("title").eq("id", str(job_description_id)).execute()
        
        if not candidate_response.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate = candidate_response.data[0]
        job = job_response.data[0]
        
        # Generate ticket code if not provided
        if not ticket_code:
            from app.services.ticket_service import TicketService
            ticket_code = TicketService.generate_ticket_code()
        
        # Generate interview link if not provided
        if not interview_link:
            base_url = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:3000"
            interview_link = f"{base_url}/interview/job/{job_description_id}"
        
        # Get branding
        branding = await EmailService.get_company_branding(recruiter_id)
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        # Interview invitation email template
        template_html = """
        <div style="max-width: 600px; margin: 0 auto;">
            <h2 style="color: {{primary_color}};">Interview Invitation</h2>
            <p>Dear {{candidate_name}},</p>
            <p>Thank you for your interest in the <strong>{{job_title}}</strong> position. We would like to invite you to complete an AI-powered interview.</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Your Interview Ticket Code:</h3>
                <p style="font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 2px; color: {{primary_color}};">{{ticket_code}}</p>
            </div>
            
            <p><strong>To start your interview:</strong></p>
            <ol>
                <li>Click the link below or copy it into your browser</li>
                <li>Enter your ticket code when prompted</li>
                <li>Complete the interview at your convenience</li>
            </ol>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{interview_link}}" style="background-color: {{primary_color}}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Start Interview</a>
            </div>
            
            <p style="font-size: 14px; color: #666;">Or copy this link: <a href="{{interview_link}}">{{interview_link}}</a></p>
            
            {% if expires_in_hours %}
            <p style="color: #d97706; font-weight: bold;">⏰ This ticket expires in {{expires_in_hours}} hours. Please complete your interview before then.</p>
            {% endif %}
            
            <p>If you have any questions, please don't hesitate to reach out.</p>
            <p>Best regards,<br>The Hiring Team</p>
        </div>
        """
        
        variables = {
            "candidate_name": candidate.get("full_name", "Candidate"),
            "job_title": job["title"],
            "ticket_code": ticket_code,
            "interview_link": interview_link,
            "primary_color": primary_color,
            "expires_in_hours": expires_in_hours,
        }
        
        body_html = EmailService.render_template(template_html, variables)
        final_html = EmailService.wrap_with_letterhead(body_html, branding)
        
        return Response(
            success=True,
            message="Preview generated successfully",
            data={
                "html": final_html,
                "subject": f"Interview Invitation: {job['title']}",
                "recipient_email": candidate["email"],
                "recipient_name": candidate.get("full_name", "Candidate")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating preview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/preview-offer-letter")
async def preview_offer_letter(
    request: Request,
    candidate_id: UUID = Body(...),
    job_description_id: UUID = Body(...),
    salary: Optional[str] = Body(None),
    start_date: Optional[str] = Body(None),
    location: Optional[str] = Body(None),
    employment_type: Optional[str] = Body(None),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Preview offer letter email template without sending
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        salary: Optional salary information
        start_date: Optional start date
        location: Optional location
        employment_type: Optional employment type
        recruiter_id: Current recruiter ID
    
    Returns:
        Preview HTML of the email
    """
    try:
        # Get candidate and job details
        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(candidate_id)).execute()
        job_response = db.service_client.table("job_descriptions").select("title").eq("id", str(job_description_id)).execute()
        
        if not candidate_response.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate = candidate_response.data[0]
        job = job_response.data[0]
        
        # Prepare offer details
        offer_details = {}
        if salary:
            offer_details["salary"] = salary
        if start_date:
            offer_details["start_date"] = start_date
        if location:
            offer_details["location"] = location
        if employment_type:
            offer_details["employment_type"] = employment_type
        
        # Generate preview HTML (without actually sending)
        # Use a placeholder URL for the offer letter
        offer_letter_url = "#"
        
        # Get branding
        branding = await EmailService.get_company_branding(recruiter_id)
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        # Offer letter email template
        template_html = """
        <div style="max-width: 600px; margin: 0 auto;">
            <h2 style="color: {{primary_color}};">Job Offer - {{job_title}}</h2>
            <p>Dear {{candidate_name}},</p>
            <p>We are delighted to extend a job offer to you for the position of <strong>{{job_title}}</strong>!</p>
            
            {% if offer_details %}
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Offer Details:</h3>
                {% if offer_details.salary %}
                <p><strong>Salary:</strong> {{offer_details.salary}}</p>
                {% endif %}
                {% if offer_details.start_date %}
                <p><strong>Start Date:</strong> {{offer_details.start_date}}</p>
                {% endif %}
                {% if offer_details.location %}
                <p><strong>Location:</strong> {{offer_details.location}}</p>
                {% endif %}
                {% if offer_details.employment_type %}
                <p><strong>Employment Type:</strong> {{offer_details.employment_type}}</p>
                {% endif %}
            </div>
            {% endif %}
            
            <p>Please find the detailed offer letter attached to this email.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{offer_letter_url}}" style="background-color: {{primary_color}}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Download Offer Letter</a>
            </div>
            
            <p>Please review the offer letter and let us know if you have any questions. We look forward to welcoming you to our team!</p>
            <p>Best regards,<br>The Hiring Team</p>
        </div>
        """
        
        variables = {
            "candidate_name": candidate.get("full_name", "Candidate"),
            "job_title": job["title"],
            "primary_color": primary_color,
            "offer_letter_url": offer_letter_url,
            "offer_details": offer_details if offer_details else {},
        }
        
        body_html = EmailService.render_template(template_html, variables)
        final_html = EmailService.wrap_with_letterhead(body_html, branding)
        
        return Response(
            success=True,
            message="Preview generated successfully",
            data={
                "html": final_html,
                "subject": f"Job Offer: {job['title']}",
                "recipient_email": candidate["email"],
                "recipient_name": candidate.get("full_name", "Candidate")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating preview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/send-offer-letter")
async def send_offer_letter(
    request: Request,
    candidate_id: UUID = Form(...),
    job_description_id: UUID = Form(...),
    offer_letter_file: UploadFile = File(...),
    salary: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    employment_type: Optional[str] = Form(None),
    from_email: Optional[str] = Form(None),  # Frontend configurable
    from_name: Optional[str] = Form(None),   # Frontend configurable
    email_provider: Optional[str] = Form(None),  # "resend" or "smtp"
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Send offer letter email to candidate with attached PDF
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        offer_letter_file: Offer letter PDF file
        salary: Optional salary information
        start_date: Optional start date
        location: Optional location
        employment_type: Optional employment type
        recruiter_id: Current recruiter ID
    
    Returns:
        Email sending result
    """
    try:
        # Get candidate and job details
        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(candidate_id)).execute()
        job_response = db.service_client.table("job_descriptions").select("title").eq("id", str(job_description_id)).execute()
        
        if not candidate_response.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        candidate = candidate_response.data[0]
        job = job_response.data[0]
        
        # Upload offer letter to Supabase Storage
        bucket_name = "offer-letters"  # Create this bucket in Supabase
        import time
        import uuid
        
        # Make filename unique to avoid conflicts
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        file_extension = offer_letter_file.filename.split('.')[-1] if '.' in offer_letter_file.filename else 'pdf'
        unique_filename = f"offer_letter_{timestamp}_{unique_id}.{file_extension}"
        file_path = f"{job_description_id}/{candidate_id}/{unique_filename}"
        
        content = await offer_letter_file.read()
        
        try:
            db.service_client.storage.from_(bucket_name).upload(
                file_path,
                content,
                file_options={"content-type": "application/pdf"}
            )
        except Exception as e:
            error_str = str(e).lower()
            # If bucket doesn't exist, use cvs bucket as fallback
            if "bucket not found" in error_str or "404" in str(e):
                bucket_name = "cvs"
                db.service_client.storage.from_(bucket_name).upload(
                    file_path,
                    content,
                    file_options={"content-type": "application/pdf"}
                )
            # If duplicate error, try to remove existing file first
            elif "409" in str(e) or "duplicate" in error_str or "already exists" in error_str:
                try:
                    # Try to remove existing file
                    db.service_client.storage.from_(bucket_name).remove([file_path])
                except:
                    pass  # Ignore if file doesn't exist or removal fails
                # Retry upload with unique filename (should work now)
                db.service_client.storage.from_(bucket_name).upload(
                    file_path,
                    content,
                    file_options={"content-type": "application/pdf"}
                )
            else:
                raise
        
        # Get public URL
        offer_letter_url = db.service_client.storage.from_(bucket_name).get_public_url(file_path)
        
        # Prepare offer details
        offer_details = {}
        if salary:
            offer_details["salary"] = salary
        if start_date:
            offer_details["start_date"] = start_date
        if location:
            offer_details["location"] = location
        if employment_type:
            offer_details["employment_type"] = employment_type
        
        # Send offer letter email (pass content directly to avoid re-downloading)
        result = await EmailService.send_offer_letter_email(
            recruiter_id=recruiter_id,
            candidate_id=candidate_id,
            candidate_email=candidate["email"],
            candidate_name=candidate.get("full_name", "Candidate"),
            job_title=job["title"],
            job_description_id=job_description_id,
            offer_letter_url=offer_letter_url,
            offer_letter_content=content,  # Pass content directly
            offer_details=offer_details if offer_details else None,
            from_email=from_email,
            from_name=from_name,
            email_provider=email_provider,
        )
        
        return Response(
            success=True,
            message="Offer letter email sent successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        logger.error("Error sending offer letter", error=error_message, recruiter_id=str(recruiter_id))
        
        # Provide more helpful error messages
        if "RESEND_API_KEY" in error_message or "not configured" in error_message or "Email service not configured" in error_message:
            error_message = "Email service not configured. Please set RESEND_API_KEY in your environment variables. See docs/EMAIL_SETUP_GUIDE.md for setup instructions."
        elif "domain" in error_message.lower() or "from" in error_message.lower() or "verify" in error_message.lower():
            error_message = f"Email sending failed: Please verify your 'from' email address in Resend. Current: {settings.email_from_address}. See docs/EMAIL_SETUP_GUIDE.md for setup instructions."
        elif "api key" in error_message.lower() or "unauthorized" in error_message.lower():
            error_message = "Email sending failed: Invalid or missing Resend API key. Please check your RESEND_API_KEY. See docs/EMAIL_SETUP_GUIDE.md for setup instructions."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.get("/sent")
async def get_sent_emails(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    candidate_id: Optional[UUID] = None,
    job_description_id: Optional[UUID] = None,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get sent emails history
    
    Args:
        limit: Number of emails to return
        offset: Pagination offset
        candidate_id: Optional filter by candidate
        job_description_id: Optional filter by job
        recruiter_id: Current recruiter ID
    
    Returns:
        List of sent emails
    """
    try:
        query = db.service_client.table("sent_emails").select("*").eq("recruiter_id", str(recruiter_id))
        
        if candidate_id:
            query = query.eq("candidate_id", str(candidate_id))
        if job_description_id:
            query = query.eq("job_description_id", str(job_description_id))
        
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return Response(
            success=True,
            message="Sent emails retrieved successfully",
            data=response.data or []
        )
    except Exception as e:
        logger.error("Error fetching sent emails", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sent emails: {str(e)}"
        )


@router.get("/sent/{email_id}")
async def get_sent_email(
    request: Request,
    email_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific sent email
    
    Args:
        email_id: Email ID
        recruiter_id: Current recruiter ID
    
    Returns:
        Email details
    """
    try:
        response = db.service_client.table("sent_emails").select("*").eq("id", str(email_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return Response(
            success=True,
            message="Email retrieved successfully",
            data=response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch email: {str(e)}"
        )


@router.post("/send-interview-invitation", status_code=status.HTTP_201_CREATED)
async def send_interview_invitation(
    request: Request,
    candidate_id: UUID = Body(...),
    job_description_id: UUID = Body(...),
    expires_in_hours: Optional[int] = Body(48),
    from_email: Optional[str] = Body(None),  # Frontend configurable
    from_name: Optional[str] = Body(None),   # Frontend configurable
    email_provider: Optional[str] = Body(None),  # "resend" or "smtp"
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create interview ticket and send invitation email to qualified candidate
    
    This is the main function for sending interview invitations after CV screening.
    It creates a ticket and sends the email automatically.
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        expires_in_hours: Ticket expiration (default: 48 hours)
        from_email: Sender email address (if None, uses default from settings)
        from_name: Sender name (if None, uses default from settings)
        email_provider: "resend" or "smtp" (if None, uses default from settings)
        recruiter_id: Current recruiter ID
    
    Returns:
        Created ticket and email sending result
    """
    try:
        # Get candidate and job details
        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(candidate_id)).execute()
        if not candidate_response.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate = candidate_response.data[0]
        if not candidate.get("email"):
            raise HTTPException(status_code=400, detail="Candidate email not found")
        
        job_response = db.service_client.table("job_descriptions").select("title, id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")
        
        job = job_response.data[0]
        
        # Create interview ticket
        ticket = await TicketService.create_ticket(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            created_by=recruiter_id,
            expires_in_hours=expires_in_hours
        )
        
        # Generate interview link
        base_url = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:3000"
        interview_link = f"{base_url}/interview/job/{job_description_id}"
        
        # Send interview invitation email
        email_result = await EmailService.send_ticket_email(
            recruiter_id=recruiter_id,
            candidate_id=candidate_id,
            ticket_code=ticket["ticket_code"],
            interview_link=interview_link,
            job_title=job.get("title", "Interview"),
            candidate_name=candidate.get("full_name", "Candidate"),
            candidate_email=candidate["email"],
            ticket_id=UUID(ticket["id"]),
            job_description_id=job_description_id,
            expires_in_hours=expires_in_hours,
            from_email=from_email,
            from_name=from_name,
            email_provider=email_provider,
        )
        
        return Response(
            success=True,
            message="Interview invitation sent successfully",
            data={
                "ticket": ticket,
                "email": email_result
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending interview invitation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send interview invitation: {str(e)}"
        )


@router.post("/bulk-send", status_code=status.HTTP_201_CREATED)
async def bulk_send_emails(
    request: Request,
    job_description_id: UUID = Body(...),
    job_status: str = Body(...),  # accepted, rejected
    template_id: Optional[UUID] = Body(None),
    template_type: Optional[str] = Body(None),  # acceptance, rejection
    custom_subject: Optional[str] = Body(None),
    custom_body_html: Optional[str] = Body(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Bulk send emails to all candidates with a specific job_status for a job
    
    Args:
        job_description_id: Job description ID
        job_status: Filter by job_status (accepted, rejected)
        template_id: Optional template ID to use
        template_type: Template type if not using template_id (acceptance, rejection)
        custom_subject: Optional custom subject (will use template if not provided)
        custom_body_html: Optional custom body (will use template if not provided)
        background_tasks: Background tasks for email sending
        recruiter_id: Current recruiter ID
    
    Returns:
        Bulk sending result with count
    """
    try:
        
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id, title").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")
        
        job = job_response.data[0]
        
        # Get all interviews with the specified job_status
        interviews_response = db.service_client.table("interviews").select(
            "id, candidate_id, candidates!inner(email, full_name)"
        ).eq("job_description_id", str(job_description_id)).eq("job_status", job_status).execute()
        
        if not interviews_response.data:
            return Response(
                success=True,
                message=f"No candidates found with status '{job_status}'",
                data={"sent_count": 0, "total_count": 0}
            )
        
        interviews = interviews_response.data
        total_count = len(interviews)
        
        # Get template if provided
        template = None
        if template_id:
            template_response = db.service_client.table("email_templates").select("*").eq("id", str(template_id)).eq("recruiter_id", str(recruiter_id)).execute()
            if template_response.data:
                template = template_response.data[0]
        elif template_type:
            template_response = db.service_client.table("email_templates").select("*").eq("recruiter_id", str(recruiter_id)).eq("template_type", template_type).eq("is_default", True).limit(1).execute()
            if template_response.data:
                template = template_response.data[0]
        
        # Prepare email data
        subject = custom_subject or (template.get("subject") if template else f"Update: {job['title']}")
        body_template = custom_body_html or (template.get("body_html") if template else "Dear {{first_name}},\n\nThank you for your interest.")
        
        # Send emails in background
        sent_count = 0
        for interview in interviews:
            candidate = interview.get("candidates", {})
            if not candidate.get("email"):
                continue
            
            # Substitute variables
            candidate_data = {
                "email": candidate.get("email", ""),
                "full_name": candidate.get("full_name", ""),
            }
            job_data = {
                "id": str(job_description_id),
                "title": job["title"],
            }
            
            body_html = EmailService.substitute_template_variables(
                body_template,
                candidate_data,
                job_data
            )
            
            # Send email in background
            background_tasks.add_task(
                send_single_email_background,
                recruiter_id=recruiter_id,
                recipient_email=candidate["email"],
                recipient_name=candidate.get("full_name", "Candidate"),
                subject=subject,
                body_html=body_html,
                candidate_id=UUID(interview["candidate_id"]),
                job_description_id=job_description_id
            )
            sent_count += 1
        
        logger.info(
            "Bulk email sending initiated",
            job_id=str(job_description_id),
            job_status=job_status,
            total_count=total_count,
            sent_count=sent_count
        )
        
        return Response(
            success=True,
            message=f"Bulk email sending initiated for {sent_count} candidates",
            data={
                "sent_count": sent_count,
                "total_count": total_count,
                "job_status": job_status
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in bulk email sending", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk emails: {str(e)}"
        )


async def send_single_email_background(
    recruiter_id: UUID,
    recipient_email: str,
    recipient_name: str,
    subject: str,
    body_html: str,
    candidate_id: UUID,
    job_description_id: UUID
):
    """Background task to send a single email"""
    try:
        await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            body_html=body_html,
            candidate_id=candidate_id,
            job_description_id=job_description_id,
        )
    except Exception as e:
        logger.error("Error sending email in bulk", error=str(e), recipient=recipient_email)


@router.post("/send-offer-letter", status_code=status.HTTP_201_CREATED)
async def send_offer_letter(
    request: Request,
    candidate_id: UUID = Body(...),
    job_description_id: UUID = Body(...),
    offer_letter_pdf_url: str = Body(..., description="URL to the PDF offer letter (Supabase Storage or external)"),
    offer_details: Optional[Dict[str, Any]] = Body(None, description="Optional offer details (salary, start_date, location)"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Send offer letter email with PDF attachment to qualified candidate
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        offer_letter_pdf_url: URL to PDF offer letter (must be publicly accessible)
        offer_details: Optional offer details dict
        recruiter_id: Current recruiter ID
    
    Returns:
        Email sending result
    """
    try:
        # Get candidate and job details
        candidate_response = db.service_client.table("candidates").select("email, full_name").eq("id", str(candidate_id)).execute()
        if not candidate_response.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate = candidate_response.data[0]
        if not candidate.get("email"):
            raise HTTPException(status_code=400, detail="Candidate email not found")
        
        job_response = db.service_client.table("job_descriptions").select("title, id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")
        
        job = job_response.data[0]
        
        # Send offer letter email
        result = await EmailService.send_offer_letter_email(
            recruiter_id=recruiter_id,
            candidate_id=candidate_id,
            candidate_email=candidate["email"],
            candidate_name=candidate.get("full_name", "Candidate"),
            job_title=job.get("title", "Position"),
            job_description_id=job_description_id,
            offer_letter_pdf_url=offer_letter_pdf_url,
            offer_details=offer_details,
        )
        
        return Response(
            success=True,
            message="Offer letter sent successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending offer letter", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send offer letter: {str(e)}"
        )

