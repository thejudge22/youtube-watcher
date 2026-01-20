"""add_backup_settings

Revision ID: 28c343f5222d
Revises: 75468de025be
Create Date: 2026-01-20 13:58:55.533739

This migration adds backup settings columns to the settings table for Issue #12.
Adds automatic backup configuration and status tracking.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28c343f5222d'
down_revision: Union[str, None] = '75468de025be'
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

        # Add backup_enabled column if not exists
        if 'backup_enabled' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN backup_enabled BOOLEAN DEFAULT 0 NOT NULL"))
            conn.commit()

        # Add backup_schedule column if not exists
        if 'backup_schedule' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN backup_schedule VARCHAR DEFAULT 'daily' NOT NULL"))
            conn.commit()

        # Add backup_time column if not exists
        if 'backup_time' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN backup_time VARCHAR DEFAULT '02:00' NOT NULL"))
            conn.commit()

        # Add backup_format column if not exists
        if 'backup_format' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN backup_format VARCHAR DEFAULT 'json' NOT NULL"))
            conn.commit()

        # Add backup_retention_days column if not exists
        if 'backup_retention_days' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN backup_retention_days INTEGER DEFAULT 30 NOT NULL"))
            conn.commit()

        # Add last_backup_at column if not exists
        if 'last_backup_at' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_backup_at DATETIME"))
            conn.commit()

        # Add last_backup_status column if not exists
        if 'last_backup_status' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_backup_status VARCHAR"))
            conn.commit()

        # Add last_backup_error column if not exists
        if 'last_backup_error' not in existing_columns:
            conn.execute(text("ALTER TABLE settings ADD COLUMN last_backup_error VARCHAR"))
            conn.commit()

    else:
        # PostgreSQL: add columns
        op.add_column('settings', sa.Column('backup_enabled', sa.Boolean(), server_default='false', nullable=False))
        op.add_column('settings', sa.Column('backup_schedule', sa.String(), server_default='daily', nullable=False))
        op.add_column('settings', sa.Column('backup_time', sa.String(), server_default='02:00', nullable=False))
        op.add_column('settings', sa.Column('backup_format', sa.String(), server_default='json', nullable=False))
        op.add_column('settings', sa.Column('backup_retention_days', sa.Integer(), server_default=30, nullable=False))
        op.add_column('settings', sa.Column('last_backup_at', sa.DateTime(), nullable=True))
        op.add_column('settings', sa.Column('last_backup_status', sa.String(), nullable=True))
        op.add_column('settings', sa.Column('last_backup_error', sa.String(), nullable=True))


def downgrade() -> None:
    # Get the database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == 'sqlite':
        # SQLite: Drop columns
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_backup_error"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_backup_status"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN last_backup_at"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN backup_retention_days"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN backup_format"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN backup_time"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN backup_schedule"))
        conn.execute(text("ALTER TABLE settings DROP COLUMN backup_enabled"))
        conn.commit()
    else:
        # PostgreSQL: Drop columns
        op.drop_column('settings', 'last_backup_error')
        op.drop_column('settings', 'last_backup_status')
        op.drop_column('settings', 'last_backup_at')
        op.drop_column('settings', 'backup_retention_days')
        op.drop_column('settings', 'backup_format')
        op.drop_column('settings', 'backup_time')
        op.drop_column('settings', 'backup_schedule')
        op.drop_column('settings', 'backup_enabled')
