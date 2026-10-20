"""Greedy trip-planner algorithm (spec §5 v1).

Pure functions operating on Hike-like objects (duck-typed, not imported from
app.models) so this module has no DB/FastAPI dependency and is trivially
unit-testable. See docs/phase3-notes.md for the reasoning behind each choice
below -- the quality-score blend, the bin-packing strategy, and the known
current limitation of the proximity ordering.
"""

import math
from typing import Protocol

DIFFICULTY_ORDER = ["easy", "moderate", "strenuous"]


class HikeLike(Protocol):
    id: int
    distance_miles: float
    elevation_gain_ft: float
    difficulty: str
    difficulty_override: str | None
    estimated_duration_min: int | None
    avg_rating: float | None
    reviews_count: int | None
    trailhead_lat: float
    trailhead_lng: float


def effective_difficulty(hike: HikeLike) -> str:
    return hike.difficulty_override or hike.difficulty


def filter_by_difficulty(hikes: list[HikeLike], max_difficulty: str | None) -> list[HikeLike]:
    if max_difficulty is None:
        return list(hikes)
    max_idx = DIFFICULTY_ORDER.index(max_difficulty)
    return [h for h in hikes if DIFFICULTY_ORDER.index(effective_difficulty(h)) <= max_idx]


def estimate_duration_min(hike: HikeLike) -> float:
    """Falls back to a simple pace-based estimate when the source gave none
    (e.g. Angels Landing in ingestion/data/zion_hikes.json) -- ~30 min/mile
    walking pace plus 1 extra minute per 50 ft of elevation gain. This is a
    rough heuristic, not from the spec; it exists only so a hike with no
    duration data doesn't silently vanish from every itinerary."""
    if hike.estimated_duration_min is not None:
        return hike.estimated_duration_min
    return hike.distance_miles * 30 + hike.elevation_gain_ft / 50


def quality_score(hike: HikeLike) -> float:
    """The spec's "blend of highlight quality and duration" (§5), made
    concrete: rating weighted by log(reviews + 1) so a single 5-star/3-review
    hike doesn't outrank a 4.8-star/40,000-review one. Duration itself isn't
    in the score -- it's what the bin-packing step budgets against instead."""
    if hike.avg_rating is None:
        return 0.0
    return hike.avg_rating * math.log((hike.reviews_count or 0) + 1)


def _order_by_proximity(hikes: list[HikeLike]) -> list[HikeLike]:
    """Greedy nearest-neighbor ordering by trailhead coordinates (plain
    Euclidean distance on lat/lng -- fine at the scale of one park, per the
    spec's own "non-fancy" framing for this kind of clustering).

    NOTE: as of Phase 2, every hike for a given park shares that park's
    centroid as a trailhead-coordinate placeholder (see docs/phase2-notes.md)
    -- so right now this is a documented no-op (all distances are 0, order is
    unchanged). It becomes meaningful once real per-trailhead coordinates land
    (the OSM/NPS-GIS pass planned for Phase 5), without needing to change this
    function.
    """
    if len(hikes) <= 1:
        return list(hikes)
    remaining = list(hikes)
    ordered = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        nearest = min(
            remaining,
            key=lambda h: (
                (h.trailhead_lat - last.trailhead_lat) ** 2
                + (h.trailhead_lng - last.trailhead_lng) ** 2
            ),
        )
        remaining.remove(nearest)
        ordered.append(nearest)
    return ordered


def build_itinerary(
    hikes: list[HikeLike],
    num_days: int,
    max_hours_per_day: float = 8.0,
    max_difficulty: str | None = None,
) -> list[list[HikeLike]]:
    """Returns a list of `num_days` day-lists of hikes, each within budget.

    Greedy bin-packing: hikes are considered highest-quality first; each goes
    into whichever day both (a) has room for it and (b) would have the least
    leftover budget afterward (best-fit decreasing) -- this tends to pack
    days tightly rather than spreading hikes thin across every day before any
    one day is full. A hike that doesn't fit in any day's remaining budget is
    dropped from the itinerary (v1 has no "overflow" handling -- see
    docs/phase3-notes.md).
    """
    hikes = filter_by_difficulty(hikes, max_difficulty)
    hikes_sorted = sorted(hikes, key=quality_score, reverse=True)

    days: list[list[HikeLike]] = [[] for _ in range(num_days)]
    day_hours = [0.0] * num_days

    for hike in hikes_sorted:
        duration_hr = estimate_duration_min(hike) / 60
        candidates = [d for d in range(num_days) if day_hours[d] + duration_hr <= max_hours_per_day]
        if not candidates:
            continue
        target = min(candidates, key=lambda d: max_hours_per_day - day_hours[d] - duration_hr)
        days[target].append(hike)
        day_hours[target] += duration_hr

    return [_order_by_proximity(day) for day in days]
