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
