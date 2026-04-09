"""
Backup scheduler using APScheduler.

Issue #12: Scheduled Backups
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..database import engine
from ..models.setting import Setting
from .backup_service import BackupService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the scheduler instance."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def get_async_session() -> AsyncSession:
    """Create a new async session for the backup job."""
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session()


async def run_scheduled_backup():
    """
    Execute scheduled backup job.
    This function is called by the scheduler.
    """
    logger.info("Starting scheduled backup...")

    async with await get_async_session() as db:
        try:
            # Get backup settings
            result = await db.execute(select(Setting).where(Setting.id == "1"))
            settings = result.scalar_one_or_none()

            if not settings or not settings.backup_enabled:
                logger.info("Backup is disabled, skipping.")
                return

            # Create backup
            success, filenames, error = await BackupService.create_backup(
                db, format=settings.backup_format
            )

            # Cleanup old backups
            if success and filenames:
                await BackupService.cleanup_old_backups(settings.backup_retention_days)

            # Update settings with backup status
            await db.execute(
                update(Setting)
                .where(Setting.id == "1")
                .values(
                    last_backup_at=datetime.now(timezone.utc),
                    last_backup_status='success' if success else 'failed',
                    last_backup_error=error if error else None
                )
            )
            await db.commit()

            if success:
                logger.info(f"Scheduled backup completed successfully: {', '.join(filenames)}")
            else:
                logger.error(f"Scheduled backup failed: {error}")

        except Exception as e:
            logger.error(f"Unexpected error during scheduled backup: {e}")

            # Try to update status
            try:
                await db.execute(
                    update(Setting)
                    .where(Setting.id == "1")
                    .values(
                        last_backup_at=datetime.now(timezone.utc),
                        last_backup_status='failed',
                        last_backup_error=str(e)
                    )
                )
                await db.commit()
            except:
                pass


def schedule_to_cron(schedule: str, time: str) -> CronTrigger:
    """
    Convert schedule settings to APScheduler CronTrigger.

    Args:
        schedule: 'daily', 'weekly', or 'monthly'
        time: HH:MM format
    """
    try:
        hour, minute = time.split(':')
        hour, minute = int(hour), int(minute)
    except (ValueError, AttributeError):
        # Default to 2 AM if time format is invalid
        hour, minute = 2, 0

    if schedule == 'daily':
        return CronTrigger(hour=hour, minute=minute)
    elif schedule == 'weekly':
        return CronTrigger(day_of_week='sun', hour=hour, minute=minute)
    elif schedule == 'monthly':
        return CronTrigger(day='1', hour=hour, minute=minute)
    else:
        # Default to daily
        return CronTrigger(hour=hour, minute=minute)


async def configure_backup_schedule(schedule: str, time: str):
    """
    Configure or update the backup schedule.

    Args:
        schedule: 'daily', 'weekly', or 'monthly'
        time: HH:MM format
    """
    sched = get_scheduler()
    job_id = 'scheduled_backup'

    # Remove existing job if present
    existing_job = sched.get_job(job_id)
    if existing_job:
        sched.remove_job(job_id)

    # Add new job with updated schedule
    trigger = schedule_to_cron(schedule, time)
    sched.add_job(
        run_scheduled_backup,
        trigger=trigger,
        id=job_id,
        name='Scheduled Backup',
        replace_existing=True
    )

    logger.info(f"Backup scheduled: {schedule} at {time}")


async def disable_backup_schedule():
    """Disable the backup schedule by removing the job."""
    sched = get_scheduler()
    job_id = 'scheduled_backup'

    existing_job = sched.get_job(job_id)
    if existing_job:
        sched.remove_job(job_id)
        logger.info("Backup schedule disabled.")


def start_scheduler():
    """Start the scheduler if not already running."""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Backup scheduler started.")


def stop_scheduler():
    """Stop the scheduler."""
    sched = get_scheduler()
    if sched and sched.running:
        sched.shutdown()
        logger.info("Backup scheduler stopped.")
