from enum import Enum


class DatePrecision(str, Enum):
    Y = "Y"
    YM = "YM"
    YMD = "YMD"
    UNKNOWN = "UNKNOWN"


class MemberStatus(str, Enum):
    FREE = "FREE"
    LOCKED = "LOCKED"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"
    ESCAPEE = "ESCAPEE"
    ABSCONDER = "ABSCONDER"


class SetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXTINCT = "EXTINCT"


class AllianceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXTINCT = "EXTINCT"
    DORMANT = "DORMANT"


class IncidentType(str, Enum):
    SHOOTING = "SHOOTING"
    MURDER = "MURDER"
    FIGHT = "FIGHT"


class ParticipantRole(str, Enum):
    SHOOTER = "SHOOTER"
    ASSISTED = "ASSISTED"
    BYSTANDER = "BYSTANDER"
    VICTIM = "VICTIM"


class ParticipantOutcome(str, Enum):
    KILLED = "KILLED"
    INJURED = "INJURED"
    UNHARMED = "UNHARMED"
    UNKNOWN = "UNKNOWN"


class SourceReliability(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNVERIFIED = "UNVERIFIED"


class GlobalRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class UniverseRole(str, Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class SetRelationshipType(str, Enum):
    FRIEND = "FRIEND"
    ENEMY = "ENEMY"


class MediaKind(str, Enum):
    R2 = "R2"
    EXTERNAL_URL = "EXTERNAL_URL"
