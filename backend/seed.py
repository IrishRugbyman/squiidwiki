"""
Seed script: wipes and repopulates a target database with Metro Detroit mock data.

Usage (from backend/):
  python seed.py              # seeds prod (squiidwiki_db)
  python seed.py --test       # wipes + seeds test (squiidwiki_test)
"""
import asyncio
import sys
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.enums import (
    DatePrecision,
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
from app.auth.security import hash_password
from app.crud.gang_set import seed_reserved_sets

PROD_URL = "postgresql+asyncpg://postgres:quentin20@localhost:5432/squiidwiki_db"
TEST_URL = "postgresql+asyncpg://postgres:quentin20@localhost:5432/squiidwiki_test"

# UUID of admin@squiidwiki.dev in prod — used for universe access in test DB
PROD_ADMIN_ID = uuid.UUID("e44913fe-9a60-4ff6-9728-82abf2804c1a")


def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "item"

WIPE_ORDER = [
    "incident_source", "member_source",
    "incident_participant", "incident",
    "set_relationships", "set_municipality", "alliance_municipality", "alliance_set",
    "member", "sets", "alliance",
    "municipality",
    "user_universe_access", "audit_log",
    "universe",
    "refresh_tokens", "users",
]


async def wipe(session: AsyncSession) -> None:
    for table in WIPE_ORDER:
        await session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    await session.commit()
    print("  Wiped all tables.")


async def seed(session: AsyncSession, is_test: bool) -> None:
    # Admin user
    if is_test:
        # Point universe access at the real prod admin so the toggle works seamlessly
        admin_id = PROD_ADMIN_ID
        admin = User(
            id=admin_id,
            email="admin@squiidwiki.dev",
            hashed_password=hash_password("admin1234"),
            global_role=GlobalRole.ADMIN,
        )
    else:
        admin = User(
            email="admin@squiidwiki.local",
            hashed_password="$argon2id$placeholder",
            global_role=GlobalRole.ADMIN,
        )
        admin_id = None  # assigned after flush

    session.add(admin)
    await session.flush()
    if admin_id is None:
        admin_id = admin.id

    # Universe
    universe = Universe(
        name="Metro Detroit",
        slug="metro-detroit",
        description="Greater Detroit metropolitan area street network research.",
        created_by_id=admin_id,
    )
    session.add(universe)
    await session.flush()
    await seed_reserved_sets(session, universe.id)

    session.add(UserUniverseAccess(
        user_id=admin_id,
        universe_id=universe.id,
        role=UniverseRole.ADMIN,
    ))

    # Municipalities
    detroit = Municipality(universe_id=universe.id, name="Detroit")
    ecorse = Municipality(universe_id=universe.id, name="Ecorse")
    river_rouge = Municipality(universe_id=universe.id, name="River Rouge")
    session.add_all([detroit, ecorse, river_rouge])
    await session.flush()

    # Sources
    news = Source(
        universe_id=universe.id,
        url="https://example.com/article",
        title="Detroit street conflict report — Aug 2023",
        reliability=SourceReliability.MEDIUM,
        created_by_id=admin_id,
    )
    court = Source(
        universe_id=universe.id,
        url="https://example.com/court-docs",
        title="Wayne County court records 2022",
        reliability=SourceReliability.HIGH,
        created_by_id=admin_id,
    )
    session.add_all([news, court])
    await session.flush()

    # Alliance
    eastside = Alliance(
        universe_id=universe.id,
        name="Eastside Coalition",
        slug=slugify("Eastside Coalition"),
        created_by_id=admin_id,
    )
    session.add(eastside)
    await session.flush()

    # Sets
    ghost_gang = GangSet(
        universe_id=universe.id,
        name="Ghost Gang", slug=slugify("Ghost Gang"),
        aliases=["GG"], bio="East side crew based in Detroit, founded early 2010s.",
        status=SetStatus.ACTIVE, alliance_id=eastside.id, created_by_id=admin_id,
    )
    seven_mile = GangSet(
        universe_id=universe.id,
        name="Seven Mile Boys", slug=slugify("Seven Mile Boys"),
        aliases=["7MB"], bio="Active on the northwest side of Detroit.",
        status=SetStatus.ACTIVE, created_by_id=admin_id,
    )
    river_crew = GangSet(
        universe_id=universe.id,
        name="River Crew", slug=slugify("River Crew"),
        aliases=["RC"], bio="Operates in Ecorse and River Rouge.",
        status=SetStatus.ACTIVE, created_by_id=admin_id,
    )
    session.add_all([ghost_gang, seven_mile, river_crew])
    await session.flush()

    # Relationships
    pairs = [
        (ghost_gang.id, seven_mile.id),
        (seven_mile.id, river_crew.id),
    ]
    for x, y in pairs:
        a, b = sorted([x, y])
        session.add(SetRelationship(set_a_id=a, set_b_id=b, relationship_type=SetRelationshipType.ENEMY))

    # Members
    ghost = Member(
        universe_id=universe.id, nickname="Ghost", slug=slugify("Ghost"),
        legal_name="Marcus Williams", set_id=ghost_gang.id, status=MemberStatus.FREE,
        dob=FuzzyDate.year_only(1995).model_dump(), created_by_id=admin_id,
    )
    dice = Member(
        universe_id=universe.id, nickname="Dice", slug=slugify("Dice"),
        set_id=ghost_gang.id, status=MemberStatus.LOCKED,
        release_date=FuzzyDate.year_only(2027).model_dump(), created_by_id=admin_id,
    )
    lil_ray = Member(
        universe_id=universe.id, nickname="Lil Ray", slug=slugify("Lil Ray"),
        set_id=seven_mile.id, status=MemberStatus.DEAD,
        date_of_death=FuzzyDate(year=2023, month=8, precision=DatePrecision.YM).model_dump(),
        created_by_id=admin_id,
    )
    ko = Member(
        universe_id=universe.id, nickname="KO", slug=slugify("KO"),
        legal_name="Kevin Odom", set_id=seven_mile.id, status=MemberStatus.FREE,
        dob=FuzzyDate.year_only(1998).model_dump(), created_by_id=admin_id,
    )
    shadow = Member(
        universe_id=universe.id, nickname="Shadow", slug=slugify("Shadow"),
        set_id=river_crew.id, status=MemberStatus.UNKNOWN, created_by_id=admin_id,
    )
    session.add_all([ghost, dice, lil_ray, ko, shadow])
    await session.flush()

    ghost_gang.founder_id = ghost.id

    # Incidents
    murder1 = Incident(
        universe_id=universe.id,
        type=IncidentType.MURDER,
        date=FuzzyDate(year=2023, month=8, precision=DatePrecision.YM).model_dump(),
        municipality_id=detroit.id,
        location_text="E Warren Ave",
        narrative="Altercation between GG and 7MB resulting in one fatality.",
        verified=True, verified_by_id=admin_id, created_by_id=admin_id,
    )
    shooting1 = Incident(
        universe_id=universe.id,
        type=IncidentType.SHOOTING,
        date=FuzzyDate(year=2023, month=11, day=3, precision=DatePrecision.YMD).model_dump(),
        municipality_id=ecorse.id,
        location_text="Outer Drive near Ecorse Rd",
        narrative="Drive-by, two injured.",
        verified=False, created_by_id=admin_id,
    )
    murder2 = Incident(
        universe_id=universe.id,
        type=IncidentType.MURDER,
        date=FuzzyDate(year=2024, month=2, precision=DatePrecision.YM).model_dump(),
        municipality_id=detroit.id,
        location_text="7 Mile Rd",
        narrative="Retaliation killing linked to November shooting.",
        verified=True, verified_by_id=admin_id, created_by_id=admin_id,
    )
    session.add_all([murder1, shooting1, murder2])
    await session.flush()

    session.add_all([
        IncidentParticipant(incident_id=murder1.id, member_id=ghost.id,
                            role=ParticipantRole.SHOOTER, outcome=ParticipantOutcome.UNHARMED),
        IncidentParticipant(incident_id=murder1.id, member_id=lil_ray.id,
                            role=ParticipantRole.VICTIM, outcome=ParticipantOutcome.KILLED),
        IncidentParticipant(incident_id=shooting1.id, member_id=ko.id,
                            role=ParticipantRole.SHOOTER, outcome=ParticipantOutcome.UNHARMED),
        IncidentParticipant(incident_id=shooting1.id, member_id=shadow.id,
                            role=ParticipantRole.VICTIM, outcome=ParticipantOutcome.INJURED),
        IncidentParticipant(incident_id=murder2.id, member_id=dice.id,
                            role=ParticipantRole.ASSISTED, outcome=ParticipantOutcome.UNHARMED),
        IncidentParticipant(incident_id=murder2.id, member_id=ko.id,
                            role=ParticipantRole.VICTIM, outcome=ParticipantOutcome.KILLED),
    ])

    session.add_all([
        MemberSource(member_id=ghost.id, source_id=news.id),
        MemberSource(member_id=lil_ray.id, source_id=court.id),
        MemberSource(member_id=ko.id, source_id=news.id),
    ])

    await session.commit()

    label = "TEST" if is_test else "PROD"
    print(f"  [{label}] Seeded Metro Detroit universe")
    print(f"  Universe: {universe.name} ({universe.slug})")
    print(f"  Sets: Ghost Gang (Eastside Coalition), Seven Mile Boys, River Crew")
    print(f"  Members: Ghost, Dice, Lil Ray, KO, Shadow")
    print(f"  Incidents: 2 murders, 1 shooting")
    print(f"  Sources: 2")


async def main(is_test: bool) -> None:
    url = TEST_URL if is_test else PROD_URL
    engine = create_async_engine(url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        if is_test:
            print("Wiping test DB...")
            await wipe(session)
        print("Seeding...")
        await seed(session, is_test)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(is_test="--test" in sys.argv))
