# Import order matters: tables must be defined before tables that reference them.
from app.models.alliance import (
    Alliance,
    AllianceMunicipality,
    AllianceRelationship,
    AllianceSet,
)
from app.models.auth import AuditLog, User, UserUniverseAccess
from app.models.business import Business, BusinessMember, BusinessSet, BusinessSource
from app.models.gang import Gang, GangCard
from app.models.gang_set import (
    GangSet,
    SetGang,
    SetLineage,
    SetMunicipality,
    SetRelationship,
    SetSource,
)
from app.models.incident import (
    Incident,
    IncidentParticipant,
    IncidentSetParticipant,
    IncidentSource,
)
from app.models.media import Media
from app.models.member import (
    Member,
    MemberAlias,
    MemberCustodyId,
    MemberIncarceration,
    MemberSet,
    MemberSource,
)
from app.models.municipality import Municipality, MunicipalityOverlap, MunicipalitySource
from app.models.research_note import ResearchNote
from app.models.source import Source
from app.models.universe import Universe

__all__ = [
    "User",
    "UserUniverseAccess",
    "AuditLog",
    "Universe",
    "Municipality",
    "MunicipalitySource",
    "MunicipalityOverlap",
    "Source",
    "Gang",
    "GangCard",
    "Alliance",
    "AllianceMunicipality",
    "AllianceRelationship",
    "AllianceSet",
    "Business",
    "BusinessMember",
    "BusinessSet",
    "BusinessSource",
    "GangSet",
    "SetLineage",
    "SetGang",
    "SetMunicipality",
    "SetRelationship",
    "SetSource",
    "Member",
    "MemberAlias",
    "MemberCustodyId",
    "MemberIncarceration",
    "MemberSet",
    "MemberSource",
    "Incident",
    "IncidentParticipant",
    "IncidentSetParticipant",
    "IncidentSource",
    "ResearchNote",
    "Media",
]
