"""
Stub implementations of database PostgreSQL functions.
These functions are used during initialization but we're moving to SQLAlchemy models.
"""

def get_db():
    """
    Stub function for database connection.
    This has been replaced by SQLAlchemy session.
    """
    raise NotImplementedError("Direct database access is no longer used. Use SQLAlchemy session instead.")

def init_db(drop_existing: bool = False):
    """
    Initialize the database schema.
    This is a stub function since we're moving to SQLAlchemy models.
    """
    print("Database initialization skipped - using SQLAlchemy models")
    return True

def get_special_set_id(set_type: str) -> int:
    """
    Get the ID of a special set (unknown or civilian).
    This is a stub function since we're moving to SQLAlchemy models.
    """
    # Return a default value
    return 1

def get_total_sets() -> int:
    """Stub function to get the total number of sets."""
    return 0

def get_total_members() -> int:
    """Stub function to get the total number of members."""
    return 0

def get_total_alliances() -> int:
    """Stub function to get the total number of alliances."""
    return 0 