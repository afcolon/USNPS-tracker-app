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


class Hike(Base):
    __tablename__ = "hikes"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_hikes_source_source_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    park_id: Mapped[int] = mapped_column(ForeignKey("parks.id"))
    name: Mapped[str]
    distance_miles: Mapped[float]
    elevation_gain_ft: Mapped[float]
    difficulty: Mapped[str]
    """NPS's 3-tier scale (easy/moderate/strenuous) -- computed via the §3.2.1
    formula unless difficulty_override is set."""
    difficulty_score: Mapped[float]
    difficulty_override: Mapped[str | None]
    """Set when the computed score misleads (e.g. exposure/scrambling the
    distance+elevation formula can't see) -- see docs/phase2-notes.md."""
    difficulty_override_reason: Mapped[str | None] = mapped_column(Text)
    hike_type: Mapped[str]
    """loop / out_and_back / point_to_point"""
    trailhead_lat: Mapped[float]
    trailhead_lng: Mapped[float]
    estimated_duration_min: Mapped[int | None]
    source: Mapped[str]
    """osm_computed / nps_gis / manual / alltrails -- see docs/phase2-notes.md
    for why alltrails is here despite docs/spec.md §3.2 ruling it out."""
    source_id: Mapped[str]
    """The source's own identifier for this hike (e.g. an AllTrails trail id),
    so re-running a loader upserts instead of duplicating."""
    source_url: Mapped[str | None]

    park: Mapped[Park] = relationship()
    highlights: Mapped[list["HikeHighlight"]] = relationship(back_populates="hike")


class HikeHighlight(Base):
    __tablename__ = "hike_highlights"

    id: Mapped[int] = mapped_column(primary_key=True)
    hike_id: Mapped[int] = mapped_column(ForeignKey("hikes.id"))
    text: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None]

    hike: Mapped[Hike] = relationship(back_populates="highlights")
