"""Central re-export hub for database models and session utilities.

All names here use the *new* consolidated models from backend.database.models.
Legacy aliases (Users, Sets, Members, etc.) keep existing router code importable
while the per-domain rewrite is in progress.
"""
from backend.database.base_class import Base, SessionLocal, engine, get_db, get_db_context
from backend.database.models import (
    # Config / system
    Config,
    DbEnum as Enums,
    # Auth
    User as Users,
    # Sets
    Set as Sets,
    SetRelationship as SetAlliesMap,
    SetRelationship as SetEnemiesMap,
    # Alliances
    Alliance,
    AllianceSetMap as AllianceSetsMap,
    AllianceSetMap,
    # Members
    Member as Members,
    # Incidents (replaced Events in Phase 7)
    Incident as Assists,
    Incident as Murders,
    Incident as Shootings,
    Incident,
    IncidentParticipant,
)

__all__ = [
    "Base", "SessionLocal", "engine", "get_db", "get_db_context",
    "Config", "Enums",
    "Users",
    "Sets", "SetAlliesMap", "SetEnemiesMap",
    "Alliance", "AllianceSetsMap", "AllianceSetMap",
    "Members",
    "Assists", "Murders", "Shootings", "Incident", "IncidentParticipant",
]
