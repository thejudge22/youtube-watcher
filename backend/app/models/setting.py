from sqlalchemy import Column, String, Float, DateTime, func
from ..database import Base

class Setting(Base):
    """
    Global application settings.
    This is a singleton table - there should only be one row with id='1'.
    """
    __tablename__ = "settings"

    id = Column(String, primary_key=True, default="1")
    http_timeout = Column(Float, default=10.0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
