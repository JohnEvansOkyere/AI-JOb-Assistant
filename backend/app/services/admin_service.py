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
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get overview of all organizations (grouped by company_name)
        
        Args:
            limit: Maximum number of organizations to return
            offset: Offset for pagination
            sort_by: Field to sort by (company_name, last_activity, interviews_count, etc.)
            sort_order: Sort order (asc, desc)
            
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
            
            # Cost by feature
            feature_costs = {}
            for log in usage_logs:
                feature = log.get("feature_name", "unknown")
                cost = float(log.get("estimated_cost_usd", 0))
                feature_costs[feature] = feature_costs.get(feature, 0) + cost
            
            # Top 10 highest cost organizations
            org_costs = {}
            for log in usage_logs:
                recruiter_id = log.get("recruiter_id")
                if not recruiter_id:
                    continue
                
                # Get user's company_name
                user_response = (
                    db.service_client.table("users")
                    .select("company_name")
                    .eq("id", recruiter_id)
                    .execute()
                )
                if user_response.data:
                    org_name = user_response.data[0].get("company_name") or "Unnamed Company"
                    cost = float(log.get("estimated_cost_usd", 0))
                    org_costs[org_name] = org_costs.get(org_name, 0) + cost
            
            top_orgs = sorted(
                org_costs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "daily_costs": {k: round(v, 2) for k, v in sorted(daily_costs.items())},
                "monthly_costs": {k: round(v, 2) for k, v in sorted(monthly_costs.items())},
                "cost_by_feature": {k: round(v, 2) for k, v in feature_costs.items()},
                "top_organizations": [
                    {"org_name": org, "cost_usd": round(cost, 2)}
                    for org, cost in top_orgs
                ],
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

