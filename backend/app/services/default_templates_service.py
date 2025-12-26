"""
Default Email Templates Service
Creates professional default email templates for new recruiters
"""

from typing import Dict, Any, List
from uuid import UUID
from app.database import db
import structlog

logger = structlog.get_logger()


class DefaultTemplatesService:
    """Service for creating default email templates"""
    
    # All template types that need defaults
    TEMPLATE_TYPES = [
        "application_received",
        "interview_invitation",
        "cv_rejection",
        "interview_rejection",
        "acceptance",
        "rejection",
        "offer_letter",
    ]
    
    @staticmethod
    def get_default_templates() -> Dict[str, Dict[str, Any]]:
        """
        Get default template definitions for all template types
        
        Returns:
            Dictionary mapping template_type to template data
        """
        return {
            "application_received": {
                "name": "Default: Application Received Confirmation",
                "subject": "Application Received: {{job_title}} - {{company_name}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
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
</div>""",
                "body_text": """Dear {{candidate_name}},

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
This is an automated confirmation email. Please do not reply to this message.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{application_id}}"]
            },
            
            "interview_invitation": {
                "name": "Default: Interview Invitation",
                "subject": "Interview Invitation: {{job_title}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Interview Invitation</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>. We were impressed with your application and would like to invite you to complete an AI-powered interview.</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
            <h3 style="margin-top: 0; color: #1e40af;">Your Interview Ticket Code:</h3>
            <p style="font-size: 28px; font-weight: bold; text-align: center; letter-spacing: 3px; color: {{primary_color}}; margin: 10px 0;">{{ticket_code}}</p>
        </div>
        
        <p style="font-size: 16px;"><strong>To start your interview:</strong></p>
        <ol style="font-size: 15px; color: #4b5563;">
            <li>Click the link below or copy it into your browser</li>
            <li>Enter your ticket code when prompted</li>
            <li>Complete the interview at your convenience</li>
        </ol>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{interview_link}}" style="background-color: {{primary_color}}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; font-size: 16px;">Start Interview</a>
        </div>
        
        <p style="font-size: 14px; color: #6b7280;">Or copy this link: <a href="{{interview_link}}" style="color: {{primary_color}};">{{interview_link}}</a></p>
        
        {% if expires_in_hours %}
        <div style="margin: 25px 0; padding: 15px; background-color: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <p style="margin: 0; font-size: 14px; color: #92400e; font-weight: bold;">
                ⏰ This ticket expires in {{expires_in_hours}} hours. Please complete your interview before then.
            </p>
        </div>
        {% endif %}
        
        <p style="font-size: 16px;">If you have any questions, please don't hesitate to reach out to us.</p>
        
        <p style="font-size: 16px; margin-bottom: 0;">
            Best regards,<br>
            <strong>The Hiring Team</strong><br>
            <span style="color: {{primary_color}};">{{company_name}}</span>
        </p>
    </div>
</div>""",
                "body_text": """Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}}. We were impressed with your application and would like to invite you to complete an AI-powered interview.

Your Interview Ticket Code: {{ticket_code}}

To start your interview:
1. Click this link: {{interview_link}}
2. Enter your ticket code when prompted
3. Complete the interview at your convenience

{% if expires_in_hours %}
⏰ This ticket expires in {{expires_in_hours}} hours. Please complete your interview before then.
{% endif %}

If you have any questions, please don't hesitate to reach out to us.

Best regards,
The Hiring Team
{{company_name}}""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{ticket_code}}", "{{interview_link}}", "{{expires_in_hours}}"]
            },
            
            "cv_rejection": {
                "name": "Default: CV Screening Rejection",
                "subject": "Update on Your Application: {{job_title}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
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
</div>""",
                "body_text": """Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}} and for taking the time to submit your application and CV.

We genuinely appreciate the time and effort you invested in your application. We received many qualified applications, and after careful review, we have decided to move forward with candidates whose experience more closely aligns with the specific requirements of this role.

Please know that this decision in no way diminishes the value of your qualifications and experience. We recognize that you have rich experience and valuable skills that would be an asset to many organizations.

We encourage you to continue pursuing opportunities that match your career goals. Your profile may be a perfect fit for future openings, and we hope you'll consider applying again when you see a position that aligns with your expertise.

We wish you all the best in your job search and future career endeavors.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated message. Please do not reply to this email.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{application_id}}"]
            },
            
            "interview_rejection": {
                "name": "Default: Interview Rejection",
                "subject": "Update on Your Interview: {{job_title}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
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
</div>""",
                "body_text": """Dear {{candidate_name}},

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
This is an automated message. Please do not reply to this email.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{interview_id}}", "{{interview_date}}"]
            },
            
            "acceptance": {
                "name": "Default: Job Acceptance",
                "subject": "Congratulations! Job Offer: {{job_title}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: #10b981; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">🎉 Congratulations!</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 18px; font-weight: bold; color: #10b981;">We are delighted to offer you the position of <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>!</p>
        
        <p style="font-size: 16px;">After careful consideration of all candidates, we were particularly impressed with your qualifications, experience, and the enthusiasm you demonstrated during the interview process.</p>
        
        <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #10b981;">
            <p style="margin: 0; font-size: 15px; color: #065f46;">
                <strong>We believe you will be an excellent addition to our team and look forward to welcoming you aboard.</strong>
            </p>
        </div>
        
        {% if salary %}
        <p style="font-size: 16px;"><strong>Offer Details:</strong></p>
        <ul style="font-size: 15px; color: #4b5563;">
            {% if salary %}<li><strong>Salary:</strong> {{salary}}</li>{% endif %}
            {% if start_date %}<li><strong>Start Date:</strong> {{start_date}}</li>{% endif %}
            {% if location %}<li><strong>Location:</strong> {{location}}</li>{% endif %}
            {% if employment_type %}<li><strong>Employment Type:</strong> {{employment_type}}</li>{% endif %}
        </ul>
        {% endif %}
        
        <p style="font-size: 16px;">Please review the offer details and let us know if you have any questions. We would be happy to discuss any aspects of this opportunity further.</p>
        
        <p style="font-size: 16px;">We hope you will accept this offer and join our team. Please confirm your acceptance at your earliest convenience.</p>
        
        <p style="font-size: 16px; margin-bottom: 0;">
            Best regards,<br>
            <strong>The Hiring Team</strong><br>
            <span style="color: {{primary_color}};">{{company_name}}</span>
        </p>
    </div>
</div>""",
                "body_text": """Dear {{candidate_name}},

We are delighted to offer you the position of {{job_title}} at {{company_name}}!

After careful consideration of all candidates, we were particularly impressed with your qualifications, experience, and the enthusiasm you demonstrated during the interview process.

We believe you will be an excellent addition to our team and look forward to welcoming you aboard.

{% if salary %}
Offer Details:
{% if salary %}- Salary: {{salary}}{% endif %}
{% if start_date %}- Start Date: {{start_date}}{% endif %}
{% if location %}- Location: {{location}}{% endif %}
{% if employment_type %}- Employment Type: {{employment_type}}{% endif %}
{% endif %}

Please review the offer details and let us know if you have any questions. We would be happy to discuss any aspects of this opportunity further.

We hope you will accept this offer and join our team. Please confirm your acceptance at your earliest convenience.

Best regards,
The Hiring Team
{{company_name}}""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{salary}}", "{{start_date}}", "{{location}}", "{{employment_type}}"]
            },
            
            "rejection": {
                "name": "Default: Generic Rejection",
                "subject": "Update on Your Application: {{job_title}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Update on Your Application</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
        
        <p style="font-size: 16px;">After careful consideration, we have decided to move forward with other candidates whose qualifications more closely align with our current needs.</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
            <p style="margin: 0; font-size: 15px; color: #1e40af;">
                <strong>We appreciate the time and effort you invested in your application.</strong> We encourage you to continue pursuing opportunities that match your career goals.
            </p>
        </div>
        
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
</div>""",
                "body_text": """Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}}.

After careful consideration, we have decided to move forward with other candidates whose qualifications more closely align with our current needs.

We appreciate the time and effort you invested in your application. We encourage you to continue pursuing opportunities that match your career goals.

We wish you all the best in your job search and future career endeavors.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated message. Please do not reply to this email.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}"]
            },
            
            "offer_letter": {
                "name": "Default: Job Offer Letter",
                "subject": "Job Offer: {{job_title}} - {{company_name}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Official Job Offer</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 18px; font-weight: bold;">We are pleased to extend to you an offer of employment for the position of <strong>{{job_title}}</strong> at <strong>{{company_name}}</strong>.</p>
        
        <p style="font-size: 16px;">After a thorough evaluation of all candidates, we believe your skills, experience, and professional demeanor make you an ideal fit for our team.</p>
        
        <div style="background-color: #f9fafb; padding: 25px; border-radius: 8px; margin: 25px 0; border: 2px solid {{primary_color}};">
            <h3 style="margin-top: 0; color: {{primary_color}};">Offer Details:</h3>
            <table style="width: 100%; font-size: 15px;">
                <tr><td style="padding: 8px 0; font-weight: bold; width: 40%;">Position:</td><td style="padding: 8px 0;">{{job_title}}</td></tr>
                {% if salary %}<tr><td style="padding: 8px 0; font-weight: bold;">Salary:</td><td style="padding: 8px 0;">{{salary}}</td></tr>{% endif %}
                {% if start_date %}<tr><td style="padding: 8px 0; font-weight: bold;">Start Date:</td><td style="padding: 8px 0;">{{start_date}}</td></tr>{% endif %}
                {% if location %}<tr><td style="padding: 8px 0; font-weight: bold;">Location:</td><td style="padding: 8px 0;">{{location}}</td></tr>{% endif %}
                {% if employment_type %}<tr><td style="padding: 8px 0; font-weight: bold;">Employment Type:</td><td style="padding: 8px 0;">{{employment_type}}</td></tr>{% endif %}
            </table>
        </div>
        
        <p style="font-size: 16px;">This offer is contingent upon the successful completion of any background checks or other pre-employment requirements as specified in our hiring process.</p>
        
        <p style="font-size: 16px;">Please review the terms of this offer carefully. If you have any questions or need clarification on any aspect of this offer, please do not hesitate to contact us.</p>
        
        <p style="font-size: 16px;">We hope you will accept this offer and look forward to welcoming you to our team. Please confirm your acceptance by responding to this email or contacting us directly.</p>
        
        <p style="font-size: 16px; margin-bottom: 0;">
            Best regards,<br>
            <strong>The Hiring Team</strong><br>
            <span style="color: {{primary_color}};">{{company_name}}</span>
        </p>
    </div>
</div>""",
                "body_text": """Dear {{candidate_name}},

We are pleased to extend to you an offer of employment for the position of {{job_title}} at {{company_name}}.

After a thorough evaluation of all candidates, we believe your skills, experience, and professional demeanor make you an ideal fit for our team.

Offer Details:
Position: {{job_title}}
{% if salary %}Salary: {{salary}}{% endif %}
{% if start_date %}Start Date: {{start_date}}{% endif %}
{% if location %}Location: {{location}}{% endif %}
{% if employment_type %}Employment Type: {{employment_type}}{% endif %}

This offer is contingent upon the successful completion of any background checks or other pre-employment requirements as specified in our hiring process.

Please review the terms of this offer carefully. If you have any questions or need clarification on any aspect of this offer, please do not hesitate to contact us.

We hope you will accept this offer and look forward to welcoming you to our team. Please confirm your acceptance by responding to this email or contacting us directly.

Best regards,
The Hiring Team
{{company_name}}""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}", "{{salary}}", "{{start_date}}", "{{location}}", "{{employment_type}}"]
            },
            
            "reassurance_14day": {
                "name": "Default: 14-Day Reassurance",
                "subject": "Update on Your Application: {{job_title}} - {{company_name}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Application Update</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong>.</p>
        
        <p style="font-size: 16px;">We wanted to reach out to let you know that we are still actively reviewing applications for this position. We received a significant number of qualified candidates, and we want to ensure we give each application the careful consideration it deserves.</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}};">
            <p style="margin: 0; font-size: 15px; color: #1e40af;">
                <strong>✓ Your application is still under review.</strong>
            </p>
        </div>
        
        <p style="font-size: 16px;">We appreciate your patience as we work through this process. Our hiring team is committed to making thoughtful decisions, and this takes time.</p>
        
        <p style="font-size: 16px;">We will be in touch as soon as we have an update on your application status. In the meantime, if you have any questions, please feel free to reach out to us.</p>
        
        <p style="font-size: 16px;">Thank you again for your interest in joining our team.</p>
        
        <p style="font-size: 16px; margin-bottom: 0;">
            Best regards,<br>
            <strong>The Hiring Team</strong><br>
            <span style="color: {{primary_color}};">{{company_name}}</span>
        </p>
    </div>
    
    <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
        <p style="margin: 5px 0;">This is an automated update email. Please do not reply to this message.</p>
    </div>
</div>""",
                "body_text": """Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}}.

We wanted to reach out to let you know that we are still actively reviewing applications for this position. We received a significant number of qualified candidates, and we want to ensure we give each application the careful consideration it deserves.

Your application is still under review.

We appreciate your patience as we work through this process. Our hiring team is committed to making thoughtful decisions, and this takes time.

We will be in touch as soon as we have an update on your application status. In the meantime, if you have any questions, please feel free to reach out to us.

Thank you again for your interest in joining our team.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated update email. Please do not reply to this message.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}"]
            },
            
            "auto_timeout_rejection": {
                "name": "Default: 30-Day Auto-Rejection",
                "subject": "Update on Your Application: {{job_title}} - {{company_name}}",
                "body_html": """<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: {{primary_color}}; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Application Update</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p style="font-size: 16px; margin-top: 0;">Dear {{candidate_name}},</p>
        
        <p style="font-size: 16px;">Thank you for your interest in the <strong>{{job_title}}</strong> position at <strong>{{company_name}}</strong> and for taking the time to submit your application.</p>
        
        <p style="font-size: 16px;">After careful consideration of all applications we received, we have decided to move forward with other candidates whose qualifications more closely align with our current needs for this position.</p>
        
        <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #ef4444;">
            <p style="margin: 0; font-size: 15px; color: #991b1b;">
                This decision was not an easy one, and we want you to know that we appreciate the time and effort you invested in your application.
            </p>
        </div>
        
        <p style="font-size: 16px;">We were impressed by the quality of applications we received, and yours was no exception. We encourage you to continue pursuing opportunities that match your career goals and skills.</p>
        
        <p style="font-size: 16px;">We wish you all the best in your job search and future career endeavors. Thank you again for your interest in {{company_name}}.</p>
        
        <p style="font-size: 16px; margin-bottom: 0;">
            Best regards,<br>
            <strong>The Hiring Team</strong><br>
            <span style="color: {{primary_color}};">{{company_name}}</span>
        </p>
    </div>
    
    <div style="text-align: center; margin-top: 20px; padding: 20px; color: #6b7280; font-size: 12px;">
        <p style="margin: 5px 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</div>""",
                "body_text": """Dear {{candidate_name}},

Thank you for your interest in the {{job_title}} position at {{company_name}} and for taking the time to submit your application.

After careful consideration of all applications we received, we have decided to move forward with other candidates whose qualifications more closely align with our current needs for this position.

This decision was not an easy one, and we want you to know that we appreciate the time and effort you invested in your application.

We were impressed by the quality of applications we received, and yours was no exception. We encourage you to continue pursuing opportunities that match your career goals and skills.

We wish you all the best in your job search and future career endeavors. Thank you again for your interest in {{company_name}}.

Best regards,
The Hiring Team
{{company_name}}

---
This is an automated message. Please do not reply to this email.""",
                "available_variables": ["{{candidate_name}}", "{{job_title}}", "{{company_name}}", "{{primary_color}}"]
            }
        }
    
    @staticmethod
    async def create_default_templates_for_recruiter(recruiter_id: UUID) -> List[Dict[str, Any]]:
        """
        Create default email templates for a recruiter if they don't already exist
        
        Args:
            recruiter_id: Recruiter UUID
        
        Returns:
            List of created template data
        """
        try:
            default_templates = DefaultTemplatesService.get_default_templates()
            created_templates = []
            
            # Check which templates already exist
            existing_response = db.service_client.table("email_templates").select(
                "template_type"
            ).eq("recruiter_id", str(recruiter_id)).execute()
            
            existing_types = {template["template_type"] for template in existing_response.data or []}
            
            # Create templates that don't exist
            for template_type, template_data in default_templates.items():
                if template_type not in existing_types:
                    template_record = {
                        "recruiter_id": str(recruiter_id),
                        "name": template_data["name"],
                        "subject": template_data["subject"],
                        "body_html": template_data["body_html"],
                        "body_text": template_data.get("body_text"),
                        "template_type": template_type,
                        "available_variables": template_data.get("available_variables", []),
                        "is_default": True,  # Mark as default so they're prioritized
                    }
                    
                    response = db.service_client.table("email_templates").insert(
                        template_record
                    ).execute()
                    
                    if response.data:
                        created_templates.append(response.data[0])
                        logger.info(
                            "Created default template",
                            template_type=template_type,
                            recruiter_id=str(recruiter_id),
                            template_id=response.data[0].get("id")
                        )
            
            logger.info(
                "Default templates initialization complete",
                recruiter_id=str(recruiter_id),
                created_count=len(created_templates),
                total_types=len(default_templates)
            )
            
            return created_templates
            
        except Exception as e:
            logger.error(
                "Error creating default templates",
                error=str(e),
                recruiter_id=str(recruiter_id),
                exc_info=True
            )
            # Don't raise - allow system to continue even if template creation fails
            return []

