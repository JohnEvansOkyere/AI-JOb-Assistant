"""
Calendar API Routes
Handles calendar events, bookings, and Google Calendar integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.common import Response
from app.services.calendar_service import CalendarService
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    request: Request,
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
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a calendar event (interview booking)
    
    Returns:
        Created calendar event
    """
    try:
        event = await CalendarService.create_calendar_event(
            recruiter_id=recruiter_id,
            candidate_id=candidate_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            is_virtual=is_virtual,
            video_link=video_link,
            job_description_id=job_description_id,
            interview_id=interview_id,
            timezone=timezone,
            attendee_emails=attendee_emails or [],
            attendee_names=attendee_names or [],
        )
        
        return Response(
            success=True,
            message="Calendar event created successfully",
            data=event
        )
    except Exception as e:
        logger.error("Error creating calendar event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create calendar event: {str(e)}"
        )


@router.get("/events")
async def get_calendar_events(
    request: Request,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    candidate_id: Optional[UUID] = None,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get calendar events
    
    Returns:
        List of calendar events
    """
    try:
        events = await CalendarService.get_calendar_events(
            recruiter_id=recruiter_id,
            start_date=start_date,
            end_date=end_date,
            candidate_id=candidate_id,
        )
        
        return Response(
            success=True,
            message="Calendar events retrieved successfully",
            data=events
        )
    except Exception as e:
        logger.error("Error fetching calendar events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch calendar events: {str(e)}"
        )


@router.put("/events/{event_id}")
async def update_calendar_event(
    request: Request,
    event_id: UUID,
    title: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update a calendar event
    
    Returns:
        Updated calendar event
    """
    try:
        updates = {}
        if title is not None:
            updates["title"] = title
        if start_time is not None:
            updates["start_time"] = start_time.isoformat()
        if end_time is not None:
            updates["end_time"] = end_time.isoformat()
        if description is not None:
            updates["description"] = description
        if location is not None:
            updates["location"] = location
        if status is not None:
            updates["status"] = status
        
        event = await CalendarService.update_calendar_event(
            event_id=event_id,
            recruiter_id=recruiter_id,
            updates=updates
        )
        
        return Response(
            success=True,
            message="Calendar event updated successfully",
            data=event
        )
    except Exception as e:
        logger.error("Error updating calendar event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calendar event: {str(e)}"
        )


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    request: Request,
    event_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a calendar event
    
    Returns:
        Deletion confirmation
    """
    try:
        success = await CalendarService.delete_calendar_event(
            event_id=event_id,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Calendar event deleted successfully"
        )
    except Exception as e:
        logger.error("Error deleting calendar event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete calendar event: {str(e)}"
        )

