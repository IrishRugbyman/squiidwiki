from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from backend.database.imports import Config, SetAlliesMap, SetEnemiesMap, Sets


def group_sets(sets: List[Sets], db: Session) -> Dict[str, List[Sets]]:
    """
    Group sets by the first alphabetical character of their name.
    Special sets are grouped under '★' after the alphabetical groups.
    Non-alphabetical names are grouped under '#'.
    """
    grouped = {}
    
    # First, identify special sets
    special_set_ids = set()
    for set_type in ['unknown', 'civilian']:  # Add other special set types if needed
        special_id = get_special_set_id(db, set_type)
        if special_id:
            special_set_ids.add(special_id)
    
    # Group special sets separately
    special_sets = []
    regular_sets = []
    
    for s in sets:
        if s.id in special_set_ids:
            special_sets.append(s)
        else:
            regular_sets.append(s)
    
    # Group regular sets alphabetically first
    for s in regular_sets:
        first_char = s.name[0].upper() if s.name and s.name[0].isalpha() else '#'
        grouped.setdefault(first_char, []).append(s)
    
    # Sort regular sets within each group
    for char in grouped:
        grouped[char] = sorted(grouped[char], key=lambda s: s.name)
    
    # Add special sets group if there are any, using a symbol that will sort after letters
    if special_sets:
        grouped['★'] = sorted(special_sets, key=lambda s: s.name)
    
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