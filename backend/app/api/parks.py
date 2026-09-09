from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import DbSession
from app.models import Park, User, VisitedPark
from app.schemas import ParkOut, VisitIn

router = APIRouter(tags=["parks"])


async def _get_current_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).order_by(User.id).limit(1))
    return result.scalar_one()


@router.get("/parks")
async def list_parks(db: DbSession) -> list[ParkOut]:
    user = await _get_current_user(db)
    result = await db.execute(
        select(Park, VisitedPark)
        .outerjoin(
            VisitedPark,
            (VisitedPark.park_id == Park.id) & (VisitedPark.user_id == user.id),
        )
        .order_by(Park.name)
    )
    return [
        ParkOut(
            id=park.id,
            nps_park_code=park.nps_park_code,
            name=park.name,
            states=park.states,
            description=park.description,
            lat=park.lat,
            lng=park.lng,
            visited=visit is not None,
            visited_date=visit.visited_date if visit else None,
        )
        for park, visit in result.all()
    ]


@router.post("/parks/{park_id}/visit", status_code=204)
async def mark_visited(park_id: int, body: VisitIn, db: DbSession) -> None:
    user = await _get_current_user(db)

    park = await db.get(Park, park_id)
    if park is None:
        raise HTTPException(status_code=404, detail="Park not found")

    result = await db.execute(
        select(VisitedPark).where(VisitedPark.user_id == user.id, VisitedPark.park_id == park_id)
    )
    visit = result.scalar_one_or_none()
    if visit is None:
        visit = VisitedPark(user_id=user.id, park_id=park_id)
        db.add(visit)
    visit.visited_date = body.visited_date
    visit.notes = body.notes
    await db.commit()


@router.delete("/parks/{park_id}/visit", status_code=204)
async def unmark_visited(park_id: int, db: DbSession) -> None:
    user = await _get_current_user(db)
    result = await db.execute(
        select(VisitedPark).where(VisitedPark.user_id == user.id, VisitedPark.park_id == park_id)
    )
    visit = result.scalar_one_or_none()
    if visit is not None:
        await db.delete(visit)
        await db.commit()
