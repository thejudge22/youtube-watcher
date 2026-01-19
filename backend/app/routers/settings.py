from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, Field

from ..database import get_db, Base
from ..models.setting import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Response model for settings."""
    http_timeout: float = Field(default=10.0, description="HTTP timeout in seconds")


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""
    http_timeout: float = Field(default=10.0, ge=1.0, le=300.0, description="HTTP timeout in seconds (1-300)")


async def _ensure_settings_table(db: AsyncSession):
    """
    Create the settings table if it doesn't exist.
    This is needed for existing databases that were created before the settings feature.
    """
    try:
        async with db.bind.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[Setting.__table__])
    except Exception:
        # If table creation fails, it might already exist, which is fine
        pass


async def _get_settings(db: AsyncSession) -> Setting:
    """
    Internal helper to get or create the settings singleton.
    Ensures there's always exactly one settings row.
    """
    # Ensure the table exists first
    await _ensure_settings_table(db)

    result = await db.execute(select(Setting).where(Setting.id == "1"))
    setting = result.scalar_one_or_none()

    if setting is None:
        # Create default settings
        setting = Setting(id="1", http_timeout=10.0)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return setting


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """
    Get current application settings.
    """
    try:
        setting = await _get_settings(db)
        return SettingsResponse(http_timeout=setting.http_timeout)
    except OperationalError:
        # Table doesn't exist yet, return default values
        return SettingsResponse(http_timeout=10.0)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update application settings.
    """
    setting = await _get_settings(db)
    setting.http_timeout = settings_update.http_timeout
    await db.commit()
    await db.refresh(setting)
    return SettingsResponse(http_timeout=setting.http_timeout)
