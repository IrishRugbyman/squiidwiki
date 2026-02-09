"""Seed script to populate database with sample data."""
from app.database import SessionLocal
from app.models import *
from app.crud import member as member_crud, set as set_crud, alliance as alliance_crud, incident as incident_crud, source as source_crud
from app.schemas.member import MemberCreate
from app.schemas.set import SetCreate
from app.schemas.alliance import AllianceCreate
from app.schemas.incident import IncidentCreate, IncidentParticipantCreate
from app.schemas.source import SourceCreate

def seed_database():
    """Seed the database with sample data."""
    db = SessionLocal()
    
    try:
        # Create sources
        print("Creating sources...")
        source1 = source_crud.create_source(db, SourceCreate(
            type=SourceType.NEWS_ARTICLE,
            title="Detroit News Report 2020",
            url="https://example.com/news1",
            date_year=2020,
            date_month=5,
            date_day=15
        ))
        
        # Create alliances
        print("Creating alliances...")
        alliance1 = alliance_crud.create_alliance(db, AllianceCreate(
            name="Eastside Alliance",
            status=AllianceStatus.ACTIVE,
            bio="Major alliance on Detroit's east side",
            founded_year=2015
        ))
        
        # Create sets
        print("Creating sets...")
        set1 = set_crud.create_set(db, SetCreate(
            primary_name="7 Mile Bloods",
            names=["SMB", "Seven Mile"],
            status=SetStatus.ACTIVE,
            territory="7 Mile & Van Dyke",
            colors="Red",
            alliance_id=alliance1.id,
            founded_year=2010
        ))
        
        set2 = set_crud.create_set(db, SetCreate(
            primary_name="6 Mile Chedda Grove",
            names=["Chedda Grove", "6MCG"],
            status=SetStatus.ACTIVE,
            territory="6 Mile & Gratiot",
            colors="Green",
            alliance_id=alliance1.id,
            founded_year=2012
        ))
        
        set3 = set_crud.create_set(db, SetCreate(
            primary_name="8 Mile Crips",
            names=["8MC"],
            status=SetStatus.ACTIVE,
            territory="8 Mile & Hoover",
            colors="Blue",
            founded_year=2008
        ))
        
        # Make set1 and set2 allies, set3 is their enemy
        print("Creating relationships...")
        set_crud.add_ally(db, set1.id, set2.id)
        set_crud.add_enemy(db, set1.id, set3.id)
        set_crud.add_enemy(db, set2.id, set3.id)
        
        # Create members
        print("Creating members...")
        member1 = member_crud.create_member(db, MemberCreate(
            first_name="John",
            last_name="Doe",
            nicknames=["JD", "Big J"],
            status=MemberStatus.ALIVE_FREE,
            affiliation_type=AffiliationType.SET,
            set_id=set1.id,
            dob_year=1995,
            dob_month=3,
            bio="Prominent member of 7 Mile Bloods"
        ))
        
        member2 = member_crud.create_member(db, MemberCreate(
            first_name="Mike",
            last_name="Smith",
            nicknames=["Money Mike"],
            status=MemberStatus.DEAD,
            affiliation_type=AffiliationType.SET,
            set_id=set3.id,
            dob_year=1993,
            dod_year=2020,
            dod_month=6,
            bio="Member of 8 Mile Crips"
        ))
        
        member3 = member_crud.create_member(db, MemberCreate(
            first_name="Tony",
            last_name="Brown",
            nicknames=["T-Money"],
            status=MemberStatus.ALIVE_LOCKED_UP,
            affiliation_type=AffiliationType.SET,
            set_id=set1.id,
            dob_year=1997,
            bio="Serving time for assault"
        ))
        
        member4 = member_crud.create_member(db, MemberCreate(
            first_name="Chris",
            last_name="Johnson",
            nicknames=["CJ"],
            status=MemberStatus.ALIVE_FREE,
            affiliation_type=AffiliationType.SET,
            set_id=set2.id,
            dob_year=1998,
            bio="Member of Chedda Grove"
        ))
        
        # Create incidents
        print("Creating incidents...")
        incident1 = incident_crud.create_incident(db, IncidentCreate(
            type=IncidentType.SHOOTING,
            location="7 Mile & Van Dyke",
            description="Drive-by shooting resulting in one fatality",
            date_year=2020,
            date_month=6,
            date_day=15,
            participants=[
                IncidentParticipantCreate(
                    member_id=member1.id,
                    role=ParticipantRole.PERPETRATOR,
                    notes="Alleged shooter"
                ),
                IncidentParticipantCreate(
                    member_id=member3.id,
                    role=ParticipantRole.ACCOMPLICE,
                    notes="Driver"
                ),
                IncidentParticipantCreate(
                    member_id=member2.id,
                    role=ParticipantRole.VICTIM,
                    outcome=VictimOutcome.KILLED,
                    notes="Rival gang member"
                )
            ]
        ))
        
        incident2 = incident_crud.create_incident(db, IncidentCreate(
            type=IncidentType.SHOOTING,
            location="8 Mile & Hoover",
            description="Retaliation shooting, no injuries",
            date_year=2020,
            date_month=7,
            date_day=2,
            participants=[
                IncidentParticipantCreate(
                    member_id=member4.id,
                    role=ParticipantRole.PERPETRATOR,
                    notes="Shooter"
                ),
                IncidentParticipantCreate(
                    member_id=member1.id,
                    role=ParticipantRole.VICTIM,
                    outcome=VictimOutcome.UNHARMED,
                    notes="Target missed"
                )
            ]
        ))
        
        print("Database seeded successfully!")
        print(f"  - {db.query(Alliance).count()} alliances")
        print(f"  - {db.query(Set).count()} sets")
        print(f"  - {db.query(Member).count()} members")
        print(f"  - {db.query(Incident).count()} incidents")
        print(f"  - {db.query(Source).count()} sources")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
