from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Hike, HikeHighlight


async def _add_hike(session_factory: async_sessionmaker[AsyncSession], park_id: int) -> int:
    async with session_factory() as session:
        hike = Hike(
            park_id=park_id,
            name="Angels Landing Trail",
            distance_miles=4.8,
            elevation_gain_ft=1745,
            difficulty="strenuous",
            difficulty_score=129.4,
            difficulty_override="strenuous",
            difficulty_override_reason="Chain-assisted exposure, not distance/elevation.",
            hike_type="out_and_back",
            trailhead_lat=44.6,
            trailhead_lng=-110.5,
            estimated_duration_min=None,
            source="alltrails",
            source_id="10006571",
            source_url="https://www.alltrails.com/trail/us/utah/angels-landing-trail",
        )
        session.add(hike)
        await session.flush()
        session.add(HikeHighlight(hike_id=hike.id, text="Chain-assisted final scramble."))
        await session.commit()
        return hike.id


async def test_list_hikes_for_park(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession], seeded_park: int
) -> None:
    await _add_hike(session_factory, seeded_park)

    response = await client.get(f"/parks/{seeded_park}/hikes")
    assert response.status_code == 200
    hikes = response.json()
    assert len(hikes) == 1
    assert hikes[0]["name"] == "Angels Landing Trail"
    assert hikes[0]["difficulty"] == "strenuous"
    assert hikes[0]["difficulty_override"] == "strenuous"
    assert hikes[0]["highlights"] == [
        {"text": "Chain-assisted final scramble.", "source_url": None}
    ]


async def test_list_hikes_empty_for_park_with_none(client: AsyncClient, seeded_park: int) -> None:
    response = await client.get(f"/parks/{seeded_park}/hikes")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_hikes_unknown_park_404(client: AsyncClient) -> None:
    response = await client.get("/parks/999/hikes")
    assert response.status_code == 404
