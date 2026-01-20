"""add_is_short_to_videos

Revision ID: 75468de025be
Revises: add_channel_info_to_videos
Create Date: 2026-01-20 13:37:33.745417

This migration adds is_short column to videos table for Issue #8.
YouTube Shorts Separation - allows filtering inbox videos by Shorts status.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75468de025be'
down_revision: Union[str, None] = 'add_channel_info_to_videos'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Check if column exists first for safety
    from sqlalchemy import text

    if dialect == 'sqlite':
        # Check existing columns
        result = conn.execute(text("SELECT name FROM pragma_table_info('videos')"))
        existing_columns = {row[0] for row in result}

        # Add is_short column if not exists
        if 'is_short' not in existing_columns:
            conn.execute(text("ALTER TABLE videos ADD COLUMN is_short BOOLEAN DEFAULT 0 NOT NULL"))
            conn.commit()

        # Create index if not exists
        try:
            conn.execute(text("CREATE INDEX ix_videos_is_short ON videos(is_short)"))
            conn.commit()
        except Exception:
            pass  # Index might already exist

    else:
        # PostgreSQL: add column with default
        op.add_column('videos', sa.Column('is_short', sa.Boolean(), server_default='false', nullable=False))
        op.create_index('ix_videos_is_short', 'videos', ['is_short'])


def downgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        # SQLite: Drop column and index
        conn.execute(text("DROP INDEX IF EXISTS ix_videos_is_short"))
        conn.execute(text("ALTER TABLE videos DROP COLUMN is_short"))
        conn.commit()
    else:
        # PostgreSQL: Drop index and column
        op.drop_index('ix_videos_is_short', table_name='videos')
        op.drop_column('videos', 'is_short')
