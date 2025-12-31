"""
Usage Limit Checker Service
Enforces usage limits for organizations (interview limits, cost limits, status checks)
Automatically assigns limits based on subscription plan configuration
"""

from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.database import db
from app.config_plans import SubscriptionPlanService
from app.utils.errors import AppException
import structlog

logger = structlog.get_logger()


class UsageLimitError(AppException):
    """Raised when a usage limit is exceeded"""
    def __init__(self, limit_type: str, current: float, limit: float, period: str = "monthly"):
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        self.period = period
        message = self._get_error_message()
        super().__init__(message, status_code=429)  # HTTP 429 Too Many Requests
    
    def _get_error_message(self) -> str:
        """Generate user-friendly error message"""
        if self.limit_type == "interview_limit":
            return f"Monthly interview limit reached ({self.current}/{self.limit}). Please contact support to increase your limit or wait until next month."
        elif self.limit_type == "daily_cost_limit":
            return f"Daily cost limit reached (${self.current:.2f}/${self.limit:.2f}). This limit resets at midnight. Please contact support to increase your limit."
        elif self.limit_type == "monthly_cost_limit":
            return f"Monthly cost limit reached (${self.current:.2f}/${self.limit:.2f}). Please contact support to increase your limit or wait until next month."
        elif self.limit_type == "organization_status":
            return "Your organization account is paused or suspended. Please contact support to restore access."
        else:
            return f"Usage limit exceeded: {self.limit_type}"


class UsageLimitChecker:
    """Service for checking and enforcing usage limits"""
    
    @staticmethod
    async def get_organization_settings(recruiter_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get organization settings for a recruiter
        
        Args:
            recruiter_id: Recruiter/user ID
        
        Returns:
            Organization settings dict or None if not found
        """
        try:
            # Get user's organization name
            user_response = (
                db.service_client.table("users")
                .select("company_name")
                .eq("id", str(recruiter_id))
                .execute()
            )
            
            if not user_response.data:
                logger.warning("User not found for limit checking", recruiter_id=str(recruiter_id))
                return None
            
            company_name = user_response.data[0].get("company_name")
            if not company_name:
                # No organization set - allow unlimited (for backward compatibility)
                return None
            
            # Get organization settings
            settings_response = (
                db.service_client.table("organization_settings")
                .select("*")
                .eq("company_name", company_name)
                .execute()
            )
            
            if settings_response.data:
                settings = settings_response.data[0]
                # Auto-assign limits from plan config if not set
                settings = await UsageLimitChecker._ensure_limits_from_plan(settings)
                return settings
            
            # No settings found - default to unlimited
            return None
            
        except Exception as e:
            logger.error("Error getting organization settings", error=str(e), recruiter_id=str(recruiter_id))
            # On error, allow operation (fail open for availability)
            return None
    
    @staticmethod
    async def check_organization_status(recruiter_id: UUID) -> None:
        """
        Check if organization is active (not paused or suspended)
        
        Args:
            recruiter_id: Recruiter/user ID
        
        Raises:
            UsageLimitError: If organization is paused or suspended
        """
        settings = await UsageLimitChecker.get_organization_settings(recruiter_id)
        
        if not settings:
            # No settings = active (backward compatibility)
            return
        
        status = settings.get("status", "active")
        
        if status in ["paused", "suspended"]:
            raise UsageLimitError(
                limit_type="organization_status",
                current=0,
                limit=0
            )
    
    @staticmethod
    async def check_monthly_interview_limit(recruiter_id: UUID) -> None:
        """
        Check if organization can create more interviews this month
        
        Args:
            recruiter_id: Recruiter/user ID
        
        Raises:
            UsageLimitError: If monthly interview limit is exceeded
        """
        settings = await UsageLimitChecker.get_organization_settings(recruiter_id)
        
        if not settings:
            # No settings = unlimited
            return
        
        monthly_limit = settings.get("monthly_interview_limit")
        
        if monthly_limit is None:
            # NULL = unlimited
            return
        
        # Get current month's interview count for this organization
        user_response = (
            db.service_client.table("users")
            .select("company_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        if not user_response.data:
            return
        
        company_name = user_response.data[0].get("company_name")
        if not company_name:
            return
        
        # Get all users in this organization
        org_users_response = (
            db.service_client.table("users")
            .select("id")
            .eq("company_name", company_name)
            .execute()
        )
        
        org_user_ids = [u["id"] for u in (org_users_response.data or [])]
        if not org_user_ids:
            return
        
        # Get job IDs for this organization
        jobs_response = (
            db.service_client.table("job_descriptions")
            .select("id")
            .in_("recruiter_id", org_user_ids)
            .execute()
        )
        
        job_ids = [j["id"] for j in (jobs_response.data or [])]
        if not job_ids:
            # No jobs = 0 interviews
            return
        
        # Get current month start and end
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Count interviews created this month
        interviews_response = (
            db.service_client.table("interviews")
            .select("id", count="exact")
            .in_("job_description_id", job_ids)
            .gte("created_at", month_start.isoformat())
            .lte("created_at", month_end.isoformat())
            .execute()
        )
        
        current_count = interviews_response.count if hasattr(interviews_response, 'count') else len(interviews_response.data or [])
        
        if current_count >= monthly_limit:
            raise UsageLimitError(
                limit_type="interview_limit",
                current=float(current_count),
                limit=float(monthly_limit),
                period="monthly"
            )
    
    @staticmethod
    async def check_daily_cost_limit(recruiter_id: UUID, estimated_cost: Decimal = Decimal('0')) -> None:
        """
        Check if adding estimated_cost would exceed daily cost limit
        
        Args:
            recruiter_id: Recruiter/user ID
            estimated_cost: Estimated cost of the operation (default: 0, only checks current usage)
        
        Raises:
            UsageLimitError: If daily cost limit would be exceeded
        """
        settings = await UsageLimitChecker.get_organization_settings(recruiter_id)
        
        if not settings:
            return
        
        daily_limit = settings.get("daily_cost_limit_usd")
        
        if daily_limit is None:
            # NULL = unlimited
            return
        
        daily_limit_decimal = Decimal(str(daily_limit))
        
        # Get current day's cost for this organization
        user_response = (
            db.service_client.table("users")
            .select("company_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        if not user_response.data:
            return
        
        company_name = user_response.data[0].get("company_name")
        if not company_name:
            return
        
        # Get all users in this organization
        org_users_response = (
            db.service_client.table("users")
            .select("id")
            .eq("company_name", company_name)
            .execute()
        )
        
        org_user_ids = [u["id"] for u in (org_users_response.data or [])]
        if not org_user_ids:
            return
        
        # Get today's start and end (UTC)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
        
        # Get today's AI usage costs
        usage_response = (
            db.service_client.table("ai_usage_logs")
            .select("estimated_cost_usd")
            .in_("recruiter_id", org_user_ids)
            .gte("created_at", today_start.isoformat())
            .lte("created_at", today_end.isoformat())
            .eq("status", "success")
            .execute()
        )
        
        today_cost = Decimal('0')
        for log in (usage_response.data or []):
            cost = log.get("estimated_cost_usd")
            if cost:
                today_cost += Decimal(str(cost))
        
        # Check if adding estimated_cost would exceed limit
        if today_cost + estimated_cost > daily_limit_decimal:
            raise UsageLimitError(
                limit_type="daily_cost_limit",
                current=float(today_cost + estimated_cost),
                limit=float(daily_limit_decimal),
                period="daily"
            )
    
    @staticmethod
    async def check_monthly_cost_limit(recruiter_id: UUID, estimated_cost: Decimal = Decimal('0')) -> None:
        """
        Check if adding estimated_cost would exceed monthly cost limit
        
        Args:
            recruiter_id: Recruiter/user ID
            estimated_cost: Estimated cost of the operation (default: 0, only checks current usage)
        
        Raises:
            UsageLimitError: If monthly cost limit would be exceeded
        """
        settings = await UsageLimitChecker.get_organization_settings(recruiter_id)
        
        if not settings:
            return
        
        monthly_limit = settings.get("monthly_cost_limit_usd")
        
        if monthly_limit is None:
            # NULL = unlimited
            return
        
        monthly_limit_decimal = Decimal(str(monthly_limit))
        
        # Get current month's cost for this organization
        user_response = (
            db.service_client.table("users")
            .select("company_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        if not user_response.data:
            return
        
        company_name = user_response.data[0].get("company_name")
        if not company_name:
            return
        
        # Get all users in this organization
        org_users_response = (
            db.service_client.table("users")
            .select("id")
            .eq("company_name", company_name)
            .execute()
        )
        
        org_user_ids = [u["id"] for u in (org_users_response.data or [])]
        if not org_user_ids:
            return
        
        # Get current month start and end
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Get this month's AI usage costs
        usage_response = (
            db.service_client.table("ai_usage_logs")
            .select("estimated_cost_usd")
            .in_("recruiter_id", org_user_ids)
            .gte("created_at", month_start.isoformat())
            .lte("created_at", month_end.isoformat())
            .eq("status", "success")
            .execute()
        )
        
        month_cost = Decimal('0')
        for log in (usage_response.data or []):
            cost = log.get("estimated_cost_usd")
            if cost:
                month_cost += Decimal(str(cost))
        
        # Check if adding estimated_cost would exceed limit
        if month_cost + estimated_cost > monthly_limit_decimal:
            raise UsageLimitError(
                limit_type="monthly_cost_limit",
                current=float(month_cost + estimated_cost),
                limit=float(monthly_limit_decimal),
                period="monthly"
            )
    
    @staticmethod
    async def check_all_limits(
        recruiter_id: UUID,
        check_interview_limit: bool = False,
        check_cost_limit: bool = False,
        estimated_cost: Optional[Decimal] = None
    ) -> None:
        """
        Convenience method to check all relevant limits
        
        Args:
            recruiter_id: Recruiter/user ID
            check_interview_limit: Whether to check monthly interview limit
            check_cost_limit: Whether to check cost limits
            estimated_cost: Estimated cost of the operation (for cost limit checking)
        
        Raises:
            UsageLimitError: If any limit is exceeded
        """
        # Always check organization status
        await UsageLimitChecker.check_organization_status(recruiter_id)
        
        if check_interview_limit:
            await UsageLimitChecker.check_monthly_interview_limit(recruiter_id)
        
        if check_cost_limit:
            cost = estimated_cost or Decimal('0')
            await UsageLimitChecker.check_daily_cost_limit(recruiter_id, cost)
            await UsageLimitChecker.check_monthly_cost_limit(recruiter_id, cost)
    
    @staticmethod
    async def get_usage_summary(recruiter_id: UUID) -> Dict[str, Any]:
        """
        Get current usage summary for an organization (for display/info purposes)
        
        Args:
            recruiter_id: Recruiter/user ID
        
        Returns:
            Dictionary with current usage stats
        """
        settings = await UsageLimitChecker.get_organization_settings(recruiter_id)
        
        if not settings:
            return {
                "organization_status": "active",
                "monthly_interview_limit": None,
                "monthly_cost_limit_usd": None,
                "daily_cost_limit_usd": None,
                "current_monthly_interviews": 0,
                "current_monthly_cost_usd": 0.0,
                "current_daily_cost_usd": 0.0,
                "has_limits": False
            }
        
        # Get organization users
        user_response = (
            db.service_client.table("users")
            .select("company_name")
            .eq("id", str(recruiter_id))
            .execute()
        )
        
        company_name = user_response.data[0].get("company_name") if user_response.data else None
        
        monthly_interviews = 0
        monthly_cost = Decimal('0')
        daily_cost = Decimal('0')
        
        if company_name:
            org_users_response = (
                db.service_client.table("users")
                .select("id")
                .eq("company_name", company_name)
                .execute()
            )
            
            org_user_ids = [u["id"] for u in (org_users_response.data or [])]
            
            if org_user_ids:
                # Get current month
                now = datetime.now(timezone.utc)
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                
                # Count monthly interviews
                jobs_response = (
                    db.service_client.table("job_descriptions")
                    .select("id")
                    .in_("recruiter_id", org_user_ids)
                    .execute()
                )
                
                job_ids = [j["id"] for j in (jobs_response.data or [])]
                
                if job_ids:
                    interviews_response = (
                        db.service_client.table("interviews")
                        .select("id", count="exact")
                        .in_("job_description_id", job_ids)
                        .gte("created_at", month_start.isoformat())
                        .lte("created_at", month_end.isoformat())
                        .execute()
                    )
                    
                    monthly_interviews = interviews_response.count if hasattr(interviews_response, 'count') else len(interviews_response.data or [])
                
                # Get monthly costs
                monthly_usage_response = (
                    db.service_client.table("ai_usage_logs")
                    .select("estimated_cost_usd")
                    .in_("recruiter_id", org_user_ids)
                    .gte("created_at", month_start.isoformat())
                    .lte("created_at", month_end.isoformat())
                    .eq("status", "success")
                    .execute()
                )
                
                for log in (monthly_usage_response.data or []):
                    cost = log.get("estimated_cost_usd")
                    if cost:
                        monthly_cost += Decimal(str(cost))
                
                # Get daily costs
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
                
                daily_usage_response = (
                    db.service_client.table("ai_usage_logs")
                    .select("estimated_cost_usd")
                    .in_("recruiter_id", org_user_ids)
                    .gte("created_at", today_start.isoformat())
                    .lte("created_at", today_end.isoformat())
                    .eq("status", "success")
                    .execute()
                )
                
                for log in (daily_usage_response.data or []):
                    cost = log.get("estimated_cost_usd")
                    if cost:
                        daily_cost += Decimal(str(cost))
        
        return {
            "organization_status": settings.get("status", "active"),
            "monthly_interview_limit": settings.get("monthly_interview_limit"),
            "monthly_cost_limit_usd": float(settings.get("monthly_cost_limit_usd")) if settings.get("monthly_cost_limit_usd") else None,
            "daily_cost_limit_usd": float(settings.get("daily_cost_limit_usd")) if settings.get("daily_cost_limit_usd") else None,
            "current_monthly_interviews": monthly_interviews,
            "current_monthly_cost_usd": float(monthly_cost),
            "current_daily_cost_usd": float(daily_cost),
            "has_limits": (
                settings.get("monthly_interview_limit") is not None or
                settings.get("monthly_cost_limit_usd") is not None or
                settings.get("daily_cost_limit_usd") is not None
            )
        }


    @staticmethod
    async def _ensure_limits_from_plan(settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure limits are set from plan configuration if not already set.
        This automatically syncs limits when subscription_plan is set but limits aren't.
        
        Args:
            settings: Organization settings dict
        
        Returns:
            Updated settings dict
        """
        subscription_plan = settings.get("subscription_plan")
        if not subscription_plan:
            return settings
        
        # Get plan configuration
        plan_config = SubscriptionPlanService.get_plan_config(subscription_plan)
        if not plan_config:
            return settings
        
        plan_limits = plan_config.get("limits", {})
        needs_update = False
        update_data = {}
        
        # Check and set monthly_interview_limit
        if settings.get("monthly_interview_limit") is None:
            limit = plan_limits.get("monthly_interview_limit")
            if limit is not None:
                update_data["monthly_interview_limit"] = limit
                needs_update = True
                settings["monthly_interview_limit"] = limit
        
        # Check and set monthly_cost_limit_usd
        if settings.get("monthly_cost_limit_usd") is None:
            limit = plan_limits.get("monthly_cost_limit_usd")
            if limit is not None:
                # Convert Decimal to float for database
                update_data["monthly_cost_limit_usd"] = float(limit)
                needs_update = True
                settings["monthly_cost_limit_usd"] = float(limit)
        
        # Check and set daily_cost_limit_usd
        if settings.get("daily_cost_limit_usd") is None:
            limit = plan_limits.get("daily_cost_limit_usd")
            if limit is not None:
                # Convert Decimal to float for database
                update_data["daily_cost_limit_usd"] = float(limit)
                needs_update = True
                settings["daily_cost_limit_usd"] = float(limit)
        
        # Update database if needed
        if needs_update and update_data:
            try:
                company_name = settings.get("company_name")
                update_data["updated_at"] = datetime.utcnow().isoformat()
                
                db.service_client.table("organization_settings").update(update_data).eq(
                    "company_name", company_name
                ).execute()
                
                logger.info(
                    "Auto-assigned limits from plan",
                    company_name=company_name,
                    subscription_plan=subscription_plan,
                    limits=update_data
                )
            except Exception as e:
                logger.warning(
                    "Failed to auto-assign limits from plan",
                    error=str(e),
                    company_name=settings.get("company_name")
                )
        
        return settings
    
    @staticmethod
    async def assign_plan_limits(company_name: str, subscription_plan: str) -> Dict[str, Any]:
        """
        Assign limits from plan configuration to an organization.
        This should be called when a subscription plan is set or changed.
        
        Args:
            company_name: Organization company name
            subscription_plan: Plan identifier
        
        Returns:
            Updated settings dict
        """
        plan_config = SubscriptionPlanService.get_plan_config(subscription_plan)
        if not plan_config:
            logger.warning("Plan config not found", plan=subscription_plan)
            return {}
        
        plan_limits = plan_config.get("limits", {})
        update_data = {
            "subscription_plan": subscription_plan,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Set limits from plan (override existing if plan is changed)
        if "monthly_interview_limit" in plan_limits:
            update_data["monthly_interview_limit"] = plan_limits["monthly_interview_limit"]
        
        if "monthly_cost_limit_usd" in plan_limits:
            limit = plan_limits["monthly_cost_limit_usd"]
            update_data["monthly_cost_limit_usd"] = float(limit) if limit is not None else None
        
        if "daily_cost_limit_usd" in plan_limits:
            limit = plan_limits["daily_cost_limit_usd"]
            update_data["daily_cost_limit_usd"] = float(limit) if limit is not None else None
        
        try:
            # Update or insert settings
            response = (
                db.service_client.table("organization_settings")
                .select("id")
                .eq("company_name", company_name)
                .execute()
            )
            
            if response.data:
                # Update existing
                result = (
                    db.service_client.table("organization_settings")
                    .update(update_data)
                    .eq("company_name", company_name)
                    .execute()
                )
            else:
                # Insert new
                update_data["company_name"] = company_name
                update_data["status"] = "trial"  # New subscriptions start as trial
                result = (
                    db.service_client.table("organization_settings")
                    .insert(update_data)
                    .execute()
                )
            
            logger.info(
                "Assigned plan limits",
                company_name=company_name,
                subscription_plan=subscription_plan,
                limits=update_data
            )
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(
                "Failed to assign plan limits",
                error=str(e),
                company_name=company_name,
                subscription_plan=subscription_plan
            )
            raise
