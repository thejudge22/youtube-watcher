"""
Utility to run Alembic migrations programmatically during application startup.
This ensures database schema is up to date on fresh installs.
"""
import asyncio
import logging
from pathlib import Path

from alembic.config import Config
from alembic import command
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from ..config import settings
from ..database import Base
# Import all models to ensure they're registered with Base.metadata
from ..models import *  # noqa


logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """
    Run Alembic migrations programmatically.

    This is called during application startup to ensure the database
    schema is up to date before any database queries are made.
    """
    # Construct path to alembic.ini (from backend/ directory)
    backend_dir = Path(__file__).parent.parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"

    if not alembic_ini_path.exists():
        logger.warning(f"Alembic config not found at {alembic_ini_path}, skipping migrations")
        return

    # Create Alembic config
    config = Config(str(alembic_ini_path))
    config.set_main_option("sqlalchemy.url", settings.database_url)

    # Create engine for running migrations
    engine = async_engine_from_config(
        {"sqlalchemy.url": settings.database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        # Run Alembic migrations first
        def do_upgrade(connection):
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

        async with engine.connect() as connection:
            await connection.run_sync(do_upgrade)

        logger.info("Database migrations completed successfully")

        # Create any tables not tracked by Alembic (like settings table)
        # This is needed because some tables are created lazily via the API
        # rather than through migrations
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database schema synchronized")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise
    finally:
        await engine.dispose()
