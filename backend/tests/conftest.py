from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.main import app
from app.models import Hike, Park, User


@pytest.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield factory
    await engine.dispose()


@pytest.fixture
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_park(session_factory) -> int:
    async with session_factory() as session:
        session.add(User(name="Park Explorer", email="owner@example.com"))
        park = Park(
            nps_park_code="yell",
            name="Yellowstone",
            states="ID,MT,WY",
            description="The first national park.",
            lat=44.6,
            lng=-110.5,
        )
        session.add(park)
        await session.commit()
        return park.id


@pytest.fixture
async def seeded_hike(session_factory, seeded_park: int) -> int:
    async with session_factory() as session:
        hike = Hike(
            park_id=seeded_park,
            name="Angels Landing Trail",
            distance_miles=4.8,
            elevation_gain_ft=1745,
            difficulty="moderate",
            difficulty_score=129.4,
            difficulty_override="strenuous",
            difficulty_override_reason="Chain-assisted exposure, not distance/elevation.",
            hike_type="out_and_back",
            trailhead_lat=37.3,
            trailhead_lng=-113.0,
            estimated_duration_min=240,
            source="alltrails",
            source_id="10006571",
            source_url="https://www.alltrails.com/trail/us/utah/angels-landing-trail",
            avg_rating=4.9,
            reviews_count=41568,
        )
        session.add(hike)
        await session.commit()
        return hike.id


@pytest.fixture
async def seeded_hike_long(session_factory, seeded_park: int) -> int:
    """A 5-hour hike with a modest rating (loses the quality-score tie-break
    against Angels Landing), used to test that a hike which doesn't fit the
    remaining hours/day budget is correctly reported as dropped."""
    async with session_factory() as session:
        hike = Hike(
            park_id=seeded_park,
            name="West Rim Trail",
            distance_miles=14.2,
            elevation_gain_ft=3600,
            difficulty="strenuous",
            difficulty_score=612.0,
            difficulty_override=None,
            difficulty_override_reason=None,
            hike_type="point_to_point",
            trailhead_lat=37.3,
            trailhead_lng=-113.0,
            estimated_duration_min=300,
            source="alltrails",
            source_id="10006573",
            source_url="https://www.alltrails.com/trail/us/utah/west-rim-trail",
            avg_rating=4.6,
            reviews_count=800,
        )
        session.add(hike)
        await session.commit()
        return hike.id


@pytest.fixture
async def seeded_three_equal_hikes(session_factory, seeded_park: int) -> None:
    """Three hikes with identical duration/quality -- used to reproduce the
    best-fit-decreasing packer's tendency to concentrate everything into the
    earliest day(s), leaving later days empty even though every hike got
    scheduled."""
    async with session_factory() as session:
        for i in range(3):
            session.add(
                Hike(
                    park_id=seeded_park,
                    name=f"Equal Hike {i + 1}",
                    distance_miles=5.0,
                    elevation_gain_ft=0,
                    difficulty="easy",
                    difficulty_score=50.0,
                    difficulty_override=None,
                    difficulty_override_reason=None,
                    hike_type="loop",
                    trailhead_lat=37.2,
                    trailhead_lng=-113.0,
                    estimated_duration_min=150,
                    source="alltrails",
                    source_id=f"equal-hike-{i + 1}",
                    source_url=None,
                    avg_rating=4.5,
                    reviews_count=100,
                )
            )
        await session.commit()


@pytest.fixture
async def seeded_hike_no_duration(session_factory, seeded_park: int) -> int:
    """A hike with no `estimated_duration_min` -- mirrors Angels Landing's real
    AllTrails data (see docs/phase2-notes.md), used to test the planner's
    pace/elevation fallback estimate end-to-end via the API."""
    async with session_factory() as session:
        hike = Hike(
            park_id=seeded_park,
            name="Canyon Overlook Trail",
            distance_miles=1.0,
            elevation_gain_ft=200,
            difficulty="easy",
            difficulty_score=10.0,
            difficulty_override=None,
            difficulty_override_reason=None,
            hike_type="out_and_back",
            trailhead_lat=37.25,
            trailhead_lng=-113.0,
            estimated_duration_min=None,
            source="alltrails",
            source_id="10006572",
            source_url="https://www.alltrails.com/trail/us/utah/canyon-overlook-trail",
            avg_rating=4.8,
            reviews_count=5000,
        )
        session.add(hike)
        await session.commit()
        return hike.id
