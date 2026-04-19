"""Backward-compat alias — real model lives in backend.database.models."""
from backend.database.models import Member as Members

__all__ = ["Members"]
