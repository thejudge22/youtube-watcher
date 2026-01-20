"""
Pydantic schemas for settings API.

Issue #12: Scheduled Backups - Added backup settings schemas.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
import re


class BackupSettings(BaseModel):
    """Schema for backup settings."""
    backup_enabled: bool = False
    backup_schedule: str = Field(default='daily', pattern='^(daily|weekly|monthly)$')
    backup_time: str = Field(default='02:00', pattern=r'^\d{2}:\d{2}$')
    backup_format: str = Field(default='json', pattern='^(json|database|both)$')
    backup_retention_days: int = Field(default=30, ge=1, le=365)

    @field_validator('backup_time')
    @classmethod
    def validate_time_format(cls, v):
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError('Invalid time format. Use HH:MM (24-hour)')
        return v


class BackupStatus(BaseModel):
    """Schema for backup status information."""
    last_backup_at: Optional[datetime]
    last_backup_status: Optional[str]
    last_backup_error: Optional[str]


class BackupInfo(BaseModel):
    """Schema for individual backup file info."""
    filename: str
    format: str
    size_bytes: int
    created_at: str


class BackupListResponse(BaseModel):
    """Schema for list of backups response."""
    backups: List[BackupInfo]
    total_count: int
    total_size_bytes: int


class AppSettings(BaseModel):
    """Complete application settings."""
    http_timeout: float
    backup_enabled: bool
    backup_schedule: str
    backup_time: str
    backup_format: str
    backup_retention_days: int
    last_backup_at: Optional[datetime]
    last_backup_status: Optional[str]
    last_backup_error: Optional[str]


class AppSettingsUpdate(BaseModel):
    """Schema for updating settings."""
    http_timeout: Optional[float] = Field(default=None, ge=1.0, le=300.0)
    backup_enabled: Optional[bool] = None
    backup_schedule: Optional[str] = Field(default=None, pattern='^(daily|weekly|monthly)$')
    backup_time: Optional[str] = Field(default=None, pattern=r'^\d{2}:\d{2}$')
    backup_format: Optional[str] = Field(default=None, pattern='^(json|database|both)$')
    backup_retention_days: Optional[int] = Field(default=None, ge=1, le=365)

    @field_validator('backup_time')
    @classmethod
    def validate_time_format(cls, v):
        if v is not None and not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError('Invalid time format. Use HH:MM (24-hour)')
        return v


class ManualBackupRequest(BaseModel):
    """Schema for triggering manual backup."""
    format: str = Field(default='json', pattern='^(json|database|both)$')


class ManualBackupResponse(BaseModel):
    """Schema for manual backup response."""
    success: bool
    filenames: List[str]
    error: Optional[str]
