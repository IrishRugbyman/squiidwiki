import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from app.core.enums import MunicipalityKind


class MunicipalitySource(SQLModel, table=True):
    """A source behind a municipality's description."""

    __tablename__ = "municipality_source"

    municipality_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("municipality.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    source_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True), ForeignKey("source.id", ondelete="CASCADE"), primary_key=True
        )
    )


class MunicipalityOverlap(SQLModel, table=True):
    """A neighborhood's area inside one district of the same city.

    Computed from the two outlines by `sync_overlaps` in crud/municipality.py,
    never written by hand. Slivers under OVERLAP_MIN_SHARE are not stored: they
    are where two boundary datasets disagree, not a real overlap.
    """

    __tablename__ = "municipality_overlap"

    neighborhood_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("municipality.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    district_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("municipality.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        )
    )
    share_of_neighborhood: float
    share_of_district: float


class Municipality(SQLModel, table=True):
    __tablename__ = "municipality"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="municipality.id", index=True)
    # CITY exactly when parent_id is null (CHECK ck_municipality_kind_parent).
    # VARCHAR, not a Postgres ENUM, for the same reason as media.kind.
    kind: MunicipalityKind = Field(
        default=MunicipalityKind.CITY,
        sa_column=Column(String(16), nullable=False, server_default="CITY"),
    )
    geometry: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    # Street names for the place: "The Hole", "Zone 6", "HAMTOWN".
    aliases: Optional[list] = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # The wider area it is spoken of as part of: "Downriver".
    region: Optional[str] = None
    description: Optional[str] = None
    # The latest official count, the year it counts, and whose figure it is
    # ("US Census Bureau, Vintage 2025 estimates"). Written by
    # app/scripts/import_populations.py, never by hand.
    population: Optional[int] = None
    population_year: Optional[int] = None
    population_source: Optional[str] = None
