"""
Email Service
Handles email sending with templates, branding, and letterhead support
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import resend
from jinja2 import Template
import httpx
import base64
from app.config import settings
from app.database import db
import structlog

logger = structlog.get_logger()

# Initialize Resend client
resend_client = None
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
    resend_client = resend
    logger.info("Resend email client initialized")
else:
    logger.warning("Resend API key not configured - email sending disabled")


class EmailService:
    """Service for sending emails with templates and branding"""
    
    @staticmethod
    async def get_company_branding(recruiter_id: UUID) -> Optional[Dict[str, Any]]:
        """Get company branding/letterhead for a recruiter"""
        try:
            # Get default branding first
            response = db.service_client.table("company_branding").select("*").eq(
                "recruiter_id", str(recruiter_id)
            ).eq("is_default", True).execute()
            
            if response.data:
                return response.data[0]
            
            # Fall back to any branding
            response = db.service_client.table("company_branding").select("*").eq(
                "recruiter_id", str(recruiter_id)
            ).limit(1).execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Error fetching company branding", error=str(e), recruiter_id=str(recruiter_id))
            return None
    
    @staticmethod
    def render_template(template_html: str, variables: Dict[str, Any]) -> str:
        """Render email template with variables"""
        try:
            template = Template(template_html)
            return template.render(**variables)
        except Exception as e:
            logger.error("Error rendering email template", error=str(e))
            raise
    
    @staticmethod
    def wrap_with_letterhead(
        body_html: str,
        branding: Optional[Dict[str, Any]] = None
    ) -> str:
        """Wrap email body with company letterhead/branding"""
        
        if not branding:
            # Default minimal letterhead
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                {body_html}
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">This email was sent from {settings.email_from_name}</p>
            </body>
            </html>
            """
        
        # Extract branding values
        primary_color = branding.get("primary_color", "#2563eb")
        secondary_color = branding.get("secondary_color", "#1e40af")
        company_name = branding.get("company_name", "")
        company_logo_url = branding.get("company_logo_url", "")
        company_website = branding.get("company_website", "")
        company_address = branding.get("company_address", "")
        company_phone = branding.get("company_phone", "")
        company_email = branding.get("company_email", "")
        sender_name = branding.get("sender_name", "")
        sender_title = branding.get("sender_title", "")
        email_signature = branding.get("email_signature", "")
        header_html = branding.get("letterhead_header_html", "")
        footer_html = branding.get("letterhead_footer_html", "")
        bg_color = branding.get("letterhead_background_color", "#ffffff")
        
        # Build header
        header = header_html if header_html else f"""
        <div style="background-color: {primary_color}; padding: 20px; text-align: center; margin-bottom: 20px;">
            {f'<img src="{company_logo_url}" alt="{company_name}" style="max-height: 60px; margin-bottom: 10px;">' if company_logo_url else ''}
            <h1 style="color: white; margin: 0; font-size: 24px;">{company_name}</h1>
        </div>
        """
        
        # Build footer
        footer = footer_html if footer_html else f"""
        <div style="background-color: #f5f5f5; padding: 20px; margin-top: 30px; border-top: 3px solid {primary_color};">
            {email_signature if email_signature else f'''
            <p style="margin: 0 0 10px 0; font-weight: bold;">{sender_name}</p>
            {f'<p style="margin: 0 0 10px 0; color: #666;">{sender_title}</p>' if sender_title else ''}
            {f'<p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">{company_name}</p>' if company_name else ''}
            {f'<p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">{company_address}</p>' if company_address else ''}
            {f'<p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">Phone: {company_phone}</p>' if company_phone else ''}
            {f'<p style="margin: 0; font-size: 12px; color: #666;">Email: {company_email}</p>' if company_email else ''}
            {f'<p style="margin: 10px 0 0 0; font-size: 12px;"><a href="{company_website}" style="color: {primary_color};">{company_website}</a></p>' if company_website else ''}
            '''}
        </div>
        """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: {bg_color}; margin: 0; padding: 0;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: {bg_color};">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <tr>
                                <td>
                                    {header}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 30px;">
                                    {body_html}
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    {footer}
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    @staticmethod
    async def send_email(
        recruiter_id: UUID,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        template_id: Optional[UUID] = None,
        branding_id: Optional[UUID] = None,
        candidate_id: Optional[UUID] = None,
        job_description_id: Optional[UUID] = None,
        interview_ticket_id: Optional[UUID] = None,
        application_id: Optional[UUID] = None,
        recipient_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email with branding and template support
        
        Returns:
            Dictionary with email sending result
        """
        if not resend_client:
            raise Exception("Email service not configured. Please set RESEND_API_KEY.")
        
        try:
            # Get branding if not provided
            branding = None
            if branding_id:
                response = db.service_client.table("company_branding").select("*").eq("id", str(branding_id)).execute()
                branding = response.data[0] if response.data else None
            else:
                branding = await EmailService.get_company_branding(recruiter_id)
            
            # Wrap body with letterhead
            final_html = EmailService.wrap_with_letterhead(body_html, branding)
            
            # Generate plain text version if not provided
            if not body_text:
                # Simple HTML to text conversion (basic)
                import re
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ')
            
            # Send via Resend
            params = {
                "from": f"{settings.email_from_name} <{settings.email_from_address}>",
                "to": [recipient_email],
                "subject": subject,
                "html": final_html,
                "text": body_text,
            }
            
            if settings.email_reply_to:
                params["reply_to"] = settings.email_reply_to
            
            if recipient_name:
                params["to"] = [f"{recipient_name} <{recipient_email}>"]
            
            # Add attachments if provided
            if attachments:
                params["attachments"] = attachments
            
            result = resend.Emails.send(params)
            
            external_email_id = result.get("id") if result else None
            
            # Save to sent_emails table
            sent_email_data = {
                "recruiter_id": str(recruiter_id),
                "template_id": str(template_id) if template_id else None,
                "branding_id": str(branding_id) if branding_id else (str(branding["id"]) if branding else None),
                "recipient_email": recipient_email,
                "recipient_name": recipient_name,
                "candidate_id": str(candidate_id) if candidate_id else None,
                "subject": subject,
                "body_html": final_html,
                "body_text": body_text,
                "status": "sent" if external_email_id else "failed",
                "external_email_id": external_email_id,
                "job_description_id": str(job_description_id) if job_description_id else None,
                "interview_ticket_id": str(interview_ticket_id) if interview_ticket_id else None,
                "application_id": str(application_id) if application_id else None,
                "sent_at": datetime.utcnow().isoformat() if external_email_id else None,
            }
            
            response = db.service_client.table("sent_emails").insert(sent_email_data).execute()
            
            logger.info(
                "Email sent",
                email_id=response.data[0]["id"] if response.data else None,
                recipient=recipient_email,
                external_id=external_email_id
            )
            
            return {
                "success": True,
                "email_id": response.data[0]["id"] if response.data else None,
                "external_email_id": external_email_id,
                "status": "sent" if external_email_id else "failed"
            }
            
        except Exception as e:
            logger.error("Error sending email", error=str(e), recipient=recipient_email)
            
            # Save failed email attempt
            try:
                sent_email_data = {
                    "recruiter_id": str(recruiter_id),
                    "template_id": str(template_id) if template_id else None,
                    "recipient_email": recipient_email,
                    "recipient_name": recipient_name,
                    "candidate_id": str(candidate_id) if candidate_id else None,
                    "subject": subject,
                    "body_html": body_html,
                    "body_text": body_text,
                    "status": "failed",
                    "error_message": str(e),
                    "job_description_id": str(job_description_id) if job_description_id else None,
                    "interview_ticket_id": str(interview_ticket_id) if interview_ticket_id else None,
                    "application_id": str(application_id) if application_id else None,
                }
                db.service_client.table("sent_emails").insert(sent_email_data).execute()
            except:
                pass
            
            raise
    
    @staticmethod
    async def send_ticket_email(
        recruiter_id: UUID,
        candidate_id: UUID,
        ticket_code: str,
        interview_link: str,
        job_title: str,
        candidate_name: str,
        candidate_email: str,
        ticket_id: UUID,
        job_description_id: UUID,
        expires_in_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send interview ticket email to candidate"""
        
        # Default ticket email template
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
        
        # Get branding for variables
        branding = await EmailService.get_company_branding(recruiter_id)
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        variables = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "ticket_code": ticket_code,
            "interview_link": interview_link,
            "primary_color": primary_color,
            "expires_in_hours": expires_in_hours,
        }
        
        body_html = EmailService.render_template(template_html, variables)
        subject = f"Interview Invitation: {job_title}"
        
        return await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            body_html=body_html,
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            interview_ticket_id=ticket_id,
        )
    
    @staticmethod
    async def send_offer_letter_email(
        recruiter_id: UUID,
        candidate_id: UUID,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        job_description_id: UUID,
        offer_letter_url: str,
        offer_letter_content: Optional[bytes] = None,
        offer_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send offer letter email to candidate with attached offer letter PDF
        
        Args:
            recruiter_id: Recruiter ID
            candidate_id: Candidate ID
            candidate_email: Candidate email address
            candidate_name: Candidate name
            job_title: Job title
            job_description_id: Job description ID
            offer_letter_url: URL to the offer letter PDF (Supabase Storage)
            offer_details: Optional offer details (salary, start date, etc.)
        
        Returns:
            Email sending result
        """
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
        
        # Get branding
        branding = await EmailService.get_company_branding(recruiter_id)
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        variables = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "primary_color": primary_color,
            "offer_letter_url": offer_letter_url,
            "offer_details": offer_details or {},
        }
        
        body_html = EmailService.render_template(template_html, variables)
        subject = f"Job Offer: {job_title}"
        
        # Send email with attachment
        if not resend_client:
            raise Exception("Email service not configured. Please set RESEND_API_KEY.")
        
        try:
            # Get branding for letterhead
            final_html = EmailService.wrap_with_letterhead(body_html, branding)
            
            # Generate plain text version
            import re
            body_text = re.sub(r'<[^>]+>', '', body_html)
            body_text = body_text.replace('&nbsp;', ' ')
            
            # Get offer letter PDF content for attachment
            if offer_letter_content:
                pdf_content = offer_letter_content
            else:
                # Download from URL if content not provided
                async with httpx.AsyncClient() as client:
                    pdf_response = await client.get(offer_letter_url)
                    pdf_content = pdf_response.content
            
            # Convert to base64 for Resend
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Send via Resend with attachment
            params = {
                "from": f"{settings.email_from_name} <{settings.email_from_address}>",
                "to": [f"{candidate_name} <{candidate_email}>"],
                "subject": subject,
                "html": final_html,
                "text": body_text,
                "attachments": [
                    {
                        "filename": f"Offer_Letter_{job_title.replace(' ', '_')}.pdf",
                        "content": pdf_base64,
                    }
                ]
            }
            
            if settings.email_reply_to:
                params["reply_to"] = settings.email_reply_to
            
            result = resend.Emails.send(params)
            external_email_id = result.get("id") if result else None
            
            # Save to sent_emails table
            from datetime import datetime
            sent_email_data = {
                "recruiter_id": str(recruiter_id),
                "recipient_email": candidate_email,
                "recipient_name": candidate_name,
                "candidate_id": str(candidate_id),
                "subject": subject,
                "body_html": final_html,
                "body_text": body_text,
                "status": "sent" if external_email_id else "failed",
                "external_email_id": external_email_id,
                "job_description_id": str(job_description_id),
                "sent_at": datetime.utcnow().isoformat() if external_email_id else None,
            }
            
            response = db.service_client.table("sent_emails").insert(sent_email_data).execute()
            
            logger.info(
                "Offer letter email sent",
                email_id=response.data[0]["id"] if response.data else None,
                recipient=candidate_email,
                external_id=external_email_id
            )
            
            return {
                "success": True,
                "email_id": response.data[0]["id"] if response.data else None,
                "external_email_id": external_email_id,
                "status": "sent" if external_email_id else "failed"
            }
            
        except Exception as e:
            logger.error("Error sending offer letter email", error=str(e), recipient=candidate_email)
            raise
    
    @staticmethod
    def extract_first_name(full_name: Optional[str], email: Optional[str] = None) -> str:
        """Extract first name from full name or email"""
        if full_name:
            # Split by space and take first part
            first_name = full_name.split()[0] if full_name.split() else ""
            if first_name:
                return first_name
        
        # Fallback to email username if no full name
        if email:
            return email.split("@")[0].split(".")[0].capitalize()
        
        return "Candidate"
    
    @staticmethod
    def substitute_template_variables(
        template_html: str,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        additional_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Substitute template variables in email template
        
        Available variables:
        - {{first_name}} - Candidate's first name
        - {{full_name}} - Candidate's full name
        - {{email}} - Candidate's email
        - {{job_title}} - Job title
        - {{job_description_id}} - Job ID
        - {{salary}} - Salary (if provided)
        - {{start_date}} - Start date (if provided)
        - {{location}} - Location (if provided)
        - {{employment_type}} - Employment type (if provided)
        - Custom variables from additional_vars
        """
        first_name = EmailService.extract_first_name(
            candidate.get("full_name"),
            candidate.get("email")
        )
        
        variables = {
            "first_name": first_name,
            "full_name": candidate.get("full_name", "Candidate"),
            "email": candidate.get("email", ""),
            "job_title": job.get("title", "Position"),
            "job_description_id": job.get("id", ""),
        }
        
        # Add additional variables
        if additional_vars:
            variables.update(additional_vars)
        
        # Replace variables in template
        result = template_html
        for key, value in variables.items():
            if value is not None:
                result = result.replace(f"{{{{{key}}}}}", str(value))
                result = result.replace(f"{{{{ {key} }}}}", str(value))  # Handle spaces
        
        return result
    
    @staticmethod
    async def send_offer_letter_email(
        recruiter_id: UUID,
        candidate_id: UUID,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        job_description_id: UUID,
        offer_letter_pdf_url: str,
        offer_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send offer letter email with PDF attachment
        
        Args:
            recruiter_id: Recruiter ID
            candidate_id: Candidate ID
            candidate_email: Candidate email
            candidate_name: Candidate name
            job_title: Job title
            job_description_id: Job description ID
            offer_letter_pdf_url: URL to the PDF offer letter (Supabase Storage or external)
            offer_details: Optional offer details (salary, start date, etc.)
        
        Returns:
            Email sending result
        """
        # Default offer letter email template
        template_html = """
        <div style="max-width: 600px; margin: 0 auto;">
            <h2 style="color: {{primary_color}};">Job Offer - {{job_title}}</h2>
            <p>Dear {{candidate_name}},</p>
            <p>We are delighted to offer you the position of <strong>{{job_title}}</strong> at our company.</p>
            
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
            </div>
            {% endif %}
            
            <p>Please find attached the formal offer letter with all the details. We look forward to welcoming you to our team!</p>
            
            <p>If you have any questions or need clarification on any aspect of this offer, please don't hesitate to reach out.</p>
            
            <p>We hope you will accept this offer and look forward to working with you.</p>
            <p>Best regards,<br>The Hiring Team</p>
        </div>
        """
        
        # Get branding
        branding = await EmailService.get_company_branding(recruiter_id)
        primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
        
        variables = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "primary_color": primary_color,
            "offer_details": offer_details or {},
        }
        
        body_html = EmailService.render_template(template_html, variables)
        subject = f"Job Offer: {job_title}"
        
        # Prepare attachment
        attachments = [{
            "filename": f"Offer_Letter_{job_title.replace(' ', '_')}.pdf",
            "path": offer_letter_pdf_url,  # Resend supports URLs
        }]
        
        return await EmailService.send_email(
            recruiter_id=recruiter_id,
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            body_html=body_html,
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            attachments=attachments,
        )

