"""Exports and JSON backups keep channel info for saved videos from unsubscribed channels."""
import gzip
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.services import backup_service
from app.services.backup_service import BackupService, get_backup_dir
from tests.factories import make_video

EXPECTED = {"channel_youtube_id": "UC-gone", "channel_name": "Gone Channel",
            "channel_url": "https://www.youtube.com/channel/UC-gone"}


def unsubscribed_video():
    return make_video(status="saved", channel_id=None, channel_youtube_id="UC-gone",
                      channel_name="Gone Channel")


async def add_unsubscribed_video(db_session):
    db_session.add(unsubscribed_video())
    await db_session.commit()


async def test_export_all_keeps_unsubscribed_channel_info(client, db_session):
    await add_unsubscribed_video(db_session)
    data = (await client.get("/api/import-export/export/all")).json()
    assert EXPECTED.items() <= data["saved_videos"][0].items()


async def test_export_saved_videos_keeps_unsubscribed_channel_info(client, db_session):
    await add_unsubscribed_video(db_session)
    data = (await client.get("/api/import-export/export/saved-videos")).json()
    assert EXPECTED.items() <= data["saved_videos"][0].items()


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    path = tmp_path / "data" / "app.db"
    path.parent.mkdir()
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(unsubscribed_video())
        session.commit()
    engine.dispose()
    monkeypatch.setattr(backup_service, "get_database_path", lambda: path)
    return path


async def test_json_backup_keeps_unsubscribed_channel_info(file_db):
    ok, name, err = await BackupService.create_json_backup(None)
    assert ok, err
    with gzip.open(get_backup_dir() / name, "rt", encoding="utf-8") as f:
        video = json.load(f)["saved_videos"][0]
    assert EXPECTED.items() <= video.items()
