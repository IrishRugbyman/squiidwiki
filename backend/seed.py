"""
Seed script: creates Metro Detroit universe with sample data for local dev.
Run: python -m seed   (from backend/)
"""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.enums import (
    GlobalRole,
    IncidentType,
    MemberStatus,
    ParticipantOutcome,
    ParticipantRole,
    SetRelationshipType,
    SetStatus,
    SourceReliability,
    UniverseRole,
)
from app.core.fuzzy_date import FuzzyDate
from app.models import (
    Alliance,
    AuditLog,
    GangSet,
    Incident,
    IncidentParticipant,
    Member,
    MemberSource,
    Municipality,
    SetRelationship,
    Source,
    Universe,
    User,
    UserUniverseAccess,
)

DATABASE_URL = "postgresql+asyncpg://postgres:quentin20@localhost:5432/squiidwiki_db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    async with SessionLocal() as session:
        # Admin user
        admin = User(
            email="admin@squiidwiki.local",
            hashed_password="$argon2id$placeholder",  # real hash set via API
            global_role=GlobalRole.ADMIN,
        )
        session.add(admin)
        await session.flush()

        # Universe
        universe = Universe(
            name="Metro Detroit",
            slug="metro-detroit",
            description="Greater Detroit metropolitan area street network research.",
            created_by_id=admin.id,
        )
        session.add(universe)
        await session.flush()

        # Universe access
        session.add(UserUniverseAccess(
            user_id=admin.id,
            universe_id=universe.id,
            role=UniverseRole.ADMIN,
        ))

        # Municipalities
        detroit = Municipality(universe_id=universe.id, name="Detroit")
        ecorse = Municipality(universe_id=universe.id, name="Ecorse")
        river_rouge = Municipality(universe_id=universe.id, name="River Rouge")
        session.add_all([detroit, ecorse, river_rouge])
        await session.flush()

        # Source
        source = Source(
            universe_id=universe.id,
            url="https://example.com/article",
            title="Sample news article",
            reliability=SourceReliability.MEDIUM,
            created_by_id=admin.id,
        )
        session.add(source)
        await session.flush()

        # Sets
        ghost_gang = GangSet(
            universe_id=universe.id,
            name="Ghost Gang",
            alias="GG",
            bio="East side crew based in Detroit.",
            status=SetStatus.ACTIVE,
            created_by_id=admin.id,
        )
        seven_mile = GangSet(
            universe_id=universe.id,
            name="Seven Mile Boys",
            status=SetStatus.ACTIVE,
            created_by_id=admin.id,
        )
        session.add_all([ghost_gang, seven_mile])
        await session.flush()

        # Enemy relationship (normalized: smaller UUID first)
        a, b = sorted([ghost_gang.id, seven_mile.id])
        session.add(SetRelationship(
            set_a_id=a,
            set_b_id=b,
            relationship_type=SetRelationshipType.ENEMY,
        ))

        # Members
        ghost = Member(
            universe_id=universe.id,
            nickname="Ghost",
            legal_name="Marcus Williams",
            set_id=ghost_gang.id,
            status=MemberStatus.FREE,
            dob=FuzzyDate.year_only(1995).model_dump(),
            created_by_id=admin.id,
        )
        dice = Member(
            universe_id=universe.id,
            nickname="Dice",
            set_id=ghost_gang.id,
            status=MemberStatus.LOCKED,
            release_date=FuzzyDate.year_only(2027).model_dump(),
            created_by_id=admin.id,
        )
        lil_ray = Member(
            universe_id=universe.id,
            nickname="Lil Ray",
            set_id=seven_mile.id,
            status=MemberStatus.DEAD,
            created_by_id=admin.id,
        )
        session.add_all([ghost, dice, lil_ray])
        await session.flush()

        # Set founder
        ghost_gang.founder_id = ghost.id

        # Incident
        from app.core.enums import DatePrecision
        from app.core.fuzzy_date import FuzzyDate as FD

        incident = Incident(
            universe_id=universe.id,
            type=IncidentType.MURDER,
            date=FD(year=2023, month=8, precision=DatePrecision.YM).model_dump(),
            municipality_id=detroit.id,
            location_text="E Warren Ave",
            narrative="Altercation between GG and 7MB resulting in one fatality.",
            verified=True,
            verified_by_id=admin.id,
            created_by_id=admin.id,
        )
        session.add(incident)
        await session.flush()

        session.add_all([
            IncidentParticipant(
                incident_id=incident.id,
                member_id=ghost.id,
                role=ParticipantRole.SHOOTER,
                outcome=ParticipantOutcome.UNHARMED,
            ),
            IncidentParticipant(
                incident_id=incident.id,
                member_id=lil_ray.id,
                role=ParticipantRole.VICTIM,
                outcome=ParticipantOutcome.KILLED,
            ),
        ])

        # Link source to member and incident
        session.add(MemberSource(member_id=ghost.id, source_id=source.id))

        await session.commit()
        print("OK Seeded Metro Detroit universe")
        print(f"  Admin email: admin@squiidwiki.local")
        print(f"  Universe: {universe.name} ({universe.slug})")
        print(f"  Sets: Ghost Gang, Seven Mile Boys (enemies)")
        print(f"  Members: Ghost, Dice, Lil Ray")
        print(f"  Incidents: 1 murder")


if __name__ == "__main__":
    asyncio.run(seed())
