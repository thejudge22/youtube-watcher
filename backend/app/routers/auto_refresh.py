"""
Auto-refresh management API router.

Issue #54: Automatic feed refresh
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.setting import Setting
from ..schemas.settings import AutoRefreshSettings, RefreshStatus
from ..services.feed_refresh_scheduler import (
    configure_auto_refresh_schedule,
    disable_auto_refresh_schedule,
)

router = APIRouter(prefix="/auto-refresh", tags=["auto-refresh"])

logger = logging.getLogger(__name__)


@router.get("/settings", response_model=AutoRefreshSettings)
async def get_auto_refresh_settings(db: AsyncSession = Depends(get_db)):
    """Get current auto-refresh settings."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        return AutoRefreshSettings()

    return AutoRefreshSettings(
        auto_refresh_enabled=settings.auto_refresh_enabled,
        auto_refresh_interval=settings.auto_refresh_interval,
    )


@router.put("/settings", response_model=AutoRefreshSettings)
async def update_auto_refresh_settings(
    settings_update: AutoRefreshSettings,
    db: AsyncSession = Depends(get_db)
):
    """Update auto-refresh settings."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create settings if they don't exist
        settings = Setting(
            id="1",
            auto_refresh_enabled=settings_update.auto_refresh_enabled,
            auto_refresh_interval=settings_update.auto_refresh_interval,
        )
        db.add(settings)
    else:
        settings.auto_refresh_enabled = settings_update.auto_refresh_enabled
        settings.auto_refresh_interval = settings_update.auto_refresh_interval

    await db.commit()

    # Update scheduler
    if settings_update.auto_refresh_enabled:
        await configure_auto_refresh_schedule(
            settings_update.auto_refresh_interval
        )
    else:
        await disable_auto_refresh_schedule()

    return settings_update


@router.get("/status", response_model=RefreshStatus)
async def get_auto_refresh_status(db: AsyncSession = Depends(get_db)):
    """Get auto-refresh status."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        return RefreshStatus(
            auto_refresh_enabled=False,
            auto_refresh_interval='6h',
            last_refresh_at=None,
            last_refresh_status=None,
            last_refresh_error=None,
        )

    return RefreshStatus(
        auto_refresh_enabled=settings.auto_refresh_enabled,
        auto_refresh_interval=settings.auto_refresh_interval,
        last_refresh_at=settings.last_refresh_at,
        last_refresh_status=settings.last_refresh_status,
        last_refresh_error=settings.last_refresh_error,
    )