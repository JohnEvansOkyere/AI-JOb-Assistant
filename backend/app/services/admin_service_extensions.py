"""
Admin Service Extensions
Additional methods for organization management and admin controls
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from app.database import db
import structlog

logger = structlog.get_logger()


async def update_organization_status(
    org_name: str,
    status: str,
    admin_user_id: UUID
) -> Dict[str, Any]:
    """
    Update organization status and log the action
    
    Args:
        org_name: Organization name (company_name)
        status: New status (active, paused, suspended, trial)
        admin_user_id: Admin user ID who made the change
        
    Returns:
        Updated organization settings
    """
    try:
        # Get current settings
        settings_response = (
            db.service_client.table("organization_settings")
            .select("*")
            .eq("company_name", org_name)
            .execute()
        )
        
        old_settings = settings_response.data[0] if settings_response.data else {}
        
        # Update or insert settings
        if old_settings:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            result = (
                db.service_client.table("organization_settings")
                .update(update_data)
                .eq("company_name", org_name)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        else:
            # Create new settings record
            insert_data = {
                "company_name": org_name,
                "status": status,
                "subscription_plan": "free"
            }
            result = (
                db.service_client.table("organization_settings")
                .insert(insert_data)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        
        # Log admin action
        await _log_admin_action(
            admin_user_id=admin_user_id,
            action_type="update_organization_status",
            target_type="organization",
            target_id=org_name,
            old_values={"status": old_settings.get("status")} if old_settings else {},
            new_values={"status": status},
            description=f"Updated organization status to {status}"
        )
        
        return new_settings
        
    except Exception as e:
        logger.error("Error updating organization status", error=str(e), org_name=org_name)
        return {"error": str(e)}


async def update_subscription_plan(
    org_name: str,
    subscription_plan: str,
    admin_user_id: UUID
) -> Dict[str, Any]:
    """
    Update organization subscription plan and log the action
    
    Args:
        org_name: Organization name (company_name)
        subscription_plan: New subscription plan
        admin_user_id: Admin user ID who made the change
        
    Returns:
        Updated organization settings
    """
    try:
        # Get current settings
        settings_response = (
            db.service_client.table("organization_settings")
            .select("*")
            .eq("company_name", org_name)
            .execute()
        )
        
        old_settings = settings_response.data[0] if settings_response.data else {}
        
        # Update or insert settings
        if old_settings:
            update_data = {
                "subscription_plan": subscription_plan,
                "updated_at": datetime.utcnow().isoformat()
            }
            result = (
                db.service_client.table("organization_settings")
                .update(update_data)
                .eq("company_name", org_name)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        else:
            # Create new settings record
            insert_data = {
                "company_name": org_name,
                "subscription_plan": subscription_plan,
                "status": "active"
            }
            result = (
                db.service_client.table("organization_settings")
                .insert(insert_data)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        
        # Log admin action
        await _log_admin_action(
            admin_user_id=admin_user_id,
            action_type="update_subscription_plan",
            target_type="organization",
            target_id=org_name,
            old_values={"subscription_plan": old_settings.get("subscription_plan")} if old_settings else {},
            new_values={"subscription_plan": subscription_plan},
            description=f"Updated subscription plan to {subscription_plan}"
        )
        
        return new_settings
        
    except Exception as e:
        logger.error("Error updating subscription plan", error=str(e), org_name=org_name)
        return {"error": str(e)}


async def update_usage_limits(
    org_name: str,
    limits: Dict[str, Any],
    admin_user_id: UUID
) -> Dict[str, Any]:
    """
    Update organization usage limits and log the action
    
    Args:
        org_name: Organization name (company_name)
        limits: Dictionary with limit values
        admin_user_id: Admin user ID who made the change
        
    Returns:
        Updated organization settings
    """
    try:
        # Get current settings
        settings_response = (
            db.service_client.table("organization_settings")
            .select("*")
            .eq("company_name", org_name)
            .execute()
        )
        
        old_settings = settings_response.data[0] if settings_response.data else {}
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if "monthly_interview_limit" in limits:
            update_data["monthly_interview_limit"] = limits["monthly_interview_limit"]
        if "monthly_cost_limit_usd" in limits:
            update_data["monthly_cost_limit_usd"] = limits["monthly_cost_limit_usd"]
        if "daily_cost_limit_usd" in limits:
            update_data["daily_cost_limit_usd"] = limits["daily_cost_limit_usd"]
        
        # Update or insert settings
        if old_settings:
            result = (
                db.service_client.table("organization_settings")
                .update(update_data)
                .eq("company_name", org_name)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        else:
            # Create new settings record
            insert_data = {
                "company_name": org_name,
                "status": "active",
                "subscription_plan": "free",
                **update_data
            }
            result = (
                db.service_client.table("organization_settings")
                .insert(insert_data)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        
        # Log admin action
        old_values = {
            "monthly_interview_limit": old_settings.get("monthly_interview_limit"),
            "monthly_cost_limit_usd": float(old_settings.get("monthly_cost_limit_usd")) if old_settings.get("monthly_cost_limit_usd") else None,
            "daily_cost_limit_usd": float(old_settings.get("daily_cost_limit_usd")) if old_settings.get("daily_cost_limit_usd") else None,
        }
        
        await _log_admin_action(
            admin_user_id=admin_user_id,
            action_type="update_usage_limits",
            target_type="organization",
            target_id=org_name,
            old_values=old_values,
            new_values=limits,
            description="Updated usage limits"
        )
        
        return new_settings
        
    except Exception as e:
        logger.error("Error updating usage limits", error=str(e), org_name=org_name)
        return {"error": str(e)}


async def update_admin_notes(
    org_name: str,
    admin_notes: str,
    admin_user_id: UUID
) -> Dict[str, Any]:
    """
    Update admin notes for an organization
    
    Args:
        org_name: Organization name (company_name)
        admin_notes: Admin notes (internal comments)
        admin_user_id: Admin user ID who made the change
        
    Returns:
        Updated organization settings
    """
    try:
        # Get current settings
        settings_response = (
            db.service_client.table("organization_settings")
            .select("*")
            .eq("company_name", org_name)
            .execute()
        )
        
        old_settings = settings_response.data[0] if settings_response.data else {}
        
        # Update or insert settings
        if old_settings:
            update_data = {
                "admin_notes": admin_notes,
                "updated_at": datetime.utcnow().isoformat()
            }
            result = (
                db.service_client.table("organization_settings")
                .update(update_data)
                .eq("company_name", org_name)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        else:
            # Create new settings record
            insert_data = {
                "company_name": org_name,
                "admin_notes": admin_notes,
                "status": "active",
                "subscription_plan": "free"
            }
            result = (
                db.service_client.table("organization_settings")
                .insert(insert_data)
                .execute()
            )
            new_settings = result.data[0] if result.data else {}
        
        return new_settings
        
    except Exception as e:
        logger.error("Error updating admin notes", error=str(e), org_name=org_name)
        return {"error": str(e)}


async def get_admin_logs(
    limit: int = 100,
    offset: int = 0,
    target_type: Optional[str] = None,
    action_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get admin action logs (audit trail)
    
    Args:
        limit: Maximum number of logs to return
        offset: Offset for pagination
        target_type: Filter by target type
        action_type: Filter by action type
        
    Returns:
        List of admin action logs
    """
    try:
        query = db.service_client.table("admin_action_logs").select("*")
        
        if target_type:
            query = query.eq("target_type", target_type)
        
        if action_type:
            query = query.eq("action_type", action_type)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        logs = response.data or []
        
        # Get admin user names
        admin_user_ids = list(set(log["admin_user_id"] for log in logs if log.get("admin_user_id")))
        if admin_user_ids:
            users_response = (
                db.service_client.table("users")
                .select("id, email, full_name")
                .in_("id", admin_user_ids)
                .execute()
            )
            users_map = {u["id"]: u for u in (users_response.data or [])}
            
            # Add user info to logs
            for log in logs:
                user_id = log.get("admin_user_id")
                if user_id and user_id in users_map:
                    log["admin_user"] = {
                        "email": users_map[user_id].get("email"),
                        "full_name": users_map[user_id].get("full_name")
                    }
        
        return logs
        
    except Exception as e:
        logger.error("Error fetching admin logs", error=str(e))
        return []


async def _log_admin_action(
    admin_user_id: UUID,
    action_type: str,
    target_type: str,
    target_id: str,
    old_values: Dict[str, Any],
    new_values: Dict[str, Any],
    description: str
):
    """
    Log an admin action for audit trail
    
    Args:
        admin_user_id: Admin user ID
        action_type: Type of action
        target_type: Type of target (organization, user, system)
        target_id: ID of the target
        old_values: Previous values
        new_values: New values
        description: Human-readable description
    """
    try:
        log_data = {
            "admin_user_id": str(admin_user_id),
            "action_type": action_type,
            "target_type": target_type,
            "target_id": target_id,
            "old_values": old_values,
            "new_values": new_values,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.service_client.table("admin_action_logs").insert(log_data).execute()
        
    except Exception as e:
        logger.warning("Failed to log admin action", error=str(e))
        # Don't fail the main operation if logging fails
