"""Service layer for Set (gang/group) operations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import (
    Config,
    RelationshipType,
    Set,
    SetRelationship,
)
from backend.database.service_base import BaseService
from backend.exceptions import EntityNotFoundError
from backend.validators.business_rules import BusinessRuleValidator


class SetService(BaseService[Set, Any, Any]):
    def __init__(self):
        super().__init__(Set)

    # ------------------------------------------------------------------
    # Grouping helper (for the index page)
    # ------------------------------------------------------------------
    def get_grouped(self, db: Session) -> Dict[str, List[Set]]:
        """Return all active sets grouped by first letter."""
        sets = self.get_multi(db, limit=10_000)
        special_ids = self._special_set_ids(db)

        grouped: Dict[str, List[Set]] = {}
        specials: List[Set] = []

        for s in sets:
            if s.id in special_ids:
                specials.append(s)
            else:
                key = s.name[0].upper() if s.name and s.name[0].isalpha() else "#"
                grouped.setdefault(key, []).append(s)

        for v in grouped.values():
            v.sort(key=lambda x: x.name)

        if specials:
            grouped["★"] = sorted(specials, key=lambda x: x.name)
        return grouped

    # ------------------------------------------------------------------
    # Relationships (ally / enemy)
    # ------------------------------------------------------------------
    def add_relationship(
        self,
        db: Session,
        *,
        set_a_id: int,
        set_b_id: int,
        rel_type: RelationshipType,
        force: bool = False,
    ) -> SetRelationship:
        self.get_or_404(db, set_a_id)
        self.get_or_404(db, set_b_id)

        if rel_type == RelationshipType.ALLY:
            BusinessRuleValidator.validate_no_relationship_collision(
                set_a_id, set_b_id, db, force=force,
            )

        existing = (
            db.query(SetRelationship)
            .filter(
                SetRelationship.deleted_at.is_(None),
                SetRelationship.relationship_type == rel_type,
                (
                    (
                        (SetRelationship.set_a_id == set_a_id)
                        & (SetRelationship.set_b_id == set_b_id)
                    )
                    | (
                        (SetRelationship.set_a_id == set_b_id)
                        & (SetRelationship.set_b_id == set_a_id)
                    )
                ),
            )
            .first()
        )
        if existing:
            return existing

        rel = SetRelationship(
            set_a_id=set_a_id,
            set_b_id=set_b_id,
            relationship_type=rel_type,
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel

    def remove_relationship(
        self,
        db: Session,
        *,
        set_a_id: int,
        set_b_id: int,
        rel_type: RelationshipType,
    ) -> None:
        rows = (
            db.query(SetRelationship)
            .filter(
                SetRelationship.deleted_at.is_(None),
                SetRelationship.relationship_type == rel_type,
                (
                    (
                        (SetRelationship.set_a_id == set_a_id)
                        & (SetRelationship.set_b_id == set_b_id)
                    )
                    | (
                        (SetRelationship.set_a_id == set_b_id)
                        & (SetRelationship.set_b_id == set_a_id)
                    )
                ),
            )
            .all()
        )
        for r in rows:
            r.soft_delete()
        db.commit()

    def get_allies(self, db: Session, set_id: int) -> List[Set]:
        return self._related_sets(db, set_id, RelationshipType.ALLY)

    def get_enemies(self, db: Session, set_id: int) -> List[Set]:
        return self._related_sets(db, set_id, RelationshipType.ENEMY)

    def _related_sets(
        self, db: Session, set_id: int, rel_type: RelationshipType,
    ) -> List[Set]:
        rels = (
            db.query(SetRelationship)
            .filter(
                SetRelationship.deleted_at.is_(None),
                SetRelationship.relationship_type == rel_type,
                SetRelationship.ended_at.is_(None),
                (
                    (SetRelationship.set_a_id == set_id)
                    | (SetRelationship.set_b_id == set_id)
                ),
            )
            .all()
        )
        ids = {r.set_a_id if r.set_b_id == set_id else r.set_b_id for r in rels}
        if not ids:
            return []
        return db.query(Set).filter(Set.id.in_(ids), Set.deleted_at.is_(None)).all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _special_set_ids(db: Session) -> set[int]:
        ids: set[int] = set()
        for key in ("unknown_set_id", "civilian_set_id"):
            row = db.query(Config).filter(Config.key == key).first()
            if row:
                ids.add(row.value)
        return ids


set_service = SetService()
