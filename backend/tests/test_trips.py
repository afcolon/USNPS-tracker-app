from httpx import AsyncClient


async def test_create_trip_single_hike(
    client: AsyncClient, seeded_park: int, seeded_hike: int
) -> None:
    response = await client.post("/trips", json={"park_id": seeded_park, "num_days": 2})
    assert response.status_code == 201
    trip = response.json()
    assert trip["park_id"] == seeded_park
    assert trip["num_days"] == 2
    assert trip["warning"] is not None  # only 1 hike for a 2-day trip
    assert len(trip["days"]) == 2  # both days present even though day 2 is empty
    assert trip["days"][0]["hikes"][0]["name"] == "Angels Landing Trail"
    assert trip["days"][1]["hikes"] == []


async def test_get_trip_round_trips(
    client: AsyncClient, seeded_park: int, seeded_hike: int
) -> None:
    create_response = await client.post("/trips", json={"park_id": seeded_park, "num_days": 1})
    trip_id = create_response.json()["id"]

    get_response = await client.get(f"/trips/{trip_id}")
    assert get_response.status_code == 200
    trip = get_response.json()
    assert trip["id"] == trip_id
    assert trip["days"][0]["hikes"][0]["name"] == "Angels Landing Trail"
    assert trip["warning"] is None  # not recomputed on GET, see docs/phase3-notes.md


async def test_create_trip_unknown_park_404(client: AsyncClient, seeded_park: int) -> None:
    response = await client.post("/trips", json={"park_id": 999, "num_days": 1})
    assert response.status_code == 404


async def test_get_trip_unknown_404(client: AsyncClient) -> None:
    response = await client.get("/trips/999")
    assert response.status_code == 404


async def test_create_trip_respects_max_difficulty(
    client: AsyncClient, seeded_park: int, seeded_hike: int
) -> None:
    # Angels Landing's effective difficulty is "strenuous" (override), so an
    # "easy" cap should exclude it entirely.
    response = await client.post(
        "/trips", json={"park_id": seeded_park, "num_days": 1, "max_difficulty": "easy"}
    )
    assert response.status_code == 201
    trip = response.json()
    assert trip["days"] == [{"day_number": 1, "hikes": []}]
