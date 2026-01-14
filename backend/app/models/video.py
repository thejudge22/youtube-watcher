import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_video_id = Column(String, unique=True, nullable=False)
    channel_id = Column(String, ForeignKey("channels.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(String)
    thumbnail_url = Column(String)
    video_url = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default='inbox', index=True) # 'inbox', 'saved', 'discarded'
    saved_at = Column(DateTime, index=True)
    discarded_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=func.now())

    channel = relationship("Channel")
