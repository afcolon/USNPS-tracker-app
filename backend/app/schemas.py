import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nps_park_code: str
    name: str
    states: str
    description: str
    lat: float
    lng: float
    visited: bool
    visited_date: datetime.date | None = None


class VisitIn(BaseModel):
    visited_date: datetime.date | None = None
    notes: str | None = None


class HikeHighlightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    source_url: str | None = None


class HikeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    distance_miles: float
    elevation_gain_ft: float
    difficulty: str
    difficulty_score: float
    difficulty_override: str | None = None
    difficulty_override_reason: str | None = None
    hike_type: str
    trailhead_lat: float
    trailhead_lng: float
    estimated_duration_min: int | None = None
    source: str
    source_url: str | None = None
    avg_rating: float | None = None
    reviews_count: int | None = None
    highlights: list[HikeHighlightOut] = []


class TripIn(BaseModel):
    park_id: int
    num_days: int = Field(gt=0, le=30)
    max_difficulty: Literal["easy", "moderate", "strenuous"] | None = None
    max_hours_per_day: float = Field(default=8.0, gt=0, le=24)


class TripHikeOut(HikeOut):
    effective_duration_min: int
    """What the planner actually budgeted for this hike -- `estimated_duration_min`
    when the hike has one, otherwise the planner's pace/elevation fallback
    estimate (see app.planner.estimate_duration_min). Always present, unlike
    `estimated_duration_min` which can be null; lets the UI explain why a day
    looks full even for a hike with no real duration data."""


class TripDayOut(BaseModel):
    day_number: int
    hikes: list[TripHikeOut]


class TripOut(BaseModel):
    id: int
    park_id: int
    num_days: int
    max_difficulty: Literal["easy", "moderate", "strenuous"] | None = None
    max_hours_per_day: float
    created_at: datetime.datetime
    warning: str | None = None
    days: list[TripDayOut]
