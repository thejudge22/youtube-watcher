from datetime import datetime
from pydantic import BaseModel, Field


class ChannelExport(BaseModel):
    youtube_channel_id: str
    name: str
    youtube_url: str


class VideoExport(BaseModel):
    youtube_video_id: str
    title: str
    video_url: str
    channel_youtube_id: str | None = None
    channel_name: str | None = None
    channel_url: str | None = None
    saved_at: datetime | None = None
    published_at: datetime | None = None


class ExportData(BaseModel):
    version: str = "1.0"
    exported_at: datetime
    channels: list[ChannelExport]
    saved_videos: list[VideoExport]


class ImportChannelsRequest(BaseModel):
    channels: list[ChannelExport] = Field(max_length=5000)


class ImportVideosRequest(BaseModel):
    videos: list[VideoExport] = Field(max_length=100000)


class ImportUrlsRequest(BaseModel):
    urls: list[str] = Field(max_length=1000)


class ImportPlaylistRequest(BaseModel):
    url: str


class ImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    errors: list[str]


class ChannelImportResult(ImportResult):
    pass


class VideoImportResult(ImportResult):
    pass
