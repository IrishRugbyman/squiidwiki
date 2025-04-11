from typing import Dict, List, Optional, Any
from backend.database.db_alchemy_models import Sets


class SetGrouping:
    """
    A class to represent a grouped collection of sets.
    This is used for grouping sets by first letter of their name.
    """
    
    def __init__(self, sets: List[Sets] = None):
        self.sets = sets or []
        self.grouped_sets: Dict[str, List[Dict[str, Any]]] = {}
    
    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert the grouped sets to a dictionary format suitable for templates.
        """
        return self.grouped_sets
    
    def add_set(self, set_obj: Sets) -> None:
        """
        Add a set to the collection.
        """
        self.sets.append(set_obj)


class SetRelations:
    """
    A class to represent relationships between sets (allies and enemies).
    """
    
    def __init__(self, set_id: int):
        self.set_id = set_id
        self.allies: List[Sets] = []
        self.enemies: List[Sets] = []
    
    def add_ally(self, ally: Sets) -> None:
        """
        Add an ally set.
        """
        self.allies.append(ally)
    
    def add_enemy(self, enemy: Sets) -> None:
        """
        Add an enemy set.
        """
        self.enemies.append(enemy)
    
    def get_ally_names(self) -> str:
        """
        Get comma-separated ally names.
        """
        return ", ".join(ally.name for ally in self.allies)
    
    def get_enemy_names(self) -> str:
        """
        Get comma-separated enemy names.
        """
        return ", ".join(enemy.name for enemy in self.enemies) 