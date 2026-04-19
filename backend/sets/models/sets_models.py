"""Backward-compat alias — real model lives in backend.database.models."""
from backend.database.models import (
    Set as Sets,
    SetRelationship as SetAlliesMap,
    SetRelationship as SetEnemiesMap,
)

__all__ = ["Sets", "SetAlliesMap", "SetEnemiesMap"]
