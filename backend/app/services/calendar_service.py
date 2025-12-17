"""
Calendar Service
Handles calendar integration (Google Calendar, Outlook, etc.) and event management
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
from app.database import db
from app.services.email_service import EmailService
import structlog

logger = structlog.get_logger()


class CalendarService:
    """Service for managing calendar events and integrations"""
    
    @staticmethod
    async def create_calendar_event(
        recruiter_id: UUID,
        candidate_id: UUID,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_virtual: bool = False,
        video_link: Optional[str] = None,
        job_description_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        timezone: str = "UTC",
        attendee_emails: Optional[List[str]] = None,
        attendee_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a calendar event (interview booking)
        
        Returns:
            Created calendar event
        """
        try:
            event_data = {
                "recruiter_id": str(recruiter_id),
                "candidate_id": str(candidate_id),
                "job_description_id": str(job_description_id) if job_description_id else None,
                "interview_id": str(interview_id) if interview_id else None,
                "title": title,
                "description": description or "",
                "location": location or "",
                "is_virtual": is_virtual,
                "video_link": video_link,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "timezone": timezone,
                "status": "scheduled",
                "attendee_emails": attendee_emails or [],
                "attendee_names": attendee_names or [],
            }
            
            response = db.service_client.table("calendar_events").insert(event_data).execute()
            
            if not response.data:
                raise Exception("Failed to create calendar event")
            
            event = response.data[0]
            
            # Send email notification to candidate
            try:
                await CalendarService._send_event_invitation_email(
                    recruiter_id=recruiter_id,
                    event=event
                )
            except Exception as email_error:
                logger.warning("Failed to send calendar event email", error=str(email_error), event_id=event["id"])
                # Don't fail event creation if email fails
            
            # Try to sync with external calendar if integration exists
            await CalendarService.sync_event_to_external_calendar(
                recruiter_id=recruiter_id,
                event_id=UUID(event["id"])
            )
            
            logger.info("Calendar event created", event_id=event["id"], recruiter_id=str(recruiter_id))
            return event
            
        except Exception as e:
            logger.error("Error creating calendar event", error=str(e))
            raise
    
    @staticmethod
    async def _send_event_invitation_email(
        recruiter_id: UUID,
        event: Dict[str, Any]
    ) -> None:
        """Send calendar event invitation email to candidate"""
        try:
            # Get candidate details
            candidate_response = db.service_client.table("candidates").select(
                "email, full_name"
            ).eq("id", event["candidate_id"]).execute()
            
            if not candidate_response.data:
                logger.warning("Candidate not found for calendar event", candidate_id=event["candidate_id"])
                return
            
            candidate = candidate_response.data[0]
            candidate_email = candidate.get("email")
            candidate_name = candidate.get("full_name", "Candidate")
            
            if not candidate_email:
                logger.warning("Candidate email not found", candidate_id=event["candidate_id"])
                return
            
            # Get job title if job_description_id exists
            job_title = None
            if event.get("job_description_id"):
                job_response = db.service_client.table("job_descriptions").select("title").eq(
                    "id", event["job_description_id"]
                ).execute()
                if job_response.data:
                    job_title = job_response.data[0].get("title")
            
            # Format event details
            start_dt = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00'))
            
            # Format date and time
            start_str = start_dt.strftime("%B %d, %Y at %I:%M %p")
            end_str = end_dt.strftime("%I:%M %p")
            
            # Create email template using Jinja2
            template_html = """
            <div style="max-width: 600px; margin: 0 auto;">
                <h2 style="color: {{primary_color}};">Calendar Event Invitation</h2>
                <p>Dear {{candidate_name}},</p>
                <p>You have been invited to a calendar event:</p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f2937;">{{event_title}}</h3>
                    
                    <p><strong>📅 Date & Time:</strong><br>
                    {{start_time}} - {{end_time}}</p>
                    
                    {% if location %}
                    <p><strong>📍 Location:</strong><br>{{location}}</p>
                    {% endif %}
                    
                    {% if video_link %}
                    <p><strong>💻 Video Link:</strong><br><a href="{{video_link}}" style="color: {{primary_color}};">{{video_link}}</a></p>
                    {% endif %}
                    
                    {% if description %}
                    <p><strong>📝 Description:</strong><br>{{description}}</p>
                    {% endif %}
                </div>
                
                {% if job_title %}
                <p style="margin-top: 20px;">This event is related to the <strong>{{job_title}}</strong> position.</p>
                {% endif %}
                
                <p>Please make sure to add this event to your calendar. If you have any questions or need to reschedule, please don't hesitate to reach out.</p>
                
                <p>Best regards,<br>The Hiring Team</p>
            </div>
            """
            
            # Get branding for primary color
            branding = await EmailService.get_company_branding(recruiter_id)
            primary_color = branding.get("primary_color", "#2563eb") if branding else "#2563eb"
            
            # Render template
            template_vars = {
                "candidate_name": candidate_name,
                "event_title": event.get('title', 'Event'),
                "start_time": start_str,
                "end_time": end_str,
                "location": event.get("location", ""),
                "video_link": event.get("video_link", ""),
                "description": event.get("description", ""),
                "job_title": job_title,
                "primary_color": primary_color,
            }
            
            body_html = EmailService.render_template(template_html, template_vars)
            subject = f"Calendar Event Invitation: {event.get('title', 'Event')}"
            
            # Send email
            await EmailService.send_email(
                recruiter_id=recruiter_id,
                recipient_email=candidate_email,
                recipient_name=candidate_name,
                subject=subject,
                body_html=body_html,
                candidate_id=UUID(event["candidate_id"]),
                job_description_id=UUID(event["job_description_id"]) if event.get("job_description_id") else None,
            )
            
            logger.info("Calendar event invitation email sent", event_id=event["id"], recipient=candidate_email)
            
        except Exception as e:
            logger.error("Error sending calendar event invitation email", error=str(e), event_id=event.get("id"))
            raise
    
    @staticmethod
    async def sync_event_to_external_calendar(
        recruiter_id: UUID,
        event_id: UUID
    ) -> bool:
        """
        Sync calendar event to external calendar (Google Calendar, etc.)
        
        Returns:
            True if synced successfully
        """
        try:
            # Get the event
            event_response = db.service_client.table("calendar_events").select("*").eq("id", str(event_id)).execute()
            if not event_response.data:
                return False
            
            event = event_response.data[0]
            
            # Get active calendar integrations
            integrations_response = db.service_client.table("calendar_integrations").select("*").eq(
                "recruiter_id", str(recruiter_id)
            ).eq("is_active", True).eq("auto_sync", True).execute()
            
            if not integrations_response.data:
                logger.info("No active calendar integrations found", recruiter_id=str(recruiter_id))
                return False
            
            # Sync to each active integration
            for integration in integrations_response.data:
                provider = integration.get("provider")
                
                if provider == "google":
                    success = await CalendarService._sync_to_google_calendar(event, integration)
                elif provider == "outlook":
                    # TODO: Implement Outlook sync
                    logger.warning("Outlook calendar sync not yet implemented")
                    success = False
                else:
                    logger.warning("Unknown calendar provider", provider=provider)
                    success = False
                
                if success:
                    # Update event with external calendar ID
                    db.service_client.table("calendar_events").update({
                        "external_calendar_id": integration.get("external_calendar_id"),
                        "external_calendar_provider": provider,
                        "calendar_sync_status": "synced"
                    }).eq("id", str(event_id)).execute()
            
            return True
            
        except Exception as e:
            logger.error("Error syncing to external calendar", error=str(e), event_id=str(event_id))
            # Update sync status to failed
            try:
                db.service_client.table("calendar_events").update({
                    "calendar_sync_status": "failed"
                }).eq("id", str(event_id)).execute()
            except:
                pass
            return False
    
    @staticmethod
    async def _sync_to_google_calendar(
        event: Dict[str, Any],
        integration: Dict[str, Any]
    ) -> bool:
        """
        Sync event to Google Calendar
        
        Note: This requires Google Calendar API setup and OAuth tokens
        For now, this is a placeholder that logs the intent
        """
        try:
            # TODO: Implement actual Google Calendar API integration
            # This requires:
            # 1. OAuth token refresh
            # 2. Google Calendar API client
            # 3. Event creation via API
            
            logger.info(
                "Google Calendar sync requested",
                event_id=event.get("id"),
                provider_account=integration.get("provider_account_email")
            )
            
            # Placeholder - actual implementation would use google-api-python-client
            # from google.oauth2.credentials import Credentials
            # from googleapiclient.discovery import build
            # 
            # creds = Credentials.from_authorized_user_info(integration)
            # service = build('calendar', 'v3', credentials=creds)
            # 
            # calendar_event = {
            #     'summary': event['title'],
            #     'description': event.get('description', ''),
            #     'start': {'dateTime': event['start_time'], 'timeZone': event.get('timezone', 'UTC')},
            #     'end': {'dateTime': event['end_time'], 'timeZone': event.get('timezone', 'UTC')},
            #     'location': event.get('location', ''),
            #     'attendees': [{'email': email} for email in event.get('attendee_emails', [])],
            # }
            # 
            # created_event = service.events().insert(calendarId='primary', body=calendar_event).execute()
            # return created_event.get('id')
            
            return False  # Not implemented yet
            
        except Exception as e:
            logger.error("Error syncing to Google Calendar", error=str(e))
            return False
    
    @staticmethod
    async def get_calendar_events(
        recruiter_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        candidate_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get calendar events for a recruiter"""
        try:
            query = db.service_client.table("calendar_events").select("*").eq("recruiter_id", str(recruiter_id))
            
            if start_date:
                query = query.gte("start_time", start_date.isoformat())
            if end_date:
                query = query.lte("end_time", end_date.isoformat())
            if candidate_id:
                query = query.eq("candidate_id", str(candidate_id))
            
            response = query.order("start_time").execute()
            return response.data or []
            
        except Exception as e:
            logger.error("Error fetching calendar events", error=str(e))
            raise
    
    @staticmethod
    async def update_calendar_event(
        event_id: UUID,
        recruiter_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a calendar event"""
        try:
            # Verify ownership
            event_response = db.service_client.table("calendar_events").select("recruiter_id").eq("id", str(event_id)).execute()
            if not event_response.data:
                raise Exception("Event not found")
            
            if event_response.data[0]["recruiter_id"] != str(recruiter_id):
                raise Exception("Not authorized to update this event")
            
            # Update event
            response = db.service_client.table("calendar_events").update(updates).eq("id", str(event_id)).execute()
            
            if not response.data:
                raise Exception("Failed to update event")
            
            # Re-sync if needed
            if any(key in updates for key in ["start_time", "end_time", "title", "description", "location"]):
                await CalendarService.sync_event_to_external_calendar(recruiter_id, event_id)
            
            return response.data[0]
            
        except Exception as e:
            logger.error("Error updating calendar event", error=str(e))
            raise
    
    @staticmethod
    async def delete_calendar_event(
        event_id: UUID,
        recruiter_id: UUID
    ) -> bool:
        """Delete a calendar event"""
        try:
            # Verify ownership
            event_response = db.service_client.table("calendar_events").select("recruiter_id, external_calendar_id, external_calendar_provider").eq("id", str(event_id)).execute()
            if not event_response.data:
                raise Exception("Event not found")
            
            event = event_response.data[0]
            if event["recruiter_id"] != str(recruiter_id):
                raise Exception("Not authorized to delete this event")
            
            # TODO: Delete from external calendar if synced
            # if event.get("external_calendar_id"):
            #     await CalendarService._delete_from_external_calendar(event, integration)
            
            # Delete from database
            db.service_client.table("calendar_events").delete().eq("id", str(event_id)).execute()
            
            logger.info("Calendar event deleted", event_id=str(event_id))
            return True
            
        except Exception as e:
            logger.error("Error deleting calendar event", error=str(e))
            raise

