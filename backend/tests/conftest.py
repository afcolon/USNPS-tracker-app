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
