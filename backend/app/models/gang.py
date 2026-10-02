import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class Gang(SQLModel, table=True):
    """A gang card or nation (Black Disciples, Latin Kings, Rollin 60s).

    Sets claim one or more (`set_gang`); alliances and members can each be
    tagged with one. Cards nest: a branch points at the card it belongs to
    through `parent_id` (Rollin 60s Neighborhood Crips -> Crips, Mafia Insane
    Vice Lords -> Vice Lords), and the Chicago lineages carry the super-alliance
    they ride under in `nation`.
    """

    __tablename__ = "gang"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id", index=True)
    name: str = Field(index=True)
    aliases: list | None = Field(default=None, sa_column=Column(JSONB))
    description: str | None = None
    slug: str | None = Field(default=None, index=True)
    color: str | None = Field(default=None, max_length=16)
    color_secondary: str | None = Field(default=None, max_length=16)
    # The card this one is a branch of. SET NULL: deleting a parent leaves its
    # branches as top-level cards rather than taking them with it.
    parent_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(sa.Uuid, sa.ForeignKey("gang.id", ondelete="SET NULL"), index=True),
    )
    # GangNation value, stored as text (as media.kind is) so a new value is not
    # a Postgres enum migration.
    nation: str | None = Field(default=None, sa_column=Column(sa.String(16)))
    # Where the card was founded, in a few words ("Chicago, Lawndale").
    origin: str | None = None
    # FuzzyDate dict, like alliance.founded_at.
    founded_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # Identifiers a reader would recognise: "six-pointed star", "pitchfork".
    symbols: list | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # The shared card this gang is an instance of; see GangCard.
    card_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(sa.Uuid, sa.ForeignKey("gang_card.id", ondelete="SET NULL"), index=True),
    )
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")


class GangCard(SQLModel, table=True):
    """What a gang *is*, shared by every universe that has it.

    Colours, nation, origin, founding, symbols, the national history and the
    card's own parent are the same in Detroit and in Chicago, so they live here
    once instead of being copied into each universe's `gang` row. A universe's
    `gang` points at its card through `card_id` and keeps only what is local:
    its name as used there, local aliases, a local note in `description`, its
    sets, alliances and members.

    The reference fields are also mirrored onto each linked `gang` row (the way
    `sets.gang_id` mirrors `set_gang`), so the map, the set lists and every
    other reader of `gang.color` keep working untouched. `sync_card_to_gangs`
    in `crud/gang.py` is the only writer of that mirror.
    """

    __tablename__ = "gang_card"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    slug: str = Field(sa_column=Column(sa.String, unique=True, nullable=False, index=True))
    name: str
    aliases: list | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    # The national history; a universe's own note stays on gang.description.
    description: str | None = None
    color: str | None = Field(default=None, max_length=16)
    color_secondary: str | None = Field(default=None, max_length=16)
    nation: str | None = Field(default=None, sa_column=Column(sa.String(16)))
    origin: str | None = None
    founded_at: dict | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    symbols: list | None = Field(default=None, sa_column=Column(JSONB(none_as_null=True)))
    parent_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(sa.Uuid, sa.ForeignKey("gang_card.id", ondelete="SET NULL"), index=True),
    )
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
