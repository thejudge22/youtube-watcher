"""
Backup management API router.

Issue #12: Scheduled Backups
"""

import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..database import get_db
from ..models.setting import Setting
from ..schemas.settings import (
    BackupSettings,
    BackupStatus,
    BackupListResponse,
    BackupInfo,
    ManualBackupRequest,
    ManualBackupResponse,
)
from ..services.backup_service import BackupService
from ..services.backup_scheduler import configure_backup_schedule, disable_backup_schedule

router = APIRouter(prefix="/backup", tags=["backup"])

logger = logging.getLogger(__name__)


@router.get("/settings", response_model=BackupSettings)
async def get_backup_settings(db: AsyncSession = Depends(get_db)):
    """Get current backup settings."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        # Return defaults
        return BackupSettings()

    return BackupSettings(
        backup_enabled=settings.backup_enabled,
        backup_schedule=settings.backup_schedule,
        backup_time=settings.backup_time,
        backup_format=settings.backup_format,
        backup_retention_days=settings.backup_retention_days,
    )


@router.put("/settings", response_model=BackupSettings)
async def update_backup_settings(
    settings_update: BackupSettings,
    db: AsyncSession = Depends(get_db)
):
    """Update backup settings."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create settings if they don't exist
        settings = Setting(
            id="1",
            backup_enabled=settings_update.backup_enabled,
            backup_schedule=settings_update.backup_schedule,
            backup_time=settings_update.backup_time,
            backup_format=settings_update.backup_format,
            backup_retention_days=settings_update.backup_retention_days,
        )
        db.add(settings)
    else:
        settings.backup_enabled = settings_update.backup_enabled
        settings.backup_schedule = settings_update.backup_schedule
        settings.backup_time = settings_update.backup_time
        settings.backup_format = settings_update.backup_format
        settings.backup_retention_days = settings_update.backup_retention_days

    await db.commit()

    # Update scheduler
    if settings_update.backup_enabled:
        await configure_backup_schedule(
            settings_update.backup_schedule,
            settings_update.backup_time
        )
    else:
        await disable_backup_schedule()

    return settings_update


@router.get("/status", response_model=BackupStatus)
async def get_backup_status(db: AsyncSession = Depends(get_db)):
    """Get last backup status."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    if not settings:
        return BackupStatus(
            last_backup_at=None,
            last_backup_status=None,
            last_backup_error=None,
        )

    return BackupStatus(
        last_backup_at=settings.last_backup_at,
        last_backup_status=settings.last_backup_status,
        last_backup_error=settings.last_backup_error,
    )


@router.get("/list", response_model=BackupListResponse)
async def list_backups():
    """List all existing backups."""
    backups = await BackupService.list_backups()

    total_size = sum(b['size_bytes'] for b in backups)

    return BackupListResponse(
        backups=[BackupInfo(**b) for b in backups],
        total_count=len(backups),
        total_size_bytes=total_size,
    )


@router.post("/run", response_model=ManualBackupResponse)
async def run_manual_backup(
    request: ManualBackupRequest,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a manual backup."""
    success, filenames, error = await BackupService.create_backup(db, format=request.format)

    # Clean up old backups based on retention
    if success and filenames:
        result = await db.execute(select(Setting).where(Setting.id == "1"))
        settings = result.scalar_one_or_none()
        if settings:
            await BackupService.cleanup_old_backups(settings.backup_retention_days)

        # Update status on success
        from datetime import datetime, timezone
        await db.execute(
            update(Setting)
            .where(Setting.id == "1")
            .values(
                last_backup_at=datetime.now(timezone.utc),
                last_backup_status='success' if success else 'failed',
                last_backup_error=error
            )
        )
        await db.commit()

    return ManualBackupResponse(
        success=success,
        filenames=filenames,
        error=error,
    )


@router.delete("/cleanup")
async def cleanup_old_backups(db: AsyncSession = Depends(get_db)):
    """Manually trigger cleanup of old backups."""
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    settings = result.scalar_one_or_none()

    retention_days = settings.backup_retention_days if settings else 30
    removed_count = await BackupService.cleanup_old_backups(retention_days)

    return {"removed_count": removed_count}
