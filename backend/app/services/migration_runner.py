"""
Utility to run Alembic migrations programmatically during application startup.
This ensures database schema is up to date on fresh installs.
"""
import asyncio
import logging
from pathlib import Path
import subprocess

from sqlalchemy.ext.asyncio import create_async_engine

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

    try:
        # Run alembic upgrade using subprocess
        # This avoids async/await issues with Alembic's internal asyncio.run()
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            logger.error(f"Migration failed: {result.stderr}")
            raise RuntimeError(f"Alembic migration failed: {result.stderr}")

        logger.info("Database migrations completed successfully")
    except subprocess.TimeoutExpired:
        logger.error("Migration timed out")
        raise
    except FileNotFoundError:
        logger.warning("Alembic command not found, skipping migrations")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise

    # Create any tables not tracked by Alembic (like settings table)
    # This is needed because some tables are created lazily via the API
    # rather than through migrations
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database schema synchronized")
        await engine.dispose()
    except Exception as e:
        logger.error(f"Error creating missing tables: {e}")
        raise
