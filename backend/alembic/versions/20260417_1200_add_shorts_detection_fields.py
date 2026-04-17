"""add_shorts_detection_fields

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-17 12:00:00.000000

This migration adds Issue #55 shorts detection fields:
- is_short_detected_at column to videos table (tracks when shorts were last checked)
- auto_detect_shorts column to settings table (enables automatic detection during imports)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    from sqlalchemy import text

    if dialect == 'sqlite':
        # Add is_short_detected_at to videos
        result = conn.execute(text("SELECT name FROM pragma_table_info('videos')"))
        existing_columns = {row[0] for row in result}

        if 'is_short_detected_at' not in existing_columns:
            conn.execute(text("ALTER TABLE videos ADD COLUMN is_short_detected_at DATETIME"))
            conn.commit()

        # Add auto_detect_shorts to settings
        result = conn.execute(text("SELECT name FROM pragma_table_info('settings')"))
        existing_columns = {row[0] for row in result}

        if 'auto_detect_shorts' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN auto_detect_shorts BOOLEAN DEFAULT 1 NOT NULL"))
            conn.commit()

    else:
        # PostgreSQL
        op.add_column('videos', sa.Column('is_short_detected_at', sa.DateTime(), nullable=True))
        op.add_column('settings', sa.Column('auto_detect_shorts', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        conn.execute(text("ALTER TABLE settings DROP COLUMN auto_detect_shorts"))
        conn.execute(text("ALTER TABLE videos DROP COLUMN is_short_detected_at"))
        conn.commit()
    else:
        op.drop_column('settings', 'auto_detect_shorts')
        op.drop_column('videos', 'is_short_detected_at')