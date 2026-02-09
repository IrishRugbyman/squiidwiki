"""CRUD operations for members."""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List, Dict
from app.models.member import Member
from app.models.incident import IncidentParticipant, ParticipantRole, VictimOutcome
from app.schemas.member import MemberCreate, MemberUpdate


def create_member(db: Session, member: MemberCreate) -> Member:
    """Create a new member."""
    db_member = Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def get_member(db: Session, member_id: str) -> Optional[Member]:
    """Get a member by ID."""
    return db.query(Member).filter(Member.id == member_id).first()


def get_members(db: Session, skip: int = 0, limit: int = 100) -> List[Member]:
    """Get all members with pagination."""
    return db.query(Member).offset(skip).limit(limit).all()


def update_member(db: Session, member_id: str, member: MemberUpdate) -> Optional[Member]:
    """Update a member."""
    db_member = get_member(db, member_id)
    if not db_member:
        return None
    
    for key, value in member.model_dump(exclude_unset=True).items():
        setattr(db_member, key, value)
    
    db.commit()
    db.refresh(db_member)
    return db_member


def delete_member(db: Session, member_id: str) -> bool:
    """Delete a member."""
    db_member = get_member(db, member_id)
    if not db_member:
        return False
    
    db.delete(db_member)
    db.commit()
    return True


def search_members(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Member]:
    """Search members by name, nickname, or bio."""
    search_pattern = f"%{query}%"
    return db.query(Member).filter(
        or_(
            Member.first_name.like(search_pattern),
            Member.last_name.like(search_pattern),
            Member.bio.like(search_pattern)
        )
    ).offset(skip).limit(limit).all()


def get_member_stats(db: Session, member_id: str) -> Dict[str, int]:
    """Get computed stats for a member."""
    # Kills: incidents where member is PERPETRATOR and victim outcome is KILLED
    kills = db.query(func.count(IncidentParticipant.id)).filter(
        IncidentParticipant.member_id == member_id,
        IncidentParticipant.role == ParticipantRole.PERPETRATOR,
        IncidentParticipant.incident_id.in_(
            db.query(IncidentParticipant.incident_id).filter(
                IncidentParticipant.role == ParticipantRole.VICTIM,
                IncidentParticipant.outcome == VictimOutcome.KILLED
            )
        )
    ).scalar() or 0
    
    # Assists: incidents where member is ACCOMPLICE and victim outcome is KILLED
    assists = db.query(func.count(IncidentParticipant.id)).filter(
        IncidentParticipant.member_id == member_id,
        IncidentParticipant.role == ParticipantRole.ACCOMPLICE,
        IncidentParticipant.incident_id.in_(
            db.query(IncidentParticipant.incident_id).filter(
                IncidentParticipant.role == ParticipantRole.VICTIM,
                IncidentParticipant.outcome == VictimOutcome.KILLED
            )
        )
    ).scalar() or 0
    
    # Shootings committed: count of participations as PERPETRATOR
    shootings_committed = db.query(func.count(IncidentParticipant.id)).filter(
        IncidentParticipant.member_id == member_id,
        IncidentParticipant.role == ParticipantRole.PERPETRATOR
    ).scalar() or 0
    
    # Times shot: count of participations as VICTIM
    times_shot = db.query(func.count(IncidentParticipant.id)).filter(
        IncidentParticipant.member_id == member_id,
        IncidentParticipant.role == ParticipantRole.VICTIM
    ).scalar() or 0
    
    return {
        "kills": kills,
        "assists": assists,
        "shootings_committed": shootings_committed,
        "times_shot": times_shot
    }
