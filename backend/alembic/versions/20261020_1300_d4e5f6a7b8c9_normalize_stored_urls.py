"""normalize_stored_urls

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-20 13:00:00.000000

Rebuild any stored video or channel URL that doesn't point at youtube.com from its
ID. Earlier imports stored URLs from import files verbatim, so a crafted file
could store a javascript: link that the UI would render.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text(
        "UPDATE videos SET video_url = 'https://www.youtube.com/watch?v=' || youtube_video_id "
        "WHERE video_url NOT LIKE 'https://www.youtube.com/%'"
    ))
    conn.execute(text(
        "UPDATE channels SET youtube_url = 'https://www.youtube.com/channel/' || youtube_channel_id "
        "WHERE youtube_url NOT LIKE 'https://www.youtube.com/%'"
    ))


def downgrade() -> None:
    # Normalization is not reversible; the original URLs are not kept.
    pass
