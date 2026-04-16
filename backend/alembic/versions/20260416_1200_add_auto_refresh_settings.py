"""add_auto_refresh_settings

Revision ID: a1b2c3d4e5f6
Revises: 28c343f5222d
Create Date: 2026-04-16 12:00:00.000000

This migration adds auto-refresh settings columns to the settings table for Issue #54.
Adds automatic feed refresh configuration and status tracking.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '28c343f5222d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    from sqlalchemy import text

    if dialect == 'sqlite':
        # Check existing columns
        result = conn.execute(text("SELECT name FROM pragma_table_info('settings')"))
        existing_columns = {row[0] for row in result}

        if 'auto_refresh_enabled' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN auto_refresh_enabled BOOLEAN DEFAULT 0 NOT NULL"))
            conn.commit()

        if 'auto_refresh_interval' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN auto_refresh_interval VARCHAR DEFAULT '6h' NOT NULL"))
            conn.commit()

        if 'last_refresh_at' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_refresh_at DATETIME"))
            conn.commit()

        if 'last_refresh_status' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_refresh_status VARCHAR"))
            conn.commit()

        if 'last_refresh_error' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_refresh_error VARCHAR"))
            conn.commit()

    else:
        # PostgreSQL: add columns
        op.add_column('settings', sa.Column('auto_refresh_enabled', sa.Boolean(), server_default='false', nullable=False))
        op.add_column('settings', sa.Column('auto_refresh_interval', sa.String(), server_default='6h', nullable=False))
        op.add_column('settings', sa.Column('last_refresh_at', sa.DateTime(), nullable=True))
        op.add_column('settings', sa.Column('last_refresh_status', sa.String(), nullable=True))
        op.add_column('settings', sa.Column('last_refresh_error', sa.String(), nullable=True))


def downgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_refresh_error"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_refresh_status"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_refresh_at"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN auto_refresh_interval"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN auto_refresh_enabled"))
        conn.commit()
    else:
        # PostgreSQL: Drop columns
        op.drop_column('settings', 'last_refresh_error')
        op.drop_column('settings', 'last_refresh_status')
        op.drop_column('settings', 'last_refresh_at')
        op.drop_column('settings', 'auto_refresh_interval')
        op.drop_column('settings', 'auto_refresh_enabled')