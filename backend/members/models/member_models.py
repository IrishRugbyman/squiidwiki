from typing import List, Dict, Any, Optional
from datetime import date
from backend.members.models.members_models import Members


class MemberActivity:
    """
    A class to represent a member's activity history.
    This includes shootings, murders and assists.
    """
    
    def __init__(self, member_id: int):
        self.member_id = member_id
        self.shootings: List[Dict[str, Any]] = []
        self.murders: List[Dict[str, Any]] = []
        self.assists: List[Dict[str, Any]] = []
    
    @property
    def total_events(self) -> int:
        """
        Get the total number of events for this member.
        """
        return len(self.shootings) + len(self.murders) + len(self.assists)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the activity history to a dictionary.
        """
        return {
            "member_id": self.member_id,
            "total_events": self.total_events,
            "shootings": self.shootings,
            "murders": self.murders,
            "assists": self.assists
        }


class MemberStatus:
    """
    A class to handle member status and related data.
    """
    ALIVE = "alive"
    LOCKED_UP = "locked_up"
    DEAD = "dead"
    UNKNOWN = "unknown"
    
    @staticmethod
    def is_valid_status(status: str) -> bool:
        """
        Check if a status value is valid.
        """
        valid_statuses = {
            MemberStatus.ALIVE,
            MemberStatus.LOCKED_UP,
            MemberStatus.DEAD,
            MemberStatus.UNKNOWN
        }
        return status in valid_statuses
    
    @staticmethod
    def get_release_info(member: Members) -> Dict[str, Any]:
        """
        Get release information for a member.
        """
        if member.status != MemberStatus.LOCKED_UP:
            return {
                "has_release_info": False
            }
        
        result = {
            "has_release_info": True,
            "release_date_approx": member.release_date_approx
        }
        
        if member.release_date:
            result["release_date"] = member.release_date
            result["release_date_formatted"] = member.release_date.strftime("%Y-%m-%d")
        
        return result
    
    @staticmethod
    def get_death_info(member: Members) -> Dict[str, Any]:
        """
        Get death information for a member.
        """
        if member.status != MemberStatus.DEAD:
            return {
                "has_death_info": False
            }
        
        result = {
            "has_death_info": True,
            "death_date_approx": member.death_date_approx
        }
        
        if member.death_date:
            result["death_date"] = member.death_date
            result["death_date_formatted"] = member.death_date.strftime("%Y-%m-%d")
        
        return result 