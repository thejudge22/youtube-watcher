"""
Settings service for retrieving application settings from the database.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from ..models.setting import Setting


async def get_http_timeout(db: AsyncSession) -> float:
    """
    Get the HTTP timeout setting from the database.
    Returns the default value (10.0) if no settings exist yet or if the table doesn't exist.

    Args:
        db: Database session

    Returns:
        HTTP timeout in seconds
    """
    try:
        result = await db.execute(select(Setting).where(Setting.id == "1"))
        setting = result.scalar_one_or_none()

        if setting is None:
            # Create default settings if none exist
            setting = Setting(id="1", http_timeout=10.0)
            db.add(setting)
            await db.commit()
            return 10.0

        return setting.http_timeout
    except OperationalError:
        # Table doesn't exist yet, return default value
        # The table will be created when settings are first saved via the API
        return 10.0
