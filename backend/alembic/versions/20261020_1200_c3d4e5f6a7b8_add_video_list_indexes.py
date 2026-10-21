"""add_video_list_indexes

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6g7
Create Date: 2026-10-20 12:00:00.000000

Composite indexes matching the inbox, saved and QuickPlay list queries
(filter by status, optionally is_short, ordered by a date column).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = {
    'ix_videos_status_published_at': ['status', 'published_at'],
    'ix_videos_status_saved_at': ['status', 'saved_at'],
    'ix_videos_status_is_short_published_at': ['status', 'is_short', 'published_at'],
}


def upgrade() -> None:
    for name, columns in INDEXES.items():
        op.create_index(name, 'videos', columns, if_not_exists=True)


def downgrade() -> None:
    for name in INDEXES:
        op.drop_index(name, table_name='videos', if_exists=True)
