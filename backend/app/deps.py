from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_current_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).order_by(User.id).limit(1))
    return result.scalar_one()
