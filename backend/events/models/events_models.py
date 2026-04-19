"""Backward-compat alias — real model lives in backend.database.models.

Old Assists/Murders/Shootings tables are replaced by Event in the consolidated
model. These aliases keep legacy router imports from crashing until Phase 7.
"""
from backend.database.models import Event as Assists, Event as Murders, Event as Shootings

__all__ = ["Assists", "Murders", "Shootings"]
