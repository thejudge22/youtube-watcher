"""
Settings service for retrieving application settings from the database.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from ..models.setting import Setting


async def _get_setting(db: AsyncSession) -> Setting:
    """
    Return the singleton settings row, or unsaved defaults if it doesn't exist yet.

    Never writes: committing here would expire every ORM object the caller has
    loaded and break the rest of the request.
    """
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    setting = result.scalar_one_or_none()
    if setting is None:
        return Setting(id="1", http_timeout=10.0, auto_detect_shorts=True)
    return setting


async def get_http_timeout(db: AsyncSession) -> float:
    """
    Get the HTTP timeout setting from the database.
    Returns the default value (10.0) if no settings exist yet or if the table doesn't exist.
    """
    try:
        setting = await _get_setting(db)
        return setting.http_timeout
    except OperationalError:
        return 10.0


async def get_auto_detect_shorts(db: AsyncSession) -> bool:
    """Get the auto_detect_shorts setting. Defaults to True."""
    try:
        setting = await _get_setting(db)
        return getattr(setting, 'auto_detect_shorts', True)
    except OperationalError:
        return True
