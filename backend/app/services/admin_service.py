"""
Admin Service
Provides admin dashboard data and metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.database import db
import structlog

logger = structlog.get_logger()


class AdminService:
    """Service for admin dashboard data"""
    
    @staticmethod
    async def get_organizations_overview(
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "last_activity",
        sort_order: str = "desc",
        search: Optional[str] = None,
        status: Optional[str] = None,
        subscription_plan: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get overview of all organizations (grouped by company_name)
        
        Args:
            limit: Maximum number of organizations to return
            offset: Offset for pagination
            sort_by: Field to sort by (company_name, last_activity, interviews_count, etc.)
            sort_order: Sort order (asc, desc)
            search: Search organizations by name (case-insensitive partial match)
            status: Filter by organization status
            subscription_plan: Filter by subscription plan
            
        Returns:
            List of organization summaries
        """
        try:
            # Get all users grouped by company_name
            users_response = db.service_client.table("users").select("*").execute()
            users = users_response.data or []
            
            # Group by company_name (treat each unique company_name as an "organization")
            org_map: Dict[str, Dict[str, Any]] = {}
            
            for user in users:
                company_name = user.get("company_name") or "Unnamed Company"
                user_id = user["id"]
                
                if company_name not in org_map:
                    org_map[company_name] = {
                        "org_id": company_name,  # Using company_name as ID for now
                        "org_name": company_name,
                        "user_ids": [],
                        "active_users": 0,
                    }
                
                org_map[company_name]["user_ids"].append(user_id)
            
            # Get metrics for each organization
            org_list = []
            for org_name, org_data in org_map.items():
                user_ids = [str(uid) for uid in org_data["user_ids"]]  # Ensure strings for query
                
                # Count active users (users who have created interviews or jobs)
                active_users = len(user_ids)  # For now, all users are "active"
                
                # Get job IDs for this organization
                jobs_response = (
                    db.service_client.table("job_descriptions")
                    .select("id")
                    .in_("recruiter_id", user_ids)
                    .execute()
                )
                job_ids = [j["id"] for j in (jobs_response.data or [])]
                jobs_created = len(job_ids)
                
                # Get interview counts
                interviews = []
                if job_ids:
                    interviews_response = (
                        db.service_client.table("interviews")
                        .select("id, status, created_at, job_description_id")
                        .in_("job_description_id", job_ids)
                        .execute()
                    )
                    interviews = interviews_response.data or []
                
                interviews_created = len(interviews)
                interviews_completed = len([i for i in interviews if i.get("status") == "completed"])
                
                # Get CV counts
                cvs_screened = 0
                if job_ids:
                    cvs_response = (
                        db.service_client.table("cvs")
                        .select("id")
                        .in_("job_description_id", job_ids)
                        .execute()
                    )
                    cvs_screened = len(cvs_response.data or [])
                
                # Get AI costs (last 30 days)
                # Query logs where either recruiter_id OR user_id matches (some logs may only have one)
                thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
                
                # Get logs by recruiter_id
                usage_response_recruiter = (
                    db.service_client.table("ai_usage_logs")
                    .select("id, estimated_cost_usd")
                    .in_("recruiter_id", user_ids)
                    .gte("created_at", thirty_days_ago)
                    .execute()
                )
                
                # Get logs by user_id (in case some logs only have user_id)
                usage_response_user = (
                    db.service_client.table("ai_usage_logs")
                    .select("id, estimated_cost_usd")
                    .in_("user_id", user_ids)
                    .gte("created_at", thirty_days_ago)
                    .execute()
                )
                
                # Combine and deduplicate by id
                all_logs = {}
                for log in (usage_response_recruiter.data or []):
                    log_id = log.get("id")
                    if log_id and log_id not in all_logs:
                        all_logs[log_id] = log
                
                for log in (usage_response_user.data or []):
                    log_id = log.get("id")
                    if log_id and log_id not in all_logs:
                        all_logs[log_id] = log
                
                monthly_cost = sum(
                    float(log.get("estimated_cost_usd", 0))
                    for log in all_logs.values()
                )
                
                # Calculate cost per interview
                cost_per_interview = (
                    monthly_cost / interviews_completed
                    if interviews_completed > 0
                    else 0
                )
                
                # Get last activity timestamp
                last_activity = None
                if interviews:
                    last_interview = max(interviews, key=lambda x: x.get("created_at", ""))
                    last_activity = last_interview.get("created_at")
                
                org_list.append({
                    **org_data,
                    "active_users": active_users,
                    "jobs_created": jobs_created,
                    "interviews_created": interviews_created,
                    "interviews_completed": interviews_completed,
                    "cvs_screened": cvs_screened,
                    "monthly_ai_cost_usd": round(monthly_cost, 2),
                    "cost_per_interview_usd": round(cost_per_interview, 4),
                    "last_activity": last_activity,
                })
            
            # Sort
            reverse = sort_order.lower() == "desc"
            if sort_by == "last_activity":
                org_list.sort(key=lambda x: x.get("last_activity") or "", reverse=reverse)
            elif sort_by == "monthly_ai_cost_usd":
                org_list.sort(key=lambda x: x.get("monthly_ai_cost_usd", 0), reverse=reverse)
            elif sort_by == "interviews_completed":
                org_list.sort(key=lambda x: x.get("interviews_completed", 0), reverse=reverse)
            elif sort_by == "org_name":
                org_list.sort(key=lambda x: x.get("org_name", ""), reverse=reverse)
            
            # Paginate
            return org_list[offset:offset + limit]
            
        except Exception as e:
            logger.error("Error fetching organizations overview", error=str(e))
            raise
    
    @staticmethod
    async def get_organization_detail(
        org_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific organization
        
        Args:
            org_name: Organization name (company_name)
            start_date: Start date for metrics (defaults to 30 days ago)
            end_date: End date for metrics (defaults to now)
            
        Returns:
            Organization detail with usage metrics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get all users for this organization
            users_response = (
                db.service_client.table("users")
                .select("*")
                .eq("company_name", org_name)
                .execute()
            )
            users = users_response.data or []
            
            if not users:
                return {"error": "Organization not found"}
            
            user_ids = [u["id"] for u in users]
            
            # Get job IDs
            jobs_response = (
                db.service_client.table("job_descriptions")
                .select("id")
                .in_("recruiter_id", user_ids)
                .execute()
            )
            job_ids = [j["id"] for j in (jobs_response.data or [])]
            
            # Get interviews in date range
            interviews_response = (
                db.service_client.table("interviews")
                .select("*")
                .in_("job_description_id", job_ids)
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )
            interviews = interviews_response.data or []
            
            # Get AI usage logs
            usage_response = (
                db.service_client.table("ai_usage_logs")
                .select("*")
                .in_("recruiter_id", user_ids)
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )
            usage_logs = usage_response.data or []
            
            # Calculate metrics
            total_cost = sum(float(log.get("estimated_cost_usd", 0)) for log in usage_logs)
            
            # Group by feature
            feature_usage = {}
            for log in usage_logs:
                feature = log.get("feature_name", "unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                feature_usage[feature] = feature_usage.get(feature, 0) + cost
            
            # Group by provider
            provider_usage = {}
            for log in usage_logs:
                provider = log.get("provider_name", "unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                provider_usage[provider] = provider_usage.get(provider, 0) + cost
            
            # Token usage (OpenAI)
            openai_logs = [log for log in usage_logs if log.get("provider_name") == "openai"]
            total_tokens = sum(int(log.get("total_tokens", 0)) for log in openai_logs)
            
            # Character usage (ElevenLabs)
            elevenlabs_logs = [log for log in usage_logs if log.get("provider_name") == "elevenlabs"]
            total_characters = sum(int(log.get("characters_used", 0)) for log in elevenlabs_logs)
            
            # Error rate
            total_requests = len(usage_logs)
            failed_requests = len([log for log in usage_logs if log.get("status") != "success"])
            error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Interview completion rate
            total_interviews = len(interviews)
            completed_interviews = len([i for i in interviews if i.get("status") == "completed"])
            completion_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0
            
            # Get organization settings
            settings_response = (
                db.service_client.table("organization_settings")
                .select("*")
                .eq("company_name", org_name)
                .execute()
            )
            settings = settings_response.data[0] if settings_response.data else {}
            
            return {
                "org_name": org_name,
                "active_users": len(users),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "usage": {
                    "total_interviews": total_interviews,
                    "completed_interviews": completed_interviews,
                    "completion_rate": round(completion_rate, 2),
                },
                "ai_costs": {
                    "total_cost_usd": round(total_cost, 2),
                    "by_feature": {k: round(v, 2) for k, v in feature_usage.items()},
                    "by_provider": {k: round(v, 2) for k, v in provider_usage.items()},
                },
                "ai_usage": {
                    "openai_tokens": total_tokens,
                    "elevenlabs_characters": total_characters,
                },
                "system_health": {
                    "total_requests": total_requests,
                    "failed_requests": failed_requests,
                    "error_rate_percent": round(error_rate, 2),
                },
                "settings": {
                    "subscription_plan": settings.get("subscription_plan", "free"),
                    "status": settings.get("status", "active"),
                    "monthly_interview_limit": settings.get("monthly_interview_limit"),
                    "monthly_cost_limit_usd": float(settings.get("monthly_cost_limit_usd")) if settings.get("monthly_cost_limit_usd") else None,
                    "daily_cost_limit_usd": float(settings.get("daily_cost_limit_usd")) if settings.get("daily_cost_limit_usd") else None,
                    "billing_email": settings.get("billing_email"),
                    "admin_notes": settings.get("admin_notes"),
                },
            }
            
        except Exception as e:
            logger.error("Error fetching organization detail", error=str(e), org_name=org_name)
            raise
    
    @staticmethod
    async def get_cost_monitoring(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"  # 'day' or 'month'
    ) -> Dict[str, Any]:
        """
        Get cost monitoring data
        
        Args:
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)
            group_by: Grouping period (day, month)
            
        Returns:
            Cost monitoring data
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get all usage logs in date range
            usage_response = (
                db.service_client.table("ai_usage_logs")
                .select("*")
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )
            usage_logs = usage_response.data or []
            
            # Group by date
            daily_costs = {}
            monthly_costs = {}
            
            for log in usage_logs:
                created_at = log.get("created_at")
                if not created_at:
                    continue
                
                cost = float(log.get("estimated_cost_usd", 0))
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                # Daily grouping
                day_key = dt.date().isoformat()
                daily_costs[day_key] = daily_costs.get(day_key, 0) + cost
                
                # Monthly grouping
                month_key = f"{dt.year}-{dt.month:02d}"
                monthly_costs[month_key] = monthly_costs.get(month_key, 0) + cost
            
            # Cost by feature with counts
            feature_costs = {}
            feature_counts = {}
            for log in usage_logs:
                feature = log.get("feature_name", "unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                feature_costs[feature] = feature_costs.get(feature, 0) + cost
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
            
            # Cost by provider with counts and tokens
            provider_costs = {}
            provider_counts = {}
            provider_tokens = {}
            for log in usage_logs:
                provider = log.get("provider_name", "unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                provider_costs[provider] = provider_costs.get(provider, 0) + cost
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
                
                # Track tokens for token-based providers
                if provider in ["openai", "groq", "gemini"]:
                    tokens = int(log.get("total_tokens", 0) or 0)
                    provider_tokens[provider] = provider_tokens.get(provider, 0) + tokens
            
            # Top organizations with detailed info
            org_costs = {}
            org_request_counts = {}
            org_user_counts = {}
            org_user_map = {}
            
            # Get all recruiter IDs and their organizations
            recruiter_ids = list(set(log.get("recruiter_id") for log in usage_logs if log.get("recruiter_id")))
            if recruiter_ids:
                users_response = (
                    db.service_client.table("users")
                    .select("id, company_name, full_name, email")
                    .in_("id", recruiter_ids)
                    .execute()
                )
                
                for user in (users_response.data or []):
                    org_name = user.get("company_name") or "Unknown"
                    user_id = user["id"]
                    org_user_map[user_id] = org_name
                    
                    if org_name not in org_user_counts:
                        org_user_counts[org_name] = set()
                    org_user_counts[org_name].add(user_id)
            
            # Calculate org costs and request counts
            for log in usage_logs:
                recruiter_id = log.get("recruiter_id")
                if not recruiter_id:
                    continue
                
                org_name = org_user_map.get(recruiter_id, "Unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                org_costs[org_name] = org_costs.get(org_name, 0) + cost
                org_request_counts[org_name] = org_request_counts.get(org_name, 0) + 1
            
            # Sort organizations by cost
            top_orgs = sorted(
                [
                    {
                        "org_name": name,
                        "cost_usd": round(cost, 4),
                        "request_count": org_request_counts.get(name, 0),
                        "user_count": len(org_user_counts.get(name, set())),
                        "avg_cost_per_request": round(cost / org_request_counts.get(name, 1), 6)
                    }
                    for name, cost in org_costs.items()
                ],
                key=lambda x: x["cost_usd"],
                reverse=True
            )[:20]  # Top 20 instead of 10
            
            # Cost by user/client
            user_costs = {}
            user_request_counts = {}
            
            for log in usage_logs:
                recruiter_id = log.get("recruiter_id")
                if not recruiter_id:
                    continue
                
                cost = float(log.get("estimated_cost_usd", 0))
                user_costs[recruiter_id] = user_costs.get(recruiter_id, 0) + cost
                user_request_counts[recruiter_id] = user_request_counts.get(recruiter_id, 0) + 1
            
            # Get user details for top users
            top_user_ids = sorted(
                user_costs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            top_users = []
            if top_user_ids:
                user_ids_list = [uid for uid, _ in top_user_ids]
                users_detail_response = (
                    db.service_client.table("users")
                    .select("id, full_name, email, company_name")
                    .in_("id", user_ids_list)
                    .execute()
                )
                
                users_detail_map = {u["id"]: u for u in (users_detail_response.data or [])}
                
                for user_id, cost in top_user_ids:
                    user_detail = users_detail_map.get(user_id, {})
                    top_users.append({
                        "user_id": user_id,
                        "user_name": user_detail.get("full_name") or user_detail.get("email") or "Unknown",
                        "user_email": user_detail.get("email"),
                        "org_name": user_detail.get("company_name") or "Unknown",
                        "cost_usd": round(cost, 4),
                        "request_count": user_request_counts.get(user_id, 0),
                        "avg_cost_per_request": round(cost / user_request_counts.get(user_id, 1), 6)
                    })
            
            # Calculate totals and averages
            total_cost = sum(daily_costs.values())
            total_requests = len(usage_logs)
            total_tokens = sum(provider_tokens.values())
            
            days_in_period = (end_date - start_date).days + 1
            avg_daily_cost = total_cost / days_in_period if days_in_period > 0 else 0
            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
            
            # Monthly projection
            monthly_projection = avg_daily_cost * 30
            
            # Success/failure rates
            successful_logs = [log for log in usage_logs if log.get("status") == "success"]
            failed_logs = [log for log in usage_logs if log.get("status") != "success"]
            success_rate = (len(successful_logs) / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days_in_period
                },
                "summary": {
                    "total_cost_usd": round(total_cost, 4),
                    "total_requests": total_requests,
                    "total_tokens": total_tokens,
                    "avg_daily_cost_usd": round(avg_daily_cost, 4),
                    "avg_cost_per_request_usd": round(avg_cost_per_request, 6),
                    "monthly_projection_usd": round(monthly_projection, 4),
                    "success_rate_percent": round(success_rate, 2),
                    "successful_requests": len(successful_logs),
                    "failed_requests": len(failed_logs)
                },
                "daily_costs": {k: round(v, 4) for k, v in sorted(daily_costs.items())},
                "monthly_costs": {k: round(v, 4) for k, v in sorted(monthly_costs.items())},
                "cost_by_feature": {
                    k: {
                        "cost_usd": round(v, 4),
                        "request_count": feature_counts.get(k, 0),
                        "avg_cost_per_request": round(v / feature_counts.get(k, 1), 6)
                    }
                    for k, v in feature_costs.items()
                },
                "cost_by_provider": {
                    k: {
                        "cost_usd": round(v, 4),
                        "request_count": provider_counts.get(k, 0),
                        "tokens": provider_tokens.get(k, 0),
                        "avg_cost_per_request": round(v / provider_counts.get(k, 1), 6)
                    }
                    for k, v in provider_costs.items()
                },
                "top_organizations": top_orgs,
                "top_users": top_users
            }
            
        except Exception as e:
            logger.error("Error fetching cost monitoring", error=str(e))
            raise
    
    @staticmethod
    async def get_system_health(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get system health metrics
        
        Args:
            start_date: Start date (defaults to 24 hours ago)
            end_date: End date (defaults to now)
            
        Returns:
            System health metrics
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(hours=24)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get all usage logs
            usage_response = (
                db.service_client.table("ai_usage_logs")
                .select("*")
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )
            usage_logs = usage_response.data or []
            
            # Group by provider
            provider_stats = {}
            for log in usage_logs:
                provider = log.get("provider_name", "unknown")
                status = log.get("status", "unknown")
                latency = log.get("latency_ms", 0)
                
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "total_latency_ms": 0,
                        "error_messages": [],
                    }
                
                provider_stats[provider]["total_requests"] += 1
                if status == "success":
                    provider_stats[provider]["successful_requests"] += 1
                else:
                    provider_stats[provider]["failed_requests"] += 1
                    error_msg = log.get("error_message")
                    if error_msg:
                        provider_stats[provider]["error_messages"].append(error_msg)
                
                provider_stats[provider]["total_latency_ms"] += latency
            
            # Calculate averages and rates
            health_data = {}
            for provider, stats in provider_stats.items():
                total = stats["total_requests"]
                health_data[provider] = {
                    "total_requests": total,
                    "success_rate": round((stats["successful_requests"] / total * 100), 2) if total > 0 else 0,
                    "error_rate": round((stats["failed_requests"] / total * 100), 2) if total > 0 else 0,
                    "avg_latency_ms": round(stats["total_latency_ms"] / total, 2) if total > 0 else 0,
                    "recent_errors": stats["error_messages"][-10:],  # Last 10 errors
                }
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "providers": health_data,
            }
            
        except Exception as e:
            logger.error("Error fetching system health", error=str(e))
            raise

