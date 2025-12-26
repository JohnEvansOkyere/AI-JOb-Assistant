"""
Scheduler Service
Manages APScheduler for periodic tasks like automatic follow-up emails
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.services.followup_email_service import FollowupEmailService
import structlog

logger = structlog.get_logger()

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


def start_scheduler():
    """Start the scheduler and register all jobs"""
    if not settings.followup_emails_enabled:
        logger.info("Follow-up emails are disabled, scheduler not started")
        return
    
    sched = get_scheduler()
    
    if sched.running:
        logger.warning("Scheduler is already running")
        return
    
    # Register daily follow-up email job
    sched.add_job(
        FollowupEmailService.process_daily_followups,
        trigger=CronTrigger(
            hour=settings.followup_check_hour,
            minute=settings.followup_check_minute
        ),
        id='daily_followup_emails',
        name='Daily Follow-Up Emails',
        replace_existing=True,
        max_instances=1,  # Only one instance can run at a time
        coalesce=True,  # If multiple triggers are missed, only run once
        misfire_grace_time=3600  # 1 hour grace period for missed jobs
    )
    
    sched.start()
    
    logger.info(
        "Scheduler started",
        followup_check_time=f"{settings.followup_check_hour:02d}:{settings.followup_check_minute:02d}",
        followup_reassurance_days=settings.followup_reassurance_days,
        followup_rejection_days=settings.followup_rejection_days
    )


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
    else:
        logger.info("Scheduler was not running")


def is_scheduler_running() -> bool:
    """Check if scheduler is running"""
    sched = get_scheduler()
    return sched.running if sched else False

