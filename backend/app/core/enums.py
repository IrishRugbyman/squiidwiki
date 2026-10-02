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


class SetRank(str, Enum):
    CEO = "CEO"
    CO_CEO = "CO_CEO"


class GangNation(str, Enum):
    """The Chicago super-alliance a gang rides under.

    FOLK is the six-pointed star (Detroit's "6"), PEOPLE the five-pointed star
    (the "5"). Los Angeles lineages (Crips, Bloods and their sets), Sureños and
    MS-13 carry none: where Detroit files them under the 5 or the 6, that is a
    local alignment and lives on the sets and alliances, not on the card.
    """

    FOLK = "FOLK"
    PEOPLE = "PEOPLE"


class AllianceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXTINCT = "EXTINCT"
    DORMANT = "DORMANT"


class IncidentType(str, Enum):
    SHOOTING = "SHOOTING"
    MURDER = "MURDER"
    FIGHT = "FIGHT"
    BOMBING = "BOMBING"
    ARSON = "ARSON"
    EXTORTION = "EXTORTION"
    KIDNAPPING = "KIDNAPPING"
    ROBBERY = "ROBBERY"
    CRASH = "CRASH"


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


class SetLineageKind(str, Enum):
    """How a child set came out of a parent set.

    Every kind reads in one direction, **child KIND parent**, so a row is
    unambiguous without knowing which column it came from: "Set B
    SPLINTERED_FROM Set A". Mixing readings inside one enum is what makes
    directional edges get stored backwards.

    MERGED_FROM is the one that reads the other way round in ordinary speech
    ("the old set merged into the new one"). It is named for the child here on
    purpose, to keep the single reading rule intact.
    """

    SPLINTERED_FROM = "SPLINTERED_FROM"
    RENAMED_FROM = "RENAMED_FROM"
    MERGED_FROM = "MERGED_FROM"
    YOUNGER_GENERATION_OF = "YOUNGER_GENERATION_OF"


class BusinessType(str, Enum):
    GAMING = "GAMING"
    NIGHTLIFE = "NIGHTLIFE"
    CONSTRUCTION = "CONSTRUCTION"
    PORT = "PORT"
    WASTE_MANAGEMENT = "WASTE_MANAGEMENT"
    HOSPITALITY = "HOSPITALITY"
    RETAIL = "RETAIL"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class BusinessStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    SEIZED = "SEIZED"


class BusinessRole(str, Enum):
    OWNER = "OWNER"
    FRONT = "FRONT"
    BENEFICIARY = "BENEFICIARY"


class MunicipalityKind(str, Enum):
    """What a municipality row is.

    DISTRICT partitions its city (Detroit's ZIP codes), so districts can be
    drawn together; NEIGHBORHOOD is a named area whose outline may overlap
    districts, and is drawn on its own layer.
    """

    CITY = "CITY"
    DISTRICT = "DISTRICT"
    NEIGHBORHOOD = "NEIGHBORHOOD"


class MediaKind(str, Enum):
    R2 = "R2"
    EXTERNAL_URL = "EXTERNAL_URL"


class CustodySystem(str, Enum):
    """Who issued a custody number, stored as VARCHAR so a new system is a code change.

    One member can hold numbers in several of these, and several in one of them
    (a jail booking number or an OTN is issued per arrest). MDOC and BOP are
    mirrored from their member columns until those are retired.
    """

    MDOC = "MDOC"  # Michigan Department of Corrections
    BOP = "BOP"  # Federal Bureau of Prisons register number, NNNNN-NNN
    GDC = "GDC"  # Georgia Department of Corrections ID
    GA_OTN = "GA_OTN"  # Georgia Offender Tracking Number, per arrest
    TDOC = "TDOC"  # Tennessee Department of Correction
    IDOC = "IDOC"  # Illinois Department of Corrections
    COOK_COUNTY_JAIL = "COOK_COUNTY_JAIL"  # Cook County Sheriff booking number
    RICHMOND_COUNTY_JAIL = "RICHMOND_COUNTY_JAIL"  # Augusta, Webster Detention Center
