from fastapi import APIRouter, Request, HTTPException, Depends
from datetime import datetime
import logging

from starlette.responses import HTMLResponse, RedirectResponse

from sqlalchemy.orm import Session, aliased

from backend.config.templates import templates
from backend.database.base_class import get_db
from backend.members.models import Members
from backend.events.models import Murders, Shootings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/events", response_class=HTMLResponse)
def list_events(request: Request, db: Session = Depends(get_db)):
    events = []
    try:
        # Query for releases - only include events with actual dates
        releases = db.query(Members).filter(Members.release_date != None).all()
        for member in releases:
            if member.release_date:
                events.append({
                    "title": f"{member.name} released",
                    "date": member.release_date.strftime("%Y-%m-%d"),
                    "color": "green",
                    "eventType": "release",
                    "memberId": member.id
                })

        # Query for murders with aliased tables
        Shooter = aliased(Members, name="shooter")
        Victim = aliased(Members, name="victim")
        murders = (
            db.query(Murders)
            .join(Shooter, Shooter.id == Murders.shooter_id)
            .join(Victim, Victim.id == Murders.victim_id)
            .filter(Murders.date != None)
            .all()
        )
        for murder in murders:
            if murder.shooter and murder.victim and murder.date:
                events.append({
                    "title": f"{murder.shooter.name} killed {murder.victim.name}",
                    "date": murder.date.strftime("%Y-%m-%d"),
                    "color": "darkred",
                    "eventType": "murder",
                    "shooterId": murder.shooter_id,
                    "victimId": murder.victim_id
                })

        # Query for deaths - exclude murder victims and require valid dates
        murder_victims = db.query(Murders.victim_id).filter(Murders.date != None)
        deaths = db.query(Members).filter(
            Members.death_date != None,
            ~Members.id.in_(murder_victims)
        ).all()
        
        for member in deaths:
            if member.death_date:
                events.append({
                    "title": f"{member.name} died",
                    "date": member.death_date.strftime("%Y-%m-%d"),
                    "color": "red",
                    "eventType": "death",
                    "memberId": member.id
                })
                
        # Add death anniversaries for all deceased members (including murder victims)
        try:
            today = datetime.today().date()
            all_deaths = []
            
            # Add regular deaths
            for member in deaths:
                if member.death_date:
                    try:
                        # Check if it's a datetime or date object
                        death_date = member.death_date
                        if hasattr(death_date, 'date'):
                            death_date = death_date.date()
                        
                        all_deaths.append({
                            "name": member.name,
                            "date": death_date,
                            "member_id": member.id
                        })
                    except Exception as e:
                        logger.error(f"Error processing death date for member {member.id}: {str(e)}")
                    
            # Add murder victims
            for murder in murders:
                if murder.victim and murder.date:
                    try:
                        # Check if it's a datetime or date object
                        death_date = murder.date
                        if hasattr(death_date, 'date'):
                            death_date = death_date.date()
                        
                        all_deaths.append({
                            "name": murder.victim.name,
                            "date": death_date,
                            "member_id": murder.victim_id
                        })
                    except Exception as e:
                        logger.error(f"Error processing death date for murder victim {murder.victim_id}: {str(e)}")
            
            # Add anniversaries for upcoming dates
            for death in all_deaths:
                try:
                    # Get next anniversary
                    death_date = death["date"]
                    
                    # Create datetime objects carefully with proper type checking
                    # Even using integers to create datetime to avoid type issues
                    try:
                        next_anniversary = datetime(today.year, death_date.month, death_date.day).date()
                        
                        # If the anniversary has passed this year, get next year's
                        if next_anniversary < today:
                            next_anniversary = datetime(today.year + 1, death_date.month, death_date.day).date()
                        
                        # Calculate years since death
                        years_since = next_anniversary.year - death_date.year
                        
                        if years_since > 0 and years_since <= 10:
                            events.append({
                                "title": f"{death['name']} death anniversary ({years_since} years)",
                                "date": next_anniversary.strftime("%Y-%m-%d"),
                                "color": "black",
                                "eventType": "anniversary",
                                "memberId": death["member_id"]
                            })
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.error(f"Error calculating anniversary for {death['name']}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing anniversary: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing anniversaries: {str(e)}")

        # Query for shootings - only include events with actual dates
        Shooter = aliased(Members, name="shooter")
        Victim = aliased(Members, name="victim")
        shootings = (
            db.query(Shootings)
            .join(Shooter, Shooter.id == Shootings.shooter_id)
            .join(Victim, Victim.id == Shootings.victim_id)
            .filter(Shootings.date != None)
            .all()
        )
        
        for shooting in shootings:
            if shooting.shooter and shooting.victim and shooting.date:
                events.append({
                    "title": f"{shooting.shooter.name} shot {shooting.victim.name}",
                    "date": shooting.date.strftime("%Y-%m-%d"),
                    "color": "orange",
                    "eventType": "shooting",
                    "shooterId": shooting.shooter_id,
                    "victimId": shooting.victim_id
                })

        # Categorize and sort events
        today = datetime.today().date()
        upcoming_events = [
            e for e in events
            if e["date"] and datetime.strptime(e["date"], "%Y-%m-%d").date() >= today
        ]
        latest_past_events = [
            e for e in events
            if e["date"] and datetime.strptime(e["date"], "%Y-%m-%d").date() < today
        ]
        upcoming_events.sort(key=lambda x: x["date"])
        latest_past_events.sort(key=lambda x: x["date"], reverse=True)

    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

    return templates.TemplateResponse(
        "calendar/calendar_events.html",
        {
            "request": request,
            "upcoming_events": upcoming_events[:15],
            "latest_past_events": latest_past_events[:15]
        }
    )


@router.get("/", response_class=HTMLResponse)
def show_calendar(request: Request, db: Session = Depends(get_db)):
    events = []
    try:
        # Query for releases - only include events with actual dates
        releases = db.query(Members).filter(Members.release_date != None).all()
        for member in releases:
            if member.release_date:
                events.append({
                    "title": f"{member.name} released",
                    "date": member.release_date.strftime("%Y-%m-%d"),
                    "color": "green",
                    "extendedProps": {
                        "eventType": "release",
                        "memberId": member.id
                    }
                })

        # Query for murders with aliased tables - only include events with actual dates
        Shooter = aliased(Members, name="shooter")
        Victim = aliased(Members, name="victim")
        murders = (
            db.query(Murders)
            .join(Shooter, Shooter.id == Murders.shooter_id)
            .join(Victim, Victim.id == Murders.victim_id)
            .filter(Murders.date != None)
            .all()
        )
        
        logger.info(f"Found {len(murders)} murder events")
        murder_victim_ids = set()
        for murder in murders:
            if murder.shooter and murder.victim and murder.date:
                logger.info(f"Adding murder: {murder.shooter.name} killed {murder.victim.name} on {murder.date}")
                events.append({
                    "title": f"{murder.shooter.name} killed {murder.victim.name}",
                    "date": murder.date.strftime("%Y-%m-%d"),
                    "color": "darkred",
                    "extendedProps": {
                        "eventType": "murder",
                        "shooterId": murder.shooter_id,
                        "victimId": murder.victim_id
                    }
                })
                
                # Add to set of murder victim IDs
                murder_victim_ids.add(murder.victim_id)
                
                # Add death anniversaries for murder victims
                try:
                    murder_date = murder.date
                    if hasattr(murder_date, 'date'):
                        murder_date = murder_date.date()
                    
                    death_year = murder_date.year
                    month_day = murder_date.strftime("-%m-%d")
                    for year in range(death_year + 1, death_year + 11):
                        events.append({
                            "title": f"{murder.victim.name} †",
                            "date": f"{year}{month_day}",
                            "color": "black",
                            "extendedProps": {
                                "eventType": "anniversary",
                                "memberId": murder.victim_id
                            }
                        })
                except Exception as e:
                    logger.warning(f"Invalid death date format for murder victim {murder.victim_id}: {str(e)}")

        # Query for deaths - exclude murder victims and require valid dates
        deaths = db.query(Members).filter(
            Members.death_date != None,
            ~Members.id.in_(murder_victim_ids)
        ).all()
        
        for member in deaths:
            if member.death_date:
                events.append({
                    "title": f"{member.name} died",
                    "date": member.death_date.strftime("%Y-%m-%d"),
                    "color": "red",
                    "extendedProps": {
                        "eventType": "death",
                        "memberId": member.id
                    }
                })
                # Add death anniversaries
                try:
                    death_date = member.death_date
                    if hasattr(death_date, 'date'):
                        death_date = death_date.date()
                        
                    death_year = death_date.year
                    month_day = death_date.strftime("-%m-%d")
                    for year in range(death_year + 1, death_year + 11):
                        events.append({
                            "title": f"{member.name} †",
                            "date": f"{year}{month_day}",
                            "color": "black",
                            "extendedProps": {
                                "eventType": "anniversary",
                                "memberId": member.id
                            }
                        })
                except Exception as e:
                    logger.warning(f"Invalid death date format for member {member.id}: {str(e)}")

        # Query for shootings - only include events with actual dates
        Shooter = aliased(Members, name="shooter")
        Victim = aliased(Members, name="victim")
        shootings = (
            db.query(Shootings)
            .join(Shooter, Shooter.id == Shootings.shooter_id)
            .join(Victim, Victim.id == Shootings.victim_id)
            .filter(Shootings.date != None)
            .all()
        )
        
        for shooting in shootings:
            if shooting.shooter and shooting.victim and shooting.date:
                events.append({
                    "title": f"{shooting.shooter.name} shot {shooting.victim.name}",
                    "date": shooting.date.strftime("%Y-%m-%d"),
                    "color": "orange",
                    "extendedProps": {
                        "eventType": "shooting",
                        "shooterId": shooting.shooter_id,
                        "victimId": shooting.victim_id
                    }
                })

        logger.info(f"Total events for calendar: {len(events)}")

    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return templates.TemplateResponse("calendar/calendar.html", {"request": request, "events": events})
