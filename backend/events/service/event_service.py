"""
Unified event service.

Replaces the old per-type services (MurderService, ShootingService,
AssistService) with a single ``EventService`` that operates on the
unified ``Event`` / ``EventParticipant`` tables.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import (
    DatePrecision,
    Event,
    EventParticipant,
    EventType,
    LocationType,
    Member,
    MemberStatus,
    ParticipantRole,
    Set,
)
from backend.database.service_base import BaseService
from backend.exceptions import BusinessRuleViolation, EntityNotFoundError
from backend.validators.business_rules import BusinessRuleValidator


class EventService(BaseService[Event, Any, Any]):
    def __init__(self):
        super().__init__(Event)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create_event(
        self,
        db: Session,
        *,
        event_type: EventType,
        event_date: date | None = None,
        date_precision: DatePrecision = DatePrecision.UNKNOWN,
        description: str | None = None,
        location_type: LocationType = LocationType.STREET,
        participants: list[dict] | None = None,
    ) -> Event:
        """
        Create an event and attach participants.

        ``participants`` is a list of dicts like::

            [
                {"member_id": 1, "role": "shooter"},
                {"member_id": 2, "role": "victim"},
            ]
        """
        if event_type == EventType.PRISON_INCIDENT:
            location_type = LocationType.FACILITY

        event = Event(
            event_type=event_type,
            date=event_date,
            date_precision=date_precision,
            description=description,
            location_type=location_type,
        )
        db.add(event)
        db.flush()

        for p in participants or []:
            member = db.query(Member).filter(
                Member.id == p["member_id"], Member.deleted_at.is_(None),
            ).first()
            if not member:
                raise EntityNotFoundError("Member", p["member_id"])

            role = ParticipantRole(p["role"])

            # Gather sets for temporal check
            member_sets: list[Set] = []
            if member.set_id:
                s = db.query(Set).get(member.set_id)
                if s:
                    member_sets.append(s)

            BusinessRuleValidator.validate_event_participation(
                member, event_date, location_type, member_sets,
            )

            ep = EventParticipant(
                event_id=event.id,
                member_id=member.id,
                role=role,
            )
            db.add(ep)

        db.commit()
        db.refresh(event)
        return event

    # ------------------------------------------------------------------
    # Shortcut factories for legacy form compatibility
    # ------------------------------------------------------------------
    def create_murder(
        self,
        db: Session,
        *,
        shooter_id: int,
        victim_id: int,
        event_date: date | None = None,
        date_precision: DatePrecision = DatePrecision.UNKNOWN,
        description: str | None = None,
        update_victim_death: bool = False,
    ) -> Event:
        victim = db.query(Member).filter(
            Member.id == victim_id, Member.deleted_at.is_(None),
        ).first()
        if not victim:
            raise EntityNotFoundError("Member", victim_id)

        event = self.create_event(
            db,
            event_type=EventType.MURDER,
            event_date=event_date,
            date_precision=date_precision,
            description=description,
            location_type=LocationType.STREET,
            participants=[
                {"member_id": shooter_id, "role": ParticipantRole.SHOOTER.value},
                {"member_id": victim_id, "role": ParticipantRole.VICTIM.value},
            ],
        )

        if update_victim_death or victim.status != MemberStatus.DECEASED:
            victim.status = MemberStatus.DECEASED
            victim.death_date = event_date
            victim.death_date_precision = date_precision
            db.commit()

        return event

    def create_shooting(
        self,
        db: Session,
        *,
        shooter_id: int,
        victim_id: int,
        event_date: date | None = None,
        date_precision: DatePrecision = DatePrecision.UNKNOWN,
        description: str | None = None,
    ) -> Event:
        return self.create_event(
            db,
            event_type=EventType.SHOOTING,
            event_date=event_date,
            date_precision=date_precision,
            description=description,
            location_type=LocationType.STREET,
            participants=[
                {"member_id": shooter_id, "role": ParticipantRole.SHOOTER.value},
                {"member_id": victim_id, "role": ParticipantRole.VICTIM.value},
            ],
        )

    def create_assist(
        self,
        db: Session,
        *,
        shooter_id: int,
        victim_id: int,
        event_date: date | None = None,
        date_precision: DatePrecision = DatePrecision.UNKNOWN,
        description: str | None = None,
    ) -> Event:
        return self.create_event(
            db,
            event_type=EventType.ASSIST,
            event_date=event_date,
            date_precision=date_precision,
            description=description,
            location_type=LocationType.STREET,
            participants=[
                {"member_id": shooter_id, "role": ParticipantRole.SHOOTER.value},
                {"member_id": victim_id, "role": ParticipantRole.VICTIM.value},
            ],
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_by_type(
        self,
        db: Session,
        event_type: EventType,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Event]:
        return (
            self._base_query(db)
            .filter(Event.event_type == event_type)
            .order_by(Event.date.desc().nullslast())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_member(self, db: Session, member_id: int) -> List[Event]:
        ep_ids = [
            ep.event_id
            for ep in db.query(EventParticipant)
            .filter(EventParticipant.member_id == member_id)
            .all()
        ]
        if not ep_ids:
            return []
        return (
            self._base_query(db)
            .filter(Event.id.in_(ep_ids))
            .order_by(Event.date.desc().nullslast())
            .all()
        )

    def add_participant(
        self,
        db: Session,
        *,
        event_id: int,
        member_id: int,
        role: ParticipantRole,
    ) -> EventParticipant:
        event = self.get_or_404(db, event_id)
        member = db.query(Member).filter(
            Member.id == member_id, Member.deleted_at.is_(None),
        ).first()
        if not member:
            raise EntityNotFoundError("Member", member_id)

        member_sets: list[Set] = []
        if member.set_id:
            s = db.query(Set).get(member.set_id)
            if s:
                member_sets.append(s)

        BusinessRuleValidator.validate_event_participation(
            member, event.date, event.location_type, member_sets,
        )

        ep = EventParticipant(event_id=event_id, member_id=member_id, role=role)
        db.add(ep)
        db.commit()
        db.refresh(ep)
        return ep

    # ------------------------------------------------------------------
    # Date parsing helpers (for legacy form data)
    # ------------------------------------------------------------------
    @staticmethod
    def parse_event_date(
        precision: str | None,
        exact: str | None = None,
        year: str | None = None,
    ) -> tuple[date | None, DatePrecision]:
        if precision == "exact" and exact:
            return datetime.strptime(exact, "%Y-%m-%d").date(), DatePrecision.EXACT
        if precision == "year" and year and year.isdigit() and len(year) == 4:
            return None, DatePrecision.APPROXIMATE
        return None, DatePrecision.UNKNOWN


event_service = EventService()
