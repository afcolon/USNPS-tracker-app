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
    # Regression check: the warning must reflect hikes actually *scheduled*,
    # not just the raw count available before difficulty filtering -- a
    # park with 1 hike but every day empty after filtering must still warn.
    assert trip["warning"] is not None


async def test_create_trip_rejects_non_positive_num_days(
    client: AsyncClient, seeded_park: int
) -> None:
    response = await client.post("/trips", json={"park_id": seeded_park, "num_days": 0})
    assert response.status_code == 422


async def test_trip_hike_duration_falls_back_when_unset(
    client: AsyncClient, seeded_park: int, seeded_hike_no_duration: int
) -> None:
    # Canyon Overlook has no estimated_duration_min (1.0 mi, 200 ft gain), so
    # the response should carry the planner's fallback estimate:
    # 1.0 * 30 + 200 / 50 = 34 minutes -- see app.planner.estimate_duration_min.
    response = await client.post("/trips", json={"park_id": seeded_park, "num_days": 1})
    assert response.status_code == 201
    hike = response.json()["days"][0]["hikes"][0]
    assert hike["estimated_duration_min"] is None
    assert hike["effective_duration_min"] == 34
