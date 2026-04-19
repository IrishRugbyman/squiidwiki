"""
Custom exception hierarchy for SquiidWiki.

These are raised by the service / validator layers and caught by
FastAPI exception handlers registered in ``server.py``.
"""
from __future__ import annotations

from fastapi import HTTPException, status


class BusinessRuleViolation(HTTPException):
    """A domain-level integrity rule was violated (HTTP 422)."""

    def __init__(self, detail: str, *, field: str | None = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)
        self.field = field


class TemporalIntegrityError(BusinessRuleViolation):
    """An operation violates a temporal constraint (dates out of order)."""
    pass


class VitalStateError(BusinessRuleViolation):
    """Operation conflicts with a member's vital state (deceased / incarcerated)."""
    pass


class LocationConstraintError(BusinessRuleViolation):
    """Operation conflicts with a member's location constraint."""
    pass


class RelationshipCollisionWarning(HTTPException):
    """
    Allying with a set that is a rival of an existing ally (HTTP 409).

    Callers may override with ``force=True`` in the request body.
    """

    def __init__(self, detail: str, *, conflicting_sets: list[str] | None = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
        self.conflicting_sets = conflicting_sets or []


class SoftDeletedRecordError(HTTPException):
    """Attempted to access a soft-deleted record (HTTP 410)."""

    def __init__(self, entity: str, entity_id: int):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail=f"{entity} with id {entity_id} has been archived",
        )


class EntityNotFoundError(HTTPException):
    """Requested entity does not exist (HTTP 404)."""

    def __init__(self, entity: str, entity_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity} with id {entity_id} not found",
        )
