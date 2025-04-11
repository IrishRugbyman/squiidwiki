from typing import Type, List, Optional, Dict, Any, Tuple, Generic, TypeVar, Union
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException, status

from backend.database.service_base import BaseService, ModelType
from backend.database.utils import db_error_handler, ensure_exists
from backend.members.models import Members
from backend.events.models import Murders, Shootings, Assists
from backend.events.schemas.events_schemas import EventCreate, EventUpdate


class EventServiceBase(BaseService[ModelType, EventCreate, EventUpdate, Any]):
    """
    Base service for event operations.
    
    This class provides common functionality for Murders, Shootings, and Assists.
    """
    
    def __init__(self, model: Type[ModelType]):
        super().__init__(model)
    
    @db_error_handler
    def create_event(self, db: Session, event_data: EventCreate) -> ModelType:
        """
        Create a new event.
        
        Args:
            db: SQLAlchemy database session
            event_data: Data for the new event
            
        Returns:
            The created event
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate shooter and victim
        shooter = ensure_exists(db, Members, event_data.shooter_id, "Shooter")
        victim = ensure_exists(db, Members, event_data.victim_id, "Victim")
        
        # Parse the date based on precision
        event_date, date_approx = self._parse_date(
            event_data.date_precision, 
            event_data.date_exact, 
            event_data.date_year
        )
        
        # Validate shooter was alive at event time
        self._validate_shooter_alive(shooter, event_date, date_approx)
        
        # Create the event
        new_event = self.model(
            shooter_id=event_data.shooter_id,
            victim_id=event_data.victim_id,
            date=event_date,
            date_approx=date_approx
        )
        
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event
    
    @db_error_handler
    def update_event(
        self, db: Session, event_id: int, event_data: EventUpdate
    ) -> Optional[ModelType]:
        """
        Update an event.
        
        Args:
            db: SQLAlchemy database session
            event_id: ID of the event to update
            event_data: New data for the event
            
        Returns:
            The updated event
            
        Raises:
            HTTPException: If validation fails
        """
        event = self.get(db, event_id)
        if not event:
            return None
        
        # Update shooter if provided
        if event_data.shooter_id:
            shooter = ensure_exists(db, Members, event_data.shooter_id, "Shooter")
            event.shooter_id = event_data.shooter_id
        
        # Parse and update date if provided
        if event_data.date_precision:
            event_date, date_approx = self._parse_date(
                event_data.date_precision,
                event_data.date_exact,
                event_data.date_year
            )
            event.date = event_date
            event.date_approx = date_approx
        
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    def _parse_date(
        self, date_precision: str, date_exact: Optional[str], date_year: Optional[str]
    ) -> Tuple[Optional[datetime.date], str]:
        """
        Parse date based on precision and return (date, approximate_date).
        
        Args:
            date_precision: Type of date precision ("exact", "year", "keep")
            date_exact: Exact date string in format YYYY-MM-DD
            date_year: Year string in format YYYY
            
        Returns:
            Tuple of (date object, approximate date string)
            
        Raises:
            HTTPException: If date parsing fails
        """
        event_date = None
        date_approx = "unknown"
        
        if date_precision == 'exact' and date_exact:
            try:
                event_date = datetime.strptime(date_exact, "%Y-%m-%d").date()
                date_approx = event_date.strftime("%Y")
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid date format (must be YYYY-MM-DD)"
                )
        elif date_precision == 'year' and date_year:
            if not date_year.isdigit() or len(date_year) != 4:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid year format (must be YYYY)"
                )
            date_approx = date_year
        elif date_precision == 'keep':
            # Special case for murders keeping victim's death date
            # The actual value is handled by the calling function
            pass
        
        return event_date, date_approx
    
    def _validate_shooter_alive(
        self, shooter: Members, event_date: Optional[datetime.date], date_approx: str
    ) -> None:
        """
        Validate that the shooter was alive at the event date.
        
        Args:
            shooter: Shooter member object
            event_date: Event date
            date_approx: Approximate date (year) string
            
        Raises:
            HTTPException: If the shooter was not alive at the event date
        """
        if shooter.status == 'dead':
            if event_date and shooter.death_date and event_date > shooter.death_date:
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died on {shooter.death_date}, cannot commit event on {event_date}"
                )
            elif (date_approx and date_approx != "unknown" and
                  shooter.death_date_approx and shooter.death_date_approx != "unknown" and
                  int(date_approx) > int(shooter.death_date_approx)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Shooter died approximately in {shooter.death_date_approx}, cannot commit event in {date_approx}"
                )


class MurderService(EventServiceBase[Murders]):
    """Service for murder events"""
    
    def __init__(self):
        super().__init__(Murders)
    
    @db_error_handler
    def create_event(self, db: Session, event_data: EventCreate) -> Murders:
        """Create a new murder event with special handling for victim death"""
        # Check if victim already has a murder record
        victim = ensure_exists(db, Members, event_data.victim_id, "Victim")
        existing_murder = db.query(Murders).filter(Murders.victim_id == event_data.victim_id).first()
        
        if existing_murder:
            raise HTTPException(
                status_code=400,
                detail="Victim already has a murder record"
            )
        
        # Special case for 'keep' precision - use victim's death date
        if event_data.date_precision == 'keep':
            if victim.status != "dead":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot keep death date for a living victim"
                )
            event_date = victim.death_date
            date_approx = victim.death_date_approx or (event_date.strftime("%Y") if event_date else "unknown")
        else:
            event_date, date_approx = self._parse_date(
                event_data.date_precision,
                event_data.date_exact,
                event_data.date_year
            )
            
            # Handle victim's death date logic
            if victim.status == "dead" and event_data.date_precision != "keep":
                if victim.death_date and event_date and event_date != victim.death_date:
                    if event_date > victim.death_date:
                        if not event_data.update_victim_death:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Victim died on {victim.death_date}, cannot be murdered on {event_date}. Check 'Update victim death date' to proceed."
                            )
                    elif event_date < victim.death_date and not event_data.update_victim_death:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Victim's recorded death date ({victim.death_date}) is later than the murder date ({event_date}). Check 'Update victim death date' to correct this discrepancy."
                        )
        
        # Create the murder record
        murder = super().create_event(db, event_data)
        
        # Update victim status to 'dead'
        victim.status = 'dead'
        victim.death_date = event_date
        victim.death_date_approx = date_approx
        
        db.add(victim)
        db.commit()
        return murder


class ShootingService(EventServiceBase[Shootings]):
    """Service for shooting events"""
    
    def __init__(self):
        super().__init__(Shootings)


class AssistService(EventServiceBase[Assists]):
    """Service for assist events"""
    
    def __init__(self):
        super().__init__(Assists)


# Create singleton instances
murder_service = MurderService()
shooting_service = ShootingService()
assist_service = AssistService() 