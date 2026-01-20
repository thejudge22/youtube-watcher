from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, func
from ..database import Base

class Setting(Base):
    """
    Global application settings.
    This is a singleton table - there should only be one row with id='1'.
    """
    __tablename__ = "settings"

    id = Column(String, primary_key=True, default="1")
    http_timeout = Column(Float, default=10.0, nullable=False)

    # Issue #12: Backup settings
    backup_enabled = Column(Boolean, default=False, nullable=False)
    backup_schedule = Column(String, default='daily', nullable=False)  # 'daily', 'weekly', 'monthly'
    backup_time = Column(String, default='02:00', nullable=False)  # HH:MM format
    backup_format = Column(String, default='json', nullable=False)  # 'json', 'database', 'both'
    backup_retention_days = Column(Integer, default=30, nullable=False)

    # Issue #12: Backup status
    last_backup_at = Column(DateTime, nullable=True)
    last_backup_status = Column(String, nullable=True)  # 'success', 'failed'
    last_backup_error = Column(String, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
