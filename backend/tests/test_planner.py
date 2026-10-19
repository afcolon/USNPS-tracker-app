from dataclasses import dataclass

import pytest

from app.planner import build_itinerary, estimate_duration_min, quality_score


@dataclass
class FakeHike:
    id: int
    distance_miles: float
    elevation_gain_ft: float
    difficulty: str
    difficulty_override: str | None
    estimated_duration_min: int | None
    avg_rating: float | None
    reviews_count: int | None
    trailhead_lat: float = 37.3
    trailhead_lng: float = -113.0


def make_hike(
    id: int,
    distance_miles: float,
    elevation_gain_ft: float,
    difficulty: str = "moderate",
    avg_rating: float | None = 4.5,
    reviews_count: int | None = 1000,
    estimated_duration_min: int | None = None,
    difficulty_override: str | None = None,
    trailhead_lat: float = 37.3,
    trailhead_lng: float = -113.0,
) -> FakeHike:
    return FakeHike(
        id=id,
        distance_miles=distance_miles,
        elevation_gain_ft=elevation_gain_ft,
        difficulty=difficulty,
        difficulty_override=difficulty_override,
        estimated_duration_min=estimated_duration_min,
        avg_rating=avg_rating,
        reviews_count=reviews_count,
        trailhead_lat=trailhead_lat,
        trailhead_lng=trailhead_lng,
    )


def test_estimate_duration_min_uses_known_value_when_present():
    hike = make_hike(1, distance_miles=2.0, elevation_gain_ft=200, estimated_duration_min=75)
    assert estimate_duration_min(hike) == 75


def test_estimate_duration_min_falls_back_to_pace_heuristic():
    hike = make_hike(1, distance_miles=4.8, elevation_gain_ft=1745, estimated_duration_min=None)
    # 4.8 * 30 + 1745 / 50 = 144 + 34.9
    assert estimate_duration_min(hike) == pytest.approx(178.9)


def test_quality_score_rewards_rating_and_review_volume():
    popular = make_hike(1, 1, 100, avg_rating=4.8, reviews_count=40000)
    obscure_but_perfect = make_hike(2, 1, 100, avg_rating=5.0, reviews_count=3)
    assert quality_score(popular) > quality_score(obscure_but_perfect)


def test_quality_score_zero_when_no_rating():
    hike = make_hike(1, 1, 100, avg_rating=None, reviews_count=None)
    assert quality_score(hike) == 0.0


def test_build_itinerary_respects_day_budget():
    # Three 4-hour hikes, 8-hour/day budget -> should not cram all 3 into one day
    hikes = [
        make_hike(i, distance_miles=8, elevation_gain_ft=0, estimated_duration_min=240)
        for i in range(3)
    ]
    days = build_itinerary(hikes, num_days=2, max_hours_per_day=8.0)
    assert len(days) == 2
    for day in days:
        total_hours = sum(estimate_duration_min(h) for h in day) / 60
        assert total_hours <= 8.0
    all_scheduled = [h.id for day in days for h in day]
    assert len(all_scheduled) == 3  # all 3 fit across 2 days (2 + 1)


def test_build_itinerary_drops_hikes_that_dont_fit_anywhere():
    huge_hike = make_hike(
        1, distance_miles=1, elevation_gain_ft=0, estimated_duration_min=600
    )  # 10 hours
    days = build_itinerary([huge_hike], num_days=1, max_hours_per_day=8.0)
    assert days == [[]]


def test_build_itinerary_filters_by_max_difficulty():
    easy = make_hike(1, 1, 100, difficulty="easy")
    strenuous = make_hike(2, 1, 100, difficulty="strenuous")
    days = build_itinerary([easy, strenuous], num_days=1, max_difficulty="easy")
    scheduled_ids = {h.id for day in days for h in day}
    assert scheduled_ids == {1}


def test_build_itinerary_respects_difficulty_override_not_raw_difficulty():
    # Angels Landing-style case: raw difficulty says moderate, override says strenuous
    overridden = make_hike(1, 1, 100, difficulty="moderate", difficulty_override="strenuous")
    days = build_itinerary([overridden], num_days=1, max_difficulty="moderate")
    scheduled_ids = {h.id for day in days for h in day}
    assert scheduled_ids == set()  # excluded: effective difficulty is strenuous, over the cap


def test_build_itinerary_empty_hikes_returns_empty_days():
    days = build_itinerary([], num_days=3)
    assert days == [[], [], []]
