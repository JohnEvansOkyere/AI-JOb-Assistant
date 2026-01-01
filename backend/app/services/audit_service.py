"""
Audit Service
Comprehensive audit logging for compliance and tracking
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import Request
from app.database import db
import structlog

logger = structlog.get_logger()


class AuditService:
    """Service for logging audit events"""

    @staticmethod
    async def log_user_action(
        user_id: UUID,
        action_type: str,
        resource_type: str,
        resource_id: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log a user action for audit trail
        
        Args:
            user_id: User who performed the action
            action_type: Type of action (view, create, update, delete, etc.)
            resource_type: Type of resource (candidate, interview, report, etc.)
            resource_id: ID of the resource
            description: Human-readable description
            metadata: Additional metadata (old_values, new_values, etc.)
            request: FastAPI request object (for IP/user agent extraction)
        """
        try:
            ip_address = None
            user_agent = None
            
            if request:
                # Extract IP address
                if request.client:
                    ip_address = request.client.host
                # Check for forwarded headers (if behind proxy)
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    ip_address = forwarded_for.split(",")[0].strip()
                
                # Extract user agent
                user_agent = request.headers.get("User-Agent")

            log_data = {
                "user_id": str(user_id),
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "metadata": metadata or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat()
            }
            
            db.service_client.table("audit_logs").insert(log_data).execute()
            
        except Exception as e:
            logger.warning("Failed to log user action", error=str(e), action_type=action_type)
            # Don't fail the main operation if logging fails

    @staticmethod
    async def log_candidate_view(
        user_id: UUID,
        candidate_id: UUID,
        request: Optional[Request] = None
    ):
        """Log when a user views a candidate profile"""
        await AuditService.log_user_action(
            user_id=user_id,
            action_type="view",
            resource_type="candidate",
            resource_id=str(candidate_id),
            description=f"Viewed candidate profile",
            metadata={"candidate_id": str(candidate_id)},
            request=request
        )

    @staticmethod
    async def log_report_view(
        user_id: UUID,
        report_type: str,  # "interview_analysis", "cv_screening", "detailed_cv_analysis"
        report_id: UUID,
        candidate_id: Optional[UUID] = None,
        interview_id: Optional[UUID] = None,
        application_id: Optional[UUID] = None,
        request: Optional[Request] = None
    ):
        """Log when a user views a report"""
        metadata = {
            "report_type": report_type,
            "report_id": str(report_id)
        }
        if candidate_id:
            metadata["candidate_id"] = str(candidate_id)
        if interview_id:
            metadata["interview_id"] = str(interview_id)
        if application_id:
            metadata["application_id"] = str(application_id)

        await AuditService.log_user_action(
            user_id=user_id,
            action_type="view",
            resource_type="report",
            resource_id=str(report_id),
            description=f"Viewed {report_type} report",
            metadata=metadata,
            request=request
        )

    @staticmethod
    async def log_status_change(
        user_id: UUID,
        resource_type: str,  # "candidate", "application", "interview"
        resource_id: UUID,
        old_status: Optional[str],
        new_status: str,
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log when a status is changed"""
        metadata = {
            "old_status": old_status,
            "new_status": new_status
        }
        if reason:
            metadata["reason"] = reason

        await AuditService.log_user_action(
            user_id=user_id,
            action_type="status_change",
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=f"Changed {resource_type} status from '{old_status}' to '{new_status}'",
            metadata=metadata,
            request=request
        )

    @staticmethod
    async def log_ticket_issuance(
        user_id: UUID,
        ticket_id: UUID,
        candidate_id: UUID,
        job_id: UUID,
        request: Optional[Request] = None
    ):
        """Log when an interview ticket is issued"""
        await AuditService.log_user_action(
            user_id=user_id,
            action_type="create",
            resource_type="ticket",
            resource_id=str(ticket_id),
            description="Issued interview ticket to candidate",
            metadata={
                "ticket_id": str(ticket_id),
                "candidate_id": str(candidate_id),
                "job_id": str(job_id)
            },
            request=request
        )

    @staticmethod
    async def log_ai_override(
        user_id: UUID,
        resource_type: str,  # "candidate", "application"
        resource_id: UUID,
        ai_recommendation: str,
        override_decision: str,
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log when a user overrides an AI recommendation"""
        metadata = {
            "ai_recommendation": ai_recommendation,
            "override_decision": override_decision
        }
        if reason:
            metadata["reason"] = reason

        await AuditService.log_user_action(
            user_id=user_id,
            action_type="ai_override",
            resource_type=resource_type,
            resource_id=str(resource_id),
            description=f"Overrode AI recommendation '{ai_recommendation}' with '{override_decision}'",
            metadata=metadata,
            request=request
        )

    @staticmethod
    async def log_document_download(
        user_id: UUID,
        document_type: str,  # "cv", "transcript", "report"
        document_id: UUID,
        candidate_id: Optional[UUID] = None,
        request: Optional[Request] = None
    ):
        """Log when a document is downloaded"""
        metadata = {
            "document_type": document_type,
            "document_id": str(document_id)
        }
        if candidate_id:
            metadata["candidate_id"] = str(candidate_id)

        await AuditService.log_user_action(
            user_id=user_id,
            action_type="download",
            resource_type="document",
            resource_id=str(document_id),
            description=f"Downloaded {document_type}",
            metadata=metadata,
            request=request
        )

    @staticmethod
    async def get_audit_logs(
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs with filtering
        
        Args:
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            action_type: Filter by action type
            limit: Maximum number of logs
            offset: Pagination offset
            
        Returns:
            List of audit log entries
        """
        try:
            query = db.service_client.table("audit_logs").select("*")
            
            if user_id:
                query = query.eq("user_id", str(user_id))
            if resource_type:
                query = query.eq("resource_type", resource_type)
            if resource_id:
                query = query.eq("resource_id", resource_id)
            if action_type:
                query = query.eq("action_type", action_type)
            
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error("Error fetching audit logs", error=str(e))
            return []

