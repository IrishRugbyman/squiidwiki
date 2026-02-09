"""CRUD operations for sets."""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, insert, delete as sql_delete
from typing import Optional, List
from app.models.set import Set
from app.models.associations import set_allies, set_enemies
from app.schemas.set import SetCreate, SetUpdate


def create_set(db: Session, set_data: SetCreate) -> Set:
    """Create a new set."""
    db_set = Set(**set_data.model_dump())
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set


def get_set(db: Session, set_id: str) -> Optional[Set]:
    """Get a set by ID."""
    return db.query(Set).filter(Set.id == set_id).first()


def get_sets(db: Session, skip: int = 0, limit: int = 100) -> List[Set]:
    """Get all sets with pagination."""
    return db.query(Set).offset(skip).limit(limit).all()


def update_set(db: Session, set_id: str, set_data: SetUpdate) -> Optional[Set]:
    """Update a set."""
    db_set = get_set(db, set_id)
    if not db_set:
        return None
    
    for key, value in set_data.model_dump(exclude_unset=True).items():
        setattr(db_set, key, value)
    
    db.commit()
    db.refresh(db_set)
    return db_set


def delete_set(db: Session, set_id: str) -> bool:
    """Delete a set."""
    db_set = get_set(db, set_id)
    if not db_set:
        return False
    
    db.delete(db_set)
    db.commit()
    return True


def search_sets(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Set]:
    """Search sets by name, territory, or bio."""
    search_pattern = f"%{query}%"
    return db.query(Set).filter(
        or_(
            Set.primary_name.like(search_pattern),
            Set.territory.like(search_pattern),
            Set.bio.like(search_pattern)
        )
    ).offset(skip).limit(limit).all()


def add_ally(db: Session, set_id: str, ally_id: str) -> bool:
    """Add an ally relationship (symmetric, checks for enemy conflict)."""
    if set_id == ally_id:
        return False  # Cannot be ally with self
    
    # Check if already enemies
    set_a, set_b = (set_id, ally_id) if set_id < ally_id else (ally_id, set_id)
    enemy_check = db.execute(
        set_enemies.select().where(
            and_(set_enemies.c.set_a_id == set_a, set_enemies.c.set_b_id == set_b)
        )
    ).first()
    
    if enemy_check:
        return False  # Cannot be both ally and enemy
    
    # Check if already allies
    ally_check = db.execute(
        set_allies.select().where(
            and_(set_allies.c.set_a_id == set_a, set_allies.c.set_b_id == set_b)
        )
    ).first()
    
    if ally_check:
        return True  # Already allies
    
    # Add ally relationship
    db.execute(
        insert(set_allies).values(set_a_id=set_a, set_b_id=set_b)
    )
    db.commit()
    return True


def remove_ally(db: Session, set_id: str, ally_id: str) -> bool:
    """Remove an ally relationship."""
    set_a, set_b = (set_id, ally_id) if set_id < ally_id else (ally_id, set_id)
    
    result = db.execute(
        sql_delete(set_allies).where(
            and_(set_allies.c.set_a_id == set_a, set_allies.c.set_b_id == set_b)
        )
    )
    db.commit()
    return result.rowcount > 0


def add_enemy(db: Session, set_id: str, enemy_id: str) -> bool:
    """Add an enemy relationship (symmetric, checks for ally conflict)."""
    if set_id == enemy_id:
        return False  # Cannot be enemy with self
    
    # Check if already allies
    set_a, set_b = (set_id, enemy_id) if set_id < enemy_id else (enemy_id, set_id)
    ally_check = db.execute(
        set_allies.select().where(
            and_(set_allies.c.set_a_id == set_a, set_allies.c.set_b_id == set_b)
        )
    ).first()
    
    if ally_check:
        return False  # Cannot be both ally and enemy
    
    # Check if already enemies
    enemy_check = db.execute(
        set_enemies.select().where(
            and_(set_enemies.c.set_a_id == set_a, set_enemies.c.set_b_id == set_b)
        )
    ).first()
    
    if enemy_check:
        return True  # Already enemies
    
    # Add enemy relationship
    db.execute(
        insert(set_enemies).values(set_a_id=set_a, set_b_id=set_b)
    )
    db.commit()
    return True


def remove_enemy(db: Session, set_id: str, enemy_id: str) -> bool:
    """Remove an enemy relationship."""
    set_a, set_b = (set_id, enemy_id) if set_id < enemy_id else (enemy_id, set_id)
    
    result = db.execute(
        sql_delete(set_enemies).where(
            and_(set_enemies.c.set_a_id == set_a, set_enemies.c.set_b_id == set_b)
        )
    )
    db.commit()
    return result.rowcount > 0
