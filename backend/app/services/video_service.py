"""
Video service for abstracting query construction logic.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.video import Video
from ..exceptions import ValidationError


class VideoService:
    """Service for video data access with reusable query construction."""

    @staticmethod
    async def get_videos(
        db: AsyncSession,
        status: str,
        limit: int,
        offset: int,
        channel_id: Optional[str] = None,
        channel_youtube_id: Optional[str] = None,
        is_short: Optional[bool] = None,  # Issue #8: Shorts filter
        sort_by: Optional[str] = None,
        order: str = 'desc'
    ) -> List[Video]:
        """
        Get videos with filtering, sorting, and pagination.

        Args:
            db: Database session
            status: Video status to filter by ('inbox', 'saved', 'discarded')
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            channel_id: Optional internal channel ID to filter by (for inbox)
            channel_youtube_id: Optional YouTube channel ID to filter by (for saved videos)
            is_short: Optional Shorts filter (True=only Shorts, False=only regular, None=all) - Issue #8
            sort_by: Column to sort by ('published_at', 'saved_at', 'discarded_at')
            order: Sort order ('asc' or 'desc')

        Returns:
            List of Video objects with channel relationship loaded
        """
        # Validate sort_by if provided
        if sort_by and sort_by not in ['published_at', 'saved_at', 'discarded_at']:
            raise ValidationError(
                "sort_by must be 'published_at', 'saved_at', or 'discarded_at'",
                field="sort_by"
            )

        # Validate order
        if order not in ['asc', 'desc']:
            raise ValidationError("order must be 'asc' or 'desc'", field="order")

        # Build base query with eager loading of channel relationship
        query = (
            select(Video)
            .options(selectinload(Video.channel))
            .where(Video.status == status)
        )

        # Apply channel filters
        if channel_id:
            query = query.where(Video.channel_id == channel_id)
        if channel_youtube_id:
            query = query.where(Video.channel_youtube_id == channel_youtube_id)

        # Apply Shorts filter (Issue #8)
        if is_short is not None:
            query = query.where(Video.is_short == is_short)

        # Apply sorting
        # Default to published_at if no sort_by is specified
        sort_column_name = sort_by if sort_by else 'published_at'
        sort_column = getattr(Video, sort_column_name)

        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute and return results
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_discarded_videos(
        db: AsyncSession,
        cutoff_date: datetime,
        limit: int,
        offset: int
    ) -> List[Video]:
        """
        Get discarded videos since a specific cutoff date.

        Args:
            db: Database session
            cutoff_date: Only return videos discarded after this date
            limit: Maximum number of videos to return
            offset: Number of videos to skip

        Returns:
            List of Video objects with channel relationship loaded
        """
        # Build query for discarded videos after cutoff date
        query = (
            select(Video)
            .options(selectinload(Video.channel))
            .where(Video.status == 'discarded')
            .where(Video.discarded_at >= cutoff_date)
            .order_by(Video.discarded_at.desc())
            .limit(limit)
            .offset(offset)
        )

        # Execute and return results
        result = await db.execute(query)
        return result.scalars().all()
