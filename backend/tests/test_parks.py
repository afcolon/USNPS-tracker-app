from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.main import app
from app.models import Park, User


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        session.add(User(name="Park Explorer", email="owner@example.com"))
        session.add(
            Park(
                nps_park_code="yell",
                name="Yellowstone",
                states="ID,MT,WY",
                description="The first national park.",
                lat=44.6,
                lng=-110.5,
            )
        )
        await session.commit()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_list_parks_not_visited(client: AsyncClient) -> None:
    response = await client.get("/parks")
    assert response.status_code == 200
    parks = response.json()
    assert len(parks) == 1
    assert parks[0]["name"] == "Yellowstone"
    assert parks[0]["visited"] is False
    assert parks[0]["visited_date"] is None


async def test_mark_and_unmark_visited(client: AsyncClient) -> None:
    response = await client.get("/parks")
    park_id = response.json()[0]["id"]

    response = await client.post(f"/parks/{park_id}/visit", json={"visited_date": "2024-07-04"})
    assert response.status_code == 204

    response = await client.get("/parks")
    park = response.json()[0]
    assert park["visited"] is True
    assert park["visited_date"] == "2024-07-04"

    response = await client.delete(f"/parks/{park_id}/visit")
    assert response.status_code == 204

    response = await client.get("/parks")
    assert response.json()[0]["visited"] is False


async def test_mark_visited_unknown_park_404(client: AsyncClient) -> None:
    response = await client.post("/parks/999/visit", json={})
    assert response.status_code == 404
