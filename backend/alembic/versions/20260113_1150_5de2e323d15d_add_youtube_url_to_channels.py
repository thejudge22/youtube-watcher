"""add_youtube_url_to_channels

Revision ID: 5de2e323d15d
Revises: 001
Create Date: 2026-01-13 11:50:27.707384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5de2e323d15d'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For SQLite, we need to use batch operations to modify the table
    with op.batch_alter_table('channels', schema=None) as batch_op:
        # Add youtube_url column as nullable first
        batch_op.add_column(sa.Column('youtube_url', sa.String(), nullable=True))
    
    # Populate youtube_url for existing channels using their youtube_channel_id
    op.execute("""
        UPDATE channels
        SET youtube_url = 'https://www.youtube.com/channel/' || youtube_channel_id
        WHERE youtube_url IS NULL
    """)
    
    # Recreate table with youtube_url as non-nullable
    with op.batch_alter_table('channels', schema=None) as batch_op:
        batch_op.alter_column('youtube_url', nullable=False)


def downgrade() -> None:
    # Remove youtube_url column from channels table
    op.drop_column('channels', 'youtube_url')
