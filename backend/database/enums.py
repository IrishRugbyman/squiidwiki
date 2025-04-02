from enum import Enum

class eStatus(str, Enum):
    DEAD = "dead"
    ALIVE = "alive"
    LOCKED_UP = "locked_up"
    # UNKNOWN = "unknown" NOT USED YET

class eSetType(str, Enum):
    ACTIVE = "active"  # The set is currently active
    EXTINCT = "extinct"  # The set is no longer active
    SYSTEM = "system"  # Special system sets (like unknown, civilian)

class eEventTypes(str, Enum):
    MURDERS = "murders"
    ASSISTS = "assists"
    SHOOTINGS = "shootings"