import datetime

from pydantic import BaseModel, ConfigDict


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
    highlights: list[HikeHighlightOut] = []
