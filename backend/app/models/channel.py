import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base

class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_channel_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    rss_url = Column(String, nullable=False)
    youtube_url = Column(String, nullable=False)
    thumbnail_url = Column(String)
    last_checked = Column(DateTime)
    last_video_id = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to videos
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")
