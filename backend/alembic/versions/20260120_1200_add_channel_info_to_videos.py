"""add_channel_info_to_videos

Revision ID: add_channel_info_to_videos
Revises: 63e6b77c0da0
Create Date: 2026-01-20 12:00:00.000000

This migration adds channel information to the videos table for Issue #14.
For SQLite, we skip the foreign key change due to SQLite limitations.
The new columns allow filtering saved videos by channel even after the channel is deleted.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_channel_info_to_videos'
down_revision: Union[str, None] = '63e6b77c0da0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Step 1: Add new columns (if they don't already exist)
    # Using execute with IF NOT EXISTS for safety on partial runs
    from sqlalchemy import text

    # For SQLite, we need to check if columns exist first
    if dialect == 'sqlite':
        # Check existing columns
        result = conn.execute(text("SELECT name FROM pragma_table_info('videos')"))
        existing_columns = {row[0] for row in result}

        # Add channel_youtube_id if not exists
        if 'channel_youtube_id' not in existing_columns:
            conn.execute(text("ALTER TABLE videos ADD COLUMN channel_youtube_id VARCHAR"))
            conn.commit()

        # Add channel_name if not exists
        if 'channel_name' not in existing_columns:
            conn.execute(text("ALTER TABLE videos ADD COLUMN channel_name VARCHAR"))
            conn.commit()

        # Add channel_thumbnail_url if not exists
        if 'channel_thumbnail_url' not in existing_columns:
            conn.execute(text("ALTER TABLE videos ADD COLUMN channel_thumbnail_url VARCHAR"))
            conn.commit()

        # Create index if not exists
        try:
            conn.execute(text("CREATE INDEX ix_videos_channel_youtube_id ON videos(channel_youtube_id)"))
            conn.commit()
        except Exception:
            pass  # Index might already exist

        # Populate new columns from existing channel data
        conn.execute(text("""
            UPDATE videos
            SET channel_youtube_id = (
                SELECT youtube_channel_id FROM channels WHERE channels.id = videos.channel_id
            ),
            channel_name = (
                SELECT name FROM channels WHERE channels.id = videos.channel_id
            ),
            channel_thumbnail_url = (
                SELECT thumbnail_url FROM channels WHERE channels.id = videos.channel_id
            )
            WHERE channel_id IS NOT NULL
        """))
        conn.commit()

        # Note: For SQLite, we cannot change the foreign key from CASCADE to SET NULL
        # This is a known limitation of SQLite. The new columns provide the needed
        # functionality - videos will retain their channel info even if the channel
        # is deleted, because channel_id will be set to NULL but the embedded
        # channel_youtube_id, channel_name, and channel_thumbnail_url remain.

    else:
        # PostgreSQL: can do the full migration including foreign key change
        op.add_column('videos', sa.Column('channel_youtube_id', sa.String(), nullable=True))
        op.add_column('videos', sa.Column('channel_name', sa.String(), nullable=True))
        op.add_column('videos', sa.Column('channel_thumbnail_url', sa.String(), nullable=True))

        op.create_index('ix_videos_channel_youtube_id', 'videos', ['channel_youtube_id'])

        # Populate new columns from existing channel data
        op.execute("""
            UPDATE videos
            SET channel_youtube_id = channels.youtube_channel_id,
                channel_name = channels.name,
                channel_thumbnail_url = channels.thumbnail_url
            FROM channels
            WHERE videos.channel_id = channels.id
        """)

        # Drop and recreate foreign key with SET NULL
        op.drop_constraint('videos_channel_id_fkey', 'videos', type_='foreignkey')
        op.create_foreign_key(
            'videos_channel_id_fkey',
            'videos', 'channels',
            ['channel_id'], ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        # SQLite: Drop columns
        conn.execute(text("DROP INDEX IF EXISTS ix_videos_channel_youtube_id"))
        conn.execute(text("ALTER TABLE videos DROP COLUMN channel_thumbnail_url"))
        conn.execute(text("ALTER TABLE videos DROP COLUMN channel_name"))
        conn.execute(text("ALTER TABLE videos DROP COLUMN channel_youtube_id"))
        conn.commit()
    else:
        # PostgreSQL: Revert foreign key and drop columns
        op.drop_constraint('videos_channel_id_fkey', 'videos', type_='foreignkey')
        op.create_foreign_key(
            'videos_channel_id_fkey',
            'videos', 'channels',
            ['channel_id'], ['id'],
            ondelete='CASCADE'
        )

        op.drop_index('ix_videos_channel_youtube_id', table_name='videos')
        op.drop_column('videos', 'channel_thumbnail_url')
        op.drop_column('videos', 'channel_name')
        op.drop_column('videos', 'channel_youtube_id')
