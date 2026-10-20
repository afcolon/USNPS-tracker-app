import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db import DbSession
from app.deps import get_current_user
from app.models import Hike, Park, Trip, TripItineraryItem
from app.planner import build_itinerary, estimate_duration_min, filter_by_difficulty
from app.schemas import HikeOut, TripDayOut, TripHikeOut, TripIn, TripOut

router = APIRouter(tags=["trips"])


async def _fetch_trip(db: DbSession, trip_id: int) -> Trip | None:
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.items)
            .selectinload(TripItineraryItem.hike)
            .selectinload(Hike.highlights)
        )
    )
    return result.scalar_one_or_none()


def _to_trip_hike_out(hike: Hike) -> TripHikeOut:
    return TripHikeOut(
        **HikeOut.model_validate(hike).model_dump(),
        effective_duration_min=round(estimate_duration_min(hike)),
    )


def _trip_to_out(trip: Trip, warning: str | None) -> TripOut:
    days: dict[int, list[TripHikeOut]] = {
        day_number: [] for day_number in range(1, trip.num_days + 1)
    }
    for item in trip.items:
        days[item.day_number].append(_to_trip_hike_out(item.hike))

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
    eligible_hikes = filter_by_difficulty(hikes, body.max_difficulty)

    days = build_itinerary(
        eligible_hikes,
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
    scheduled_count = sum(len(day) for day in days)
    if scheduled_count < body.num_days:
        warning = (
            f"Only {scheduled_count} hike(s) scheduled across {body.num_days} day(s) -- "
            "some days may be light or empty."
        )
    elif scheduled_count < len(eligible_hikes):
        dropped_count = len(eligible_hikes) - scheduled_count
        warning = (
            f"{dropped_count} hike(s) didn't fit within your {body.max_hours_per_day}-hour/day "
            "budget and were left out of this itinerary."
        )
    elif empty_days := [day_number for day_number, day in enumerate(days, start=1) if not day]:
        day_list = ", ".join(str(d) for d in empty_days)
        warning = (
            f"All {scheduled_count} available hike(s) were scheduled, but day(s) {day_list} "
            "ended up empty -- the planner fills earlier days first rather than spreading "
            "hikes out evenly."
        )

    trip_row = await _fetch_trip(db, trip.id)
    if trip_row is None:
        raise HTTPException(status_code=500, detail="Trip was created but could not be reloaded")
    return _trip_to_out(trip_row, warning)


@router.get("/trips/{trip_id}")
async def get_trip(trip_id: int, db: DbSession) -> TripOut:
    trip_row = await _fetch_trip(db, trip_id)
    if trip_row is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return _trip_to_out(trip_row, warning=None)
