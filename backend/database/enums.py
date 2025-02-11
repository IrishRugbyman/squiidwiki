from enum import Enum

class eStatus(str, Enum):
    DEAD = "dead"
    ALIVE = "alive"
    LOCKED_UP = "locked_up"
    UNKNOWN = "unknown"

class eSetType(str, Enum):
    ACTIVE = "active"  # The set is currently active
    EXTINCT = "extinct"  # The set is no longer active

class eEventTypes(str, Enum):
    MURDERS = "murders"
    ASSISTS = "assists"
    SHOOTINGS = "shootings"