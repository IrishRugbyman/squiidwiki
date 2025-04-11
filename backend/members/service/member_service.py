from typing import Dict, Any, Union
from sqlalchemy.orm import Session
from backend.members.models import Members
from backend.sets.models import Sets
from datetime import datetime

def format_activity(db: Session, event: Any, model_class: Any) -> Dict[str, Any]:
    """
    Format an activity (shooting, murder, assist) for display.
    
    Args:
        db: Database session
        event: The event object to format
        model_class: The Pydantic model class to use for conversion
    
    Returns:
        Dictionary with formatted event data
    """
    try:
        # Try Pydantic v2 method first
        data = model_class.model_validate(event).model_dump()
    except AttributeError:
        # Fall back to Pydantic v1 method
        data = model_class.from_orm(event).dict()
    
    # Add victim/target name if applicable
    if hasattr(event, 'victim_id') and event.victim_id:
        victim = db.get(Members, event.victim_id)
        if victim:
            data['victim_name'] = victim.name
    
    # Add set information if applicable
    if hasattr(event, 'set_id') and event.set_id:
        set_obj = db.get(Sets, event.set_id)
        if set_obj:
            data['set_name'] = set_obj.name
    
    return data

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate if a string is in the expected date format.
    
    Args:
        date_str: The date string to validate
        format_str: The expected format string (default: YYYY-MM-DD)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_year_format(year_str: str) -> bool:
    """
    Validate if a string is a 4-digit year.
    
    Args:
        year_str: The year string to validate
        
    Returns:
        True if valid, False otherwise
    """
    return year_str.isdigit() and len(year_str) == 4

def process_release_date(status: str, 
                         release_date_precision: str = None,
                         release_date_exact: str = None,
                         release_date_year: str = None) -> tuple:
    """
    Process release date information based on status and input values.
    
    Args:
        status: Member status ('locked_up', 'alive', etc.)
        release_date_precision: Precision level ('exact', 'year', 'life')
        release_date_exact: Exact release date string (YYYY-MM-DD)
        release_date_year: Release year string (YYYY)
        
    Returns:
        Tuple of (release_date, release_date_approx)
    """
    release_date = None
    release_date_approx = None
    
    if status == 'locked_up':
        if release_date_precision == 'life':
            release_date_approx = "life"
        elif release_date_precision == 'year' and release_date_year:
            if validate_year_format(release_date_year):
                release_date_approx = release_date_year
            else:
                raise ValueError("Invalid release year format (must be YYYY)")
        elif release_date_precision == 'exact' and release_date_exact:
            if validate_date_format(release_date_exact):
                parsed_date = datetime.strptime(release_date_exact, "%Y-%m-%d").date()
                release_date = parsed_date
                release_date_approx = parsed_date.strftime("%Y")
            else:
                raise ValueError("Invalid release date format (must be YYYY-MM-DD)")
        else:
            release_date_approx = 'unknown'
    
    return release_date, release_date_approx

def process_death_date(status: str,
                       death_date_exact: str = None,
                       death_date_year: str = None) -> tuple:
    """
    Process death date information based on status and input values.
    
    Args:
        status: Member status ('dead', 'alive', etc.)
        death_date_exact: Exact death date string (YYYY-MM-DD)
        death_date_year: Death year string (YYYY)
        
    Returns:
        Tuple of (death_date, death_date_approx)
    """
    death_date = None
    death_date_approx = None
    
    if status == "dead":
        if death_date_year:
            if validate_year_format(death_date_year):
                death_date_approx = death_date_year
            else:
                raise ValueError("Invalid death year format (must be YYYY)")
        elif death_date_exact:
            if validate_date_format(death_date_exact):
                parsed_date = datetime.strptime(death_date_exact, "%Y-%m-%d").date()
                death_date = parsed_date
                death_date_approx = parsed_date.strftime("%Y")
            else:
                raise ValueError("Invalid death date format (must be YYYY-MM-DD)")
        else:
            death_date_approx = 'unknown'
    
    return death_date, death_date_approx 