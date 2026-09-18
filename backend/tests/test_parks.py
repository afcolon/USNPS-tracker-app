from httpx import AsyncClient


async def test_list_parks_not_visited(client: AsyncClient, seeded_park: int) -> None:
    response = await client.get("/parks")
    assert response.status_code == 200
    parks = response.json()
    assert len(parks) == 1
    assert parks[0]["name"] == "Yellowstone"
    assert parks[0]["visited"] is False
    assert parks[0]["visited_date"] is None


async def test_mark_and_unmark_visited(client: AsyncClient, seeded_park: int) -> None:
    response = await client.post(f"/parks/{seeded_park}/visit", json={"visited_date": "2024-07-04"})
    assert response.status_code == 204

    response = await client.get("/parks")
    park = response.json()[0]
    assert park["visited"] is True
    assert park["visited_date"] == "2024-07-04"

    response = await client.delete(f"/parks/{seeded_park}/visit")
    assert response.status_code == 204

    response = await client.get("/parks")
    assert response.json()[0]["visited"] is False


async def test_mark_visited_unknown_park_404(client: AsyncClient, seeded_park: int) -> None:
    response = await client.post("/parks/999/visit", json={})
    assert response.status_code == 404
