import uuid
from sqlalchemy import Column, String, DateTime, Boolean, func, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Index on youtube_video_id for efficient lookups by YouTube video ID
    # Note: unique=True creates an implicit index, but explicit index=True
    # ensures clarity and allows SQLAlchemy to manage the index explicitly
    youtube_video_id = Column(String, unique=True, nullable=False, index=True)
    # Foreign key to channels table (optional, SET NULL on delete)
    channel_id = Column(String, ForeignKey("channels.id", ondelete="SET NULL"), nullable=True)
    # Embedded channel info (denormalized for independent filtering) - Issue #14
    channel_youtube_id = Column(String, nullable=True, index=True)
    channel_name = Column(String, nullable=True)
    channel_thumbnail_url = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    thumbnail_url = Column(String)
    video_url = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default='inbox', index=True) # 'inbox', 'saved', 'discarded'
    saved_at = Column(DateTime, index=True)
    discarded_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=func.now())
    # YouTube Shorts detection field - Issue #8
    is_short = Column(Boolean, default=False, nullable=False, index=True)

    channel = relationship("Channel", back_populates="videos")
