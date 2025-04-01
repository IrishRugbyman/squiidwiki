from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.db_alchemy_models import Config, SetAlliesMap, SetEnemiesMap, Sets


def group_sets(sets: List[Sets]) -> Dict[str, List[Sets]]:
    """
    Group sets by the first alphabetical character of their name.
    Non-alphabetical names are grouped under '#'.
    """
    grouped = {}
    for s in sets:
        first_char = s.name[0].upper() if s.name and s.name[0].isalpha() else '#'
        grouped.setdefault(first_char, []).append(s)
    return grouped


def process_relations(db: Session, set_id: int, relation_names: Optional[str], mapping_class):
    """
    Processes relation links (used for both allies and enemies).

    For the provided mapping_class (either SetAlliesMap or SetEnemiesMap),
    this function:
      - Finds current relation IDs.
      - Parses new relation names to determine new relation IDs.
      - Calculates which relations to remove and which to add.
      - Removes and adds mappings in both directions.
    """
    if mapping_class == SetAlliesMap:
        relation_attr = "ally_id"
    elif mapping_class == SetEnemiesMap:
        relation_attr = "enemy_id"
    else:
        raise ValueError(f"Unknown relation mapping: {mapping_class}")

    current_relations = db.query(mapping_class).filter(mapping_class.set_id == set_id).all()
    current_relation_ids = {getattr(r, relation_attr) for r in current_relations}
    new_relation_ids = set()
    if relation_names:
        names = [name.strip() for name in relation_names.split(",") if name.strip()]
        for name in names:
            target_set = db.query(Sets).filter(Sets.name == name).first()
            if target_set:
                new_relation_ids.add(target_set.id)
    removed_relation_ids = current_relation_ids - new_relation_ids
    added_relation_ids = new_relation_ids - current_relation_ids

    # Remove relations in both directions.
    for rid in removed_relation_ids:
        db.query(mapping_class).filter(mapping_class.set_id == set_id,
                                       getattr(mapping_class, relation_attr) == rid).delete()
        db.query(mapping_class).filter(mapping_class.set_id == rid,
                                       getattr(mapping_class, relation_attr) == set_id).delete()

    # Add new relations in both directions.
    for rid in added_relation_ids:
        new_mapping = mapping_class(set_id=set_id, **{relation_attr: rid})
        new_mapping_reverse = mapping_class(set_id=rid, **{relation_attr: set_id})
        db.add(new_mapping)
        db.add(new_mapping_reverse)


def get_special_set_id(db: Session, set_type: str) -> Optional[int]:
    """
    Retrieves the ID of a special set (e.g., 'unknown' or 'civilian')
    from the Config table.
    """
    config_entry = db.query(Config).filter(Config.key == f"{set_type}_set_id").first()
    return config_entry.value if config_entry else None
