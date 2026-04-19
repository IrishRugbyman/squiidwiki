"""Backward-compat alias — real model lives in backend.database.models."""
from backend.database.models import (
    Alliance,
    AllianceSetMap as AllianceSetsMap,
)

# Legacy secondary table placeholder — routers that used this will be rewritten in Phase 11.
alliance_set_association = None

__all__ = ["Alliance", "AllianceSetsMap", "alliance_set_association"]
