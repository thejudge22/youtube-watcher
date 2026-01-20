"""
Backup service for scheduled and manual backups.

Issue #12: Scheduled Backups
"""

import os
import shutil
import json
import gzip
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.channel import Channel
from ..models.video import Video
from ..config import settings as app_settings

logger = logging.getLogger(__name__)

# Backup directory - stored in Docker volume
BACKUP_DIR = Path("/app/data/backups")


class BackupService:
    """Service for creating and managing backups."""

    @staticmethod
    def ensure_backup_dir():
        """Ensure backup directory exists."""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_backup_filename(format: str) -> str:
        """Generate backup filename with timestamp and gzip extension."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format == 'json':
            return f"backup_{timestamp}.json.gz"
        elif format == 'database':
            return f"backup_{timestamp}.db.gz"
        return f"backup_{timestamp}.gz"

    @staticmethod
    def _create_json_backup_sync() -> Tuple[bool, str, Optional[str]]:
        """
        Synchronous helper for creating JSON backup using direct sqlite3.
        This bypasses SQLAlchemy's async complexity.
        """
        import sqlite3

        cls = BackupService
        cls.ensure_backup_dir()
        filename = cls.get_backup_filename('json')
        filepath = BACKUP_DIR / filename

        try:
            # Get database path
            db_path = os.environ.get('DATABASE_PATH', './data/youtube-watcher.db')
            if db_path.startswith('./'):
                source_path = Path('/app') / db_path[2:]
            else:
                source_path = Path(db_path)

            if not source_path.exists():
                source_path = Path('/app/data/youtube-watcher.db')

            if not source_path.exists():
                return False, filename, f"Database file not found: {source_path}"

            # Use synchronous sqlite3 connection
            conn = sqlite3.connect(source_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch channels
            cursor.execute("SELECT youtube_channel_id, name, youtube_url FROM channels ORDER BY name")
            channels = [dict(row) for row in cursor.fetchall()]

            # Fetch saved videos with channel info
            cursor.execute("""
                SELECT
                    v.youtube_video_id,
                    v.title,
                    v.video_url,
                    v.saved_at,
                    v.published_at,
                    c.youtube_channel_id as channel_youtube_id,
                    c.name as channel_name,
                    c.youtube_url as channel_url
                FROM videos v
                LEFT JOIN channels c ON v.channel_youtube_id = c.youtube_channel_id
                WHERE v.status = 'saved'
                ORDER BY v.saved_at DESC
            """)
            videos = [dict(row) for row in cursor.fetchall()]

            conn.close()

            # Build export data
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "backup_type": "scheduled",
                "channels": [
                    {
                        "youtube_channel_id": c["youtube_channel_id"],
                        "name": c["name"],
                        "youtube_url": c["youtube_url"],
                    }
                    for c in channels
                ],
                "saved_videos": [
                    {
                        "youtube_video_id": v["youtube_video_id"],
                        "title": v["title"],
                        "video_url": v["video_url"],
                        "channel_youtube_id": v["channel_youtube_id"],
                        "channel_name": v["channel_name"],
                        "channel_url": v["channel_url"],
                        "saved_at": v["saved_at"],
                        "published_at": v["published_at"],
                    }
                    for v in videos
                ]
            }

            # Write to gzip compressed file
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"JSON backup created successfully: {filename}")
            return True, filename, None

        except Exception as e:
            error_msg = f"Failed to create JSON backup: {str(e)}"
            logger.error(error_msg)
            return False, filename, error_msg

    @classmethod
    async def create_json_backup(cls, db: AsyncSession) -> Tuple[bool, str, Optional[str]]:
        """
        Create a JSON backup of all data.

        Returns:
            Tuple of (success, filename, error_message)
        """
        # Run synchronous backup in thread pool to avoid blocking async context
        return await asyncio.to_thread(cls._create_json_backup_sync)

    @staticmethod
    def _create_database_backup_sync() -> Tuple[bool, str, Optional[str]]:
        """
        Synchronous helper for creating gzipped database backup.
        """
        cls = BackupService
        cls.ensure_backup_dir()
        filename = cls.get_backup_filename('database')
        filepath = BACKUP_DIR / filename

        try:
            # Get database path from environment
            db_path = os.environ.get('DATABASE_PATH', './data/youtube-watcher.db')

            # Handle relative path
            if db_path.startswith('./'):
                source_path = Path('/app') / db_path[2:]
            else:
                source_path = Path(db_path)

            if not source_path.exists():
                # Try alternative location
                source_path = Path('/app/data/youtube-watcher.db')

            if not source_path.exists():
                return False, filename, f"Database file not found: {source_path}"

            # Read source file and write compressed
            with open(source_path, 'rb') as f_in:
                with gzip.open(filepath, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"Database backup created successfully: {filename}")
            return True, filename, None

        except Exception as e:
            error_msg = f"Failed to create database backup: {str(e)}"
            logger.error(error_msg)
            return False, filename, error_msg

    @classmethod
    async def create_database_backup(cls) -> Tuple[bool, str, Optional[str]]:
        """
        Create a gzipped copy of the SQLite database file.

        Returns:
            Tuple of (success, filename, error_message)
        """
        # Run synchronous backup in thread pool to avoid blocking async context
        return await asyncio.to_thread(cls._create_database_backup_sync)

    @classmethod
    async def create_backup(cls, db: AsyncSession, format: str = 'json') -> Tuple[bool, List[str], Optional[str]]:
        """
        Create backup in specified format.

        Args:
            db: Database session
            format: 'json', 'database', or 'both'

        Returns:
            Tuple of (success, filenames, error_message)
        """
        filenames = []
        errors = []

        if format in ('json', 'both'):
            success, filename, error = await cls.create_json_backup(db)
            if success:
                filenames.append(filename)
            else:
                errors.append(error)

        if format in ('database', 'both'):
            success, filename, error = await cls.create_database_backup()
            if success:
                filenames.append(filename)
            else:
                errors.append(error)

        overall_success = len(filenames) > 0 and len(errors) == 0
        error_message = '; '.join(errors) if errors else None

        return overall_success, filenames, error_message

    @classmethod
    async def cleanup_old_backups(cls, retention_days: int) -> int:
        """
        Remove backups older than retention period.

        Returns:
            Number of backups removed
        """
        cls.ensure_backup_dir()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        removed_count = 0

        # List all backup files first (synchronous)
        all_files = list(BACKUP_DIR.iterdir())

        for backup_file in all_files:
            if backup_file.is_file() and backup_file.name.startswith('backup_'):
                # Parse timestamp from filename
                try:
                    # Format: backup_YYYYMMDD_HHMMSS.ext.gz
                    # Need to remove .gz first, then get stem
                    stem = backup_file.stem
                    if stem.endswith('.json') or stem.endswith('.db'):
                        stem = backup_file.stem.rsplit('.', 1)[0]
                    timestamp_str = stem.replace('backup_', '')
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    # Make timezone-aware for comparison
                    file_date = file_date.replace(tzinfo=timezone.utc)

                    if file_date < cutoff_date:
                        # Run synchronous unlink in thread pool
                        await asyncio.to_thread(backup_file.unlink)
                        removed_count += 1
                        logger.info(f"Removed old backup: {backup_file.name}")
                except (ValueError, OSError) as e:
                    logger.warning(f"Could not process backup file {backup_file.name}: {e}")

        logger.info(f"Cleanup complete. Removed {removed_count} old backup(s).")
        return removed_count

    @classmethod
    async def list_backups(cls) -> List[dict]:
        """List all existing backups with metadata."""
        cls.ensure_backup_dir()
        backups = []

        for backup_file in sorted(BACKUP_DIR.iterdir(), reverse=True):
            if backup_file.is_file() and backup_file.name.startswith('backup_'):
                stat = backup_file.stat()

                # Determine format (handle .gz extension)
                suffix = backup_file.suffix
                stem = backup_file.stem
                if suffix == '.gz':
                    # Check the inner extension
                    if stem.endswith('.json'):
                        format_type = 'json'
                    elif stem.endswith('.db'):
                        format_type = 'database'
                    else:
                        format_type = 'unknown'
                elif suffix == '.json':
                    format_type = 'json'
                elif suffix == '.db':
                    format_type = 'database'
                else:
                    format_type = 'unknown'

                # Parse timestamp (handle .gz extension)
                try:
                    timestamp_str = stem
                    if suffix == '.gz':
                        # Remove the inner extension
                        if stem.endswith('.json') or stem.endswith('.db'):
                            timestamp_str = stem.rsplit('.', 1)[0]
                    timestamp_str = timestamp_str.replace('backup_', '')
                    created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    created_at = datetime.fromtimestamp(stat.st_ctime)

                backups.append({
                    'filename': backup_file.name,
                    'format': format_type,
                    'size_bytes': stat.st_size,
                    'created_at': created_at.isoformat(),
                })

        return backups
