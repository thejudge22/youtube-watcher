"""
Feed refresh scheduler using APScheduler.

Issue #54: Automatic feed refresh
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.setting import Setting
from .backup_scheduler import get_scheduler, get_async_session
from .channels_service import refresh_all_channels

logger = logging.getLogger(__name__)

# Interval mapping: string value -> hours
INTERVAL_HOURS = {
    '1h': 1,
    '6h': 6,
    '12h': 12,
    '24h': 24,
}


async def run_scheduled_refresh():
    """
    Execute scheduled feed refresh job.
    This function is called by the scheduler.
    """
    logger.info("Starting scheduled feed refresh...")

    async with await get_async_session() as db:
        try:
            # Get settings
            result = await db.execute(select(Setting).where(Setting.id == "1"))
            settings = result.scalar_one_or_none()

            if not settings or not settings.auto_refresh_enabled:
                logger.info("Auto-refresh is disabled, skipping.")
                return

            # Run the refresh
            summary = await refresh_all_channels(db)

            # Update status
            await db.execute(
                update(Setting)
                .where(Setting.id == "1")
                .values(
                    last_refresh_at=datetime.now(timezone.utc),
                    last_refresh_status='success',
                    last_refresh_error=None
                )
            )
            await db.commit()

            logger.info(
                f"Scheduled refresh completed: {summary.channels_refreshed} channels refreshed, "
                f"{summary.new_videos_found} new videos found"
            )

        except Exception as e:
            logger.error(f"Unexpected error during scheduled feed refresh: {e}")

            # Try to update status
            try:
                await db.execute(
                    update(Setting)
                    .where(Setting.id == "1")
                    .values(
                        last_refresh_at=datetime.now(timezone.utc),
                        last_refresh_status='failed',
                        last_refresh_error=str(e)[:500]  # Truncate long errors
                    )
                )
                await db.commit()
            except Exception:
                pass


def interval_to_trigger(interval: str) -> IntervalTrigger:
    """
    Convert interval string to APScheduler IntervalTrigger.

    Args:
        interval: '1h', '6h', '12h', or '24h'
    """
    hours = INTERVAL_HOURS.get(interval, 6)
    return IntervalTrigger(hours=hours)


async def configure_auto_refresh_schedule(interval: str):
    """
    Configure or update the auto-refresh schedule.

    Args:
        interval: '1h', '6h', '12h', or '24h'
    """
    sched = get_scheduler()
    job_id = 'scheduled_feed_refresh'

    # Remove existing job if present
    existing_job = sched.get_job(job_id)
    if existing_job:
        sched.remove_job(job_id)

    # Add new job with updated schedule
    trigger = interval_to_trigger(interval)
    sched.add_job(
        run_scheduled_refresh,
        trigger=trigger,
        id=job_id,
        name='Scheduled Feed Refresh',
        replace_existing=True
    )

    logger.info(f"Auto-refresh scheduled: every {interval}")


async def disable_auto_refresh_schedule():
    """Disable the auto-refresh schedule by removing the job."""
    sched = get_scheduler()
    job_id = 'scheduled_feed_refresh'

    existing_job = sched.get_job(job_id)
    if existing_job:
        sched.remove_job(job_id)
        logger.info("Auto-refresh schedule disabled.")