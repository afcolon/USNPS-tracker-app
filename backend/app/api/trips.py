import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import DbSession
from app.deps import get_current_user
from app.models import Hike, Park, Trip, TripItineraryItem
from app.planner import build_itinerary
from app.schemas import TripDayOut, TripIn, TripOut

router = APIRouter(tags=["trips"])


async def _load_trip_out(db: DbSession, trip_id: int, warning: str | None) -> TripOut:
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.items)
            .selectinload(TripItineraryItem.hike)
            .selectinload(Hike.highlights)
        )
    )
    trip = result.scalar_one()

    days: dict[int, list] = {day_number: [] for day_number in range(1, trip.num_days + 1)}
    for item in trip.items:
        days[item.day_number].append(item.hike)

    return TripOut(
        id=trip.id,
        park_id=trip.park_id,
        num_days=trip.num_days,
        created_at=trip.created_at,
        warning=warning,
        days=[
            TripDayOut(day_number=day_number, hikes=hikes)
            for day_number, hikes in sorted(days.items())
        ],
    )


@router.post("/trips", status_code=201)
async def create_trip(body: TripIn, db: DbSession) -> TripOut:
    user = await get_current_user(db)

    park = await db.get(Park, body.park_id)
    if park is None:
        raise HTTPException(status_code=404, detail="Park not found")

    result = await db.execute(select(Hike).where(Hike.park_id == body.park_id))
    hikes = list(result.scalars().all())

    days = build_itinerary(
        hikes,
        num_days=body.num_days,
        max_hours_per_day=body.max_hours_per_day,
        max_difficulty=body.max_difficulty,
    )

    trip = Trip(
        user_id=user.id,
        park_id=body.park_id,
        num_days=body.num_days,
        created_at=datetime.datetime.now(datetime.UTC),
    )
    db.add(trip)
    await db.flush()

    for day_number, day_hikes in enumerate(days, start=1):
        for order_in_day, hike in enumerate(day_hikes, start=1):
            db.add(
                TripItineraryItem(
                    trip_id=trip.id,
                    hike_id=hike.id,
                    day_number=day_number,
                    order_in_day=order_in_day,
                )
            )
    await db.commit()

    warning = None
    if len(hikes) < body.num_days:
        warning = (
            f"Only {len(hikes)} hike(s) available for this park -- some days may be light or empty."
        )

    return await _load_trip_out(db, trip.id, warning)


@router.get("/trips/{trip_id}")
async def get_trip(trip_id: int, db: DbSession) -> TripOut:
    trip = await db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return await _load_trip_out(db, trip_id, warning=None)
