"""Shared test fixtures for pytest."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models.channel import Channel
from app.models.video import Video
from datetime import datetime, UTC

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with StaticPool to maintain same in-memory DB across connections
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    """Override the get_db dependency to use test database."""
    async with TestingSessionLocal() as session:
        yield session


# Override the dependency before any tests run
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """Create a database session for direct DB operations in tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def sample_channel(db_session):
    """Create a sample channel for testing."""
    channel = Channel(
        youtube_channel_id="UC-test123",
        name="Test Channel",
        rss_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC-test123"
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)
    return channel


@pytest_asyncio.fixture
async def sample_video(db_session, sample_channel):
    """Create a sample video for testing."""
    video = Video(
        youtube_video_id="test-video-123",
        channel_id=sample_channel.id,
        title="Test Video",
        description="Test Description",
        video_url="https://www.youtube.com/watch?v=test-video-123",
        published_at=datetime.now(UTC),
        status="inbox"
    )
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return video