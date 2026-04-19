"""Backward-compat alias — real model lives in backend.database.models."""
from backend.database.models import User as Users

__all__ = ["Users"]
