"""Tests for backup paths, the SQLite backup API, and manual-backup status."""
import gzip
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database import Base
from app.models.setting import Setting
from app.services import backup_service
from app.services.backup_service import BackupService, get_backup_dir, get_database_path
from tests.factories import make_channel


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    """A real SQLite file with the app schema and one channel."""
    path = tmp_path / "data" / "app.db"
    path.parent.mkdir()
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(make_channel())
        session.commit()
    engine.dispose()
    monkeypatch.setattr(backup_service, "get_database_path", lambda: path)
    return path


def test_database_path_from_url(monkeypatch):
    monkeypatch.setattr(app_settings, "database_url", "sqlite+aiosqlite:///./data/x.db")
    assert get_database_path() == Path("data/x.db")
    monkeypatch.setattr(app_settings, "database_url", "sqlite+aiosqlite:////srv/x.db")
    assert get_database_path() == Path("/srv/x.db")


def test_backup_dir_next_to_database(file_db):
    assert get_backup_dir() == file_db.parent / "backups"


async def test_database_backup_is_valid_sqlite(file_db, tmp_path):
    ok, name, err = await BackupService.create_database_backup()
    assert ok and err is None

    restored = tmp_path / "restored.db"
    with gzip.open(get_backup_dir() / name, "rb") as src, open(restored, "wb") as dst:
        shutil.copyfileobj(src, dst)
    assert sqlite3.connect(restored).execute("select count(*) from channels").fetchone() == (1,)
    assert not any(p.name.startswith(".tmp_") for p in get_backup_dir().iterdir())


async def test_manual_backup_failure_is_recorded(client, db_session, mocker):
    db_session.add(Setting(id="1"))
    await db_session.commit()
    mocker.patch(
        "app.routers.backup.BackupService.create_backup",
        AsyncMock(return_value=(False, [], "boom")),
    )

    response = await client.post("/api/backup/run", json={"format": "json"})
    assert response.status_code == 200

    status = (await client.get("/api/backup/status")).json()
    assert status["last_backup_status"] == "failed"
    assert status["last_backup_error"] == "boom"
