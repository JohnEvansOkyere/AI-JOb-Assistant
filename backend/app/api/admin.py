"""
Admin API Routes
Internal admin dashboard endpoints (admin-only access)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.schemas.common import Response
from app.utils.admin_auth import get_current_admin, require_admin
from app.services.admin_service import AdminService
from app.services import admin_service_extensions
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/organizations", response_model=Response[list])
async def list_organizations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("last_activity", regex="^(org_name|last_activity|monthly_ai_cost_usd|interviews_completed|active_users)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: str = Query(None),  # Search by organization name
    status: str = Query(None, regex="^(active|paused|suspended|trial)$"),  # Filter by status
    subscription_plan: str = Query(None, regex="^(free|starter|professional|enterprise|custom)$"),  # Filter by plan
    admin_user: dict = Depends(get_current_admin)
):
    """
    List all organizations with usage metrics
    
    Args:
        limit: Maximum number of organizations to return
        offset: Offset for pagination
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        search: Search organizations by name (case-insensitive partial match)
        status: Filter by organization status
        subscription_plan: Filter by subscription plan
        admin_user: Current admin user (for authorization)
    
    Returns:
        List of organization summaries
    """
    try:
        organizations = await AdminService.get_organizations_overview(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
            status=status,
            subscription_plan=subscription_plan
        )
        
        return Response(
            success=True,
            message=f"Found {len(organizations)} organizations",
            data=organizations
        )
    except Exception as e:
        logger.error("Error listing organizations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch organizations: {str(e)}"
        )


@router.get("/organizations/{org_name}", response_model=Response[dict])
async def get_organization_detail(
    org_name: str,
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    admin_user: dict = Depends(get_current_admin)
):
    """
    Get detailed metrics for a specific organization
    
    Args:
        org_name: Organization name (company_name)
        start_date: Start date for metrics (defaults to 30 days ago)
        end_date: End date for metrics (defaults to now)
        admin_user: Current admin user (for authorization)
    
    Returns:
        Organization detail with usage metrics
    """
    try:
        # Default to 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        detail = await AdminService.get_organization_detail(
            org_name=org_name,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail["error"]
            )
        
        return Response(
            success=True,
            message="Organization details retrieved successfully",
            data=detail
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching organization detail", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch organization details: {str(e)}"
        )


@router.get("/costs", response_model=Response[dict])
async def get_cost_monitoring(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    group_by: str = Query("day", regex="^(day|month)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """
    Get cost monitoring data
    
    Args:
        start_date: Start date (defaults to 30 days ago)
        end_date: End date (defaults to now)
        group_by: Grouping period (day, month)
        admin_user: Current admin user (for authorization)
    
    Returns:
        Cost monitoring data with daily/monthly costs and top organizations
    """
    try:
        # Default to 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        cost_data = await AdminService.get_cost_monitoring(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        return Response(
            success=True,
            message="Cost monitoring data retrieved successfully",
            data=cost_data
        )
    except Exception as e:
        logger.error("Error fetching cost monitoring", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cost monitoring: {str(e)}"
        )


@router.get("/costs/organizations/{org_name}", response_model=Response[dict])
async def get_organization_cost_breakdown(
    org_name: str,
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    group_by: str = Query("feature", regex="^(feature|provider|user|day|month)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """
    Get cost breakdown for a specific organization
    
    Args:
        org_name: Organization name (company_name)
        start_date: Start date (defaults to 30 days ago)
        end_date: End date (defaults to now)
        group_by: Group by feature, provider, user, day, or month
        admin_user: Current admin user (for authorization)
    
    Returns:
        Cost breakdown by specified grouping
    """
    try:
        from app.services.admin_service import AdminService
        from app.database import db
        
        # Default to 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get organization ID
        org_response = db.service_client.table("organizations").select("id").eq("company_name", org_name).execute()
        if not org_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_name}' not found"
            )
        
        org_id = org_response.data[0]["id"]
        
        # Get all recruiters in this organization
        recruiters_response = db.service_client.table("recruiters").select("id").eq("organization_id", org_id).execute()
        recruiter_ids = [r["id"] for r in (recruiters_response.data or [])]
        
        if not recruiter_ids:
            return Response(
                success=True,
                message=f"No users found for organization '{org_name}'",
                data={
                    "organization": org_name,
                    "total_cost": 0.0,
                    "breakdown": [],
                    "summary": {}
                }
            )
        
        # Build query
        query = db.service_client.table("ai_usage_logs").select("*")
        query = query.in_("recruiter_id", recruiter_ids)
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        query = query.eq("status", "success")
        
        logs = query.execute()
        
        # Aggregate costs
        total_cost = 0.0
        breakdown = {}
        
        for log in (logs.data or []):
            cost = float(log.get("estimated_cost_usd", 0) or 0)
            total_cost += cost
            
            key = None
            if group_by == "feature":
                key = log.get("feature_name", "unknown")
            elif group_by == "provider":
                key = log.get("provider_name", "unknown")
            elif group_by == "user":
                key = log.get("recruiter_id", "unknown")
            elif group_by in ["day", "month"]:
                created_at = log.get("created_at")
                if created_at:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if group_by == "day":
                        key = dt.strftime("%Y-%m-%d")
                    else:
                        key = dt.strftime("%Y-%m")
            
            if key:
                if key not in breakdown:
                    breakdown[key] = {
                        "name": key,
                        "cost": 0.0,
                        "count": 0,
                        "tokens": 0
                    }
                breakdown[key]["cost"] += cost
                breakdown[key]["count"] += 1
                breakdown[key]["tokens"] += int(log.get("total_tokens", 0) or 0)
        
        # Convert to list and sort by cost
        breakdown_list = sorted(breakdown.values(), key=lambda x: x["cost"], reverse=True)
        
        # Get user names if grouping by user
        if group_by == "user":
            for item in breakdown_list:
                user_response = db.service_client.table("recruiters").select("full_name, email").eq("id", item["name"]).execute()
                if user_response.data:
                    user = user_response.data[0]
                    item["name"] = user.get("full_name") or user.get("email") or item["name"]
        
        return Response(
            success=True,
            message=f"Cost breakdown retrieved for organization '{org_name}'",
            data={
                "organization": org_name,
                "total_cost": round(total_cost, 4),
                "breakdown": breakdown_list,
                "summary": {
                    "total_requests": sum(item["count"] for item in breakdown_list),
                    "total_tokens": sum(item["tokens"] for item in breakdown_list),
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching organization cost breakdown", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cost breakdown: {str(e)}"
        )


@router.get("/costs/users/{user_id}", response_model=Response[dict])
async def get_user_cost_breakdown(
    user_id: str,
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    group_by: str = Query("feature", regex="^(feature|provider|day|month)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """
    Get cost breakdown for a specific user/recruiter
    
    Args:
        user_id: User/recruiter ID
        start_date: Start date (defaults to 30 days ago)
        end_date: End date (defaults to now)
        group_by: Group by feature, provider, day, or month
        admin_user: Current admin user (for authorization)
    
    Returns:
        Cost breakdown by specified grouping
    """
    try:
        from app.database import db
        
        # Default to 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Verify user exists
        user_response = db.service_client.table("recruiters").select("full_name, email, organization_id").eq("id", user_id).execute()
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found"
            )
        
        user = user_response.data[0]
        
        # Build query
        query = db.service_client.table("ai_usage_logs").select("*")
        query = query.eq("recruiter_id", user_id)
        query = query.gte("created_at", start_date.isoformat())
        query = query.lte("created_at", end_date.isoformat())
        query = query.eq("status", "success")
        
        logs = query.execute()
        
        # Aggregate costs
        total_cost = 0.0
        breakdown = {}
        
        for log in (logs.data or []):
            cost = float(log.get("estimated_cost_usd", 0) or 0)
            total_cost += cost
            
            key = None
            if group_by == "feature":
                key = log.get("feature_name", "unknown")
            elif group_by == "provider":
                key = log.get("provider_name", "unknown")
            elif group_by in ["day", "month"]:
                created_at = log.get("created_at")
                if created_at:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if group_by == "day":
                        key = dt.strftime("%Y-%m-%d")
                    else:
                        key = dt.strftime("%Y-%m")
            
            if key:
                if key not in breakdown:
                    breakdown[key] = {
                        "name": key,
                        "cost": 0.0,
                        "count": 0,
                        "tokens": 0
                    }
                breakdown[key]["cost"] += cost
                breakdown[key]["count"] += 1
                breakdown[key]["tokens"] += int(log.get("total_tokens", 0) or 0)
        
        # Convert to list and sort by cost
        breakdown_list = sorted(breakdown.values(), key=lambda x: x["cost"], reverse=True)
        
        return Response(
            success=True,
            message=f"Cost breakdown retrieved for user",
            data={
                "user": {
                    "id": user_id,
                    "name": user.get("full_name") or user.get("email"),
                    "email": user.get("email")
                },
                "total_cost": round(total_cost, 4),
                "breakdown": breakdown_list,
                "summary": {
                    "total_requests": sum(item["count"] for item in breakdown_list),
                    "total_tokens": sum(item["tokens"] for item in breakdown_list),
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching user cost breakdown", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch cost breakdown: {str(e)}"
        )


@router.get("/system-health", response_model=Response[dict])
async def get_system_health(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    admin_user: dict = Depends(get_current_admin)
):
    """
    Get system health metrics
    
    Args:
        start_date: Start date (defaults to 24 hours ago)
        end_date: End date (defaults to now)
        admin_user: Current admin user (for authorization)
    
    Returns:
        System health metrics by provider
    """
    try:
        # Default to 24 hours if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(hours=24)
        if not end_date:
            end_date = datetime.utcnow()
        
        health_data = await AdminService.get_system_health(
            start_date=start_date,
            end_date=end_date
        )
        
        return Response(
            success=True,
            message="System health data retrieved successfully",
            data=health_data
        )
    except Exception as e:
        logger.error("Error fetching system health", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch system health: {str(e)}"
        )


# ============================================================================
# Organization Management Endpoints
# ============================================================================

@router.put("/organizations/{org_name}/status", response_model=Response[dict])
async def update_organization_status(
    org_name: str,
    status: str = Body(..., embed=True, regex="^(active|paused|suspended|trial)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """Update organization status (pause/resume/suspend)"""
    try:
        result = await admin_service_extensions.update_organization_status(
            org_name=org_name,
            status=status,
            admin_user_id=admin_user["id"]
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return Response(
            success=True,
            message=f"Organization status updated to {status}",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating organization status", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization status: {str(e)}"
        )


@router.put("/organizations/{org_name}/subscription-plan", response_model=Response[dict])
async def update_subscription_plan(
    org_name: str,
    subscription_plan: str = Body(..., embed=True, regex="^(free|starter|professional|enterprise|custom)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """Update organization subscription plan"""
    try:
        result = await admin_service_extensions.update_subscription_plan(
            org_name=org_name,
            subscription_plan=subscription_plan,
            admin_user_id=admin_user["id"]
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return Response(
            success=True,
            message=f"Subscription plan updated to {subscription_plan}",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating subscription plan", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription plan: {str(e)}"
        )


@router.put("/organizations/{org_name}/usage-limits", response_model=Response[dict])
async def update_usage_limits(
    org_name: str,
    limits: Dict[str, Any] = Body(...),
    admin_user: dict = Depends(get_current_admin)
):
    """Update organization usage limits"""
    try:
        result = await admin_service_extensions.update_usage_limits(
            org_name=org_name,
            limits=limits,
            admin_user_id=admin_user["id"]
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return Response(
            success=True,
            message="Usage limits updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating usage limits", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update usage limits: {str(e)}"
        )


@router.put("/organizations/{org_name}/admin-notes", response_model=Response[dict])
async def update_admin_notes(
    org_name: str,
    admin_notes: str = Body(..., embed=True),
    admin_user: dict = Depends(get_current_admin)
):
    """Update admin notes for an organization"""
    try:
        result = await admin_service_extensions.update_admin_notes(
            org_name=org_name,
            admin_notes=admin_notes,
            admin_user_id=admin_user["id"]
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return Response(
            success=True,
            message="Admin notes updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating admin notes", error=str(e), org_name=org_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin notes: {str(e)}"
        )


@router.get("/admin-logs", response_model=Response[list])
async def get_admin_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    target_type: Optional[str] = Query(None, regex="^(organization|user|system)$"),
    action_type: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin)
):
    """Get admin action logs (audit trail)"""
    try:
        logs = await admin_service_extensions.get_admin_logs(
            limit=limit,
            offset=offset,
            target_type=target_type,
            action_type=action_type
        )
        
        return Response(
            success=True,
            message=f"Found {len(logs)} admin logs",
            data=logs
        )
    except Exception as e:
        logger.error("Error fetching admin logs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admin logs: {str(e)}"
        )

