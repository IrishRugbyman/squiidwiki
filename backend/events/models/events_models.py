"""Backward-compat alias — real model lives in backend.database.models.

Old Assists/Murders/Shootings tables are replaced by Incident in Phase 7.
"""
from backend.database.models import Incident as Assists, Incident as Murders, Incident as Shootings

__all__ = ["Assists", "Murders", "Shootings"]
