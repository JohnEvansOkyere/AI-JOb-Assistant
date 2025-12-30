"""
Admin API Routes
Internal admin dashboard endpoints (admin-only access)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timedelta
from app.schemas.common import Response
from app.utils.admin_auth import get_current_admin, require_admin
from app.services.admin_service import AdminService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/organizations", response_model=Response[list])
async def list_organizations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("last_activity", regex="^(org_name|last_activity|monthly_ai_cost_usd|interviews_completed)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    admin_user: dict = Depends(get_current_admin)
):
    """
    List all organizations with usage metrics
    
    Args:
        limit: Maximum number of organizations to return
        offset: Offset for pagination
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        admin_user: Current admin user (for authorization)
    
    Returns:
        List of organization summaries
    """
    try:
        organizations = await AdminService.get_organizations_overview(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
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

