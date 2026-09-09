import datetime

from sqlalchemy import Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Park(Base):
    __tablename__ = "parks"

    id: Mapped[int] = mapped_column(primary_key=True)
    nps_park_code: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    states: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    lat: Mapped[float]
    lng: Mapped[float]

    visits: Mapped[list["VisitedPark"]] = relationship(back_populates="park")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)

    visits: Mapped[list["VisitedPark"]] = relationship(back_populates="user")


class VisitedPark(Base):
    __tablename__ = "visited_parks"
    __table_args__ = (UniqueConstraint("user_id", "park_id", name="uq_visited_parks_user_park"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id"))
    visited_date: Mapped[datetime.date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="visits")
    park: Mapped[Park] = relationship(back_populates="visits")
