from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from backend.database.service_base import BaseService
from backend.database.utils import transaction_scope, db_error_handler, ensure_exists
from backend.database.imports import Alliance, AllianceSetsMap
from backend.alliances.schemas.alliance_schemas import AllianceCreate, AllianceUpdate, AllianceResponse
from backend.sets.models import Sets

@contextmanager
def transaction_scope(db: Session, error_message: str = "Database transaction failed"):
    """Provide a transactional scope around a series of operations."""
    try:
        yield
        db.commit()
    except HTTPException as e:
        db.rollback()
        raise  # Re-raise HTTP exceptions as they are already properly formatted
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{error_message}: {str(e)}")


def get_all_alliances(db: Session) -> List[Dict[str, Any]]:
    """
    Get all alliances from the database and format them as dictionaries.
    """
    alliances = db.query(Alliance).all()
    return [
        {
            "id": alliance.id,
            "name": alliance.name,
            "description": alliance.description,
            "status": alliance.status,
        }
        for alliance in alliances
    ]


def get_alliance_by_id(db: Session, alliance_id: int) -> Optional[Dict[str, Any]]:
    """
    Get alliance by ID and format it as a dictionary.
    Returns None if alliance is not found.
    """
    alliance = db.get(Alliance, alliance_id)
    if not alliance:
        return None
    
    return {
        "id": alliance.id,
        "name": alliance.name,
        "description": alliance.description,
        "status": alliance.status,
    }


def get_alliance_sets(db: Session, alliance_id: int) -> List[Dict[str, Any]]:
    """
    Get all sets associated with an alliance.
    """
    alliance = db.get(Alliance, alliance_id)
    if not alliance:
        return []
    
    # Retrieve sets

class AllianceService(BaseService[Alliance, AllianceCreate, AllianceUpdate, AllianceResponse]):
    """
    Service for managing alliances.
    
    Extends the BaseService to provide alliance-specific functionality.
    """
    
    def __init__(self):
        super().__init__(Alliance)
    
    @db_error_handler
    def create_alliance(self, db: Session, obj_in: AllianceCreate) -> AllianceResponse:
        """
        Create a new alliance with optional set relationships.
        
        Args:
            db: SQLAlchemy database session
            obj_in: Alliance creation data including optional set IDs
            
        Returns:
            The created alliance with its relationships
        """
        # Extract set_ids before creating the alliance
        set_ids = obj_in.set_ids or []
        
        # Create alliance without set_ids (not a column in the model)
        alliance_data = obj_in.dict(exclude={"set_ids"})
        alliance = Alliance(**alliance_data)
        
        # Set created_at and updated_at timestamps
        now = datetime.utcnow()
        alliance.created_at = now
        alliance.updated_at = now
        
        db.add(alliance)
        db.flush()  # Flush to get the alliance ID
        
        # Create relationships with sets if set_ids are provided
        for set_id in set_ids:
            # Verify the set exists
            set_obj = db.query(Sets).filter(Sets.id == set_id).first()
            if not set_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Set with id {set_id} not found"
                )
            
            # Create the mapping
            mapping = AllianceSetsMap(alliance_id=alliance.id, set_id=set_id)
            db.add(mapping)
        
        db.commit()
        db.refresh(alliance)
        
        # Convert to response schema and return
        return alliance

# Create a singleton instance
alliance_service = AllianceService()