import sqlite3
from pathlib import Path
import os
from backend.config.config import settings

# Define the path to the SQLite database file
# Use a different database file for testing based on environment variable
TEST_MODE = os.environ.get("TEST_MODE", "0") == "1"
if TEST_MODE:
    DB_PATH = Path(__file__).parent.parent.parent / "squiidvault_test.db"
    print(f"Running in TEST MODE using database: {DB_PATH}")
else:
    DB_PATH = Path(__file__).parent.parent.parent / "squiidvault.db"


def get_db():
    """
    Establishes and returns a connection to the SQLite database.
    Uses the centralized configuration for the database path.
    """
    conn = sqlite3.connect(settings.get_db_path())
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db(drop_existing: bool = False):
    """
    Initializes the database schema and sets up necessary tables, indexes, and triggers.
    If `drop_existing` is True, existing tables are dropped and recreated (for development purposes).

    Args:
        drop_existing (bool): If True, drops existing tables and recreates them. Defaults to False.
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        if drop_existing:
            # Disable foreign keys temporarily to allow dropping tables with dependencies
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Drop all existing tables to start with a clean slate (development only!)
            cursor.execute('DROP TABLE IF EXISTS config')
            cursor.execute('DROP TABLE IF EXISTS set_allies_map')
            cursor.execute('DROP TABLE IF EXISTS set_enemies_map')
            cursor.execute('DROP TABLE IF EXISTS alliance_sets_map')
            cursor.execute('DROP TABLE IF EXISTS alliances')
            cursor.execute('DROP TABLE IF EXISTS members')
            cursor.execute('DROP TABLE IF EXISTS shootings')
            cursor.execute('DROP TABLE IF EXISTS murders')
            cursor.execute('DROP TABLE IF EXISTS assists')
            cursor.execute('DROP TABLE IF EXISTS sets')
            cursor.execute('DROP TABLE IF EXISTS users')

            # Re-enable foreign key constraints after dropping tables
            cursor.execute("PRAGMA foreign_keys = ON")

        # --- RECREATE ALL TABLES PROPERLY ---

        # Create the main `sets` table to store gang/clique information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,  -- Name of the set (gang/clique)
                description TEXT,          -- Description of the set
                type TEXT NOT NULL CHECK (type IN ('active', 'extinct', 'system')) DEFAULT 'active',  -- Status of the set
                emoji TEXT                 -- Emoji representing the set
            )
        ''')

        # Create the `set_allies_map` table to track alliances between sets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_allies_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,   -- ID of the set
                ally_id INTEGER NOT NULL,  -- ID of the allied set
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (ally_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, ally_id)  -- Ensure unique alliance pairs
            )
        ''')

        # Create the `set_enemies_map` table to track rivalries between sets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_enemies_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,   -- ID of the set
                enemy_id INTEGER NOT NULL, -- ID of the enemy set
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (enemy_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, enemy_id)  -- Ensure unique rivalry pairs
            )
        ''')

        # Create the `alliances` table to store alliance groups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,  -- Name of the alliance
                description TEXT,          -- Description of the alliance
                status TEXT NOT NULL CHECK (status IN ('active', 'inactive')) DEFAULT 'active'  -- Status of the alliance
            )
        ''')
        # this table is for establihed alliances, that have a name and are official, it shouldn't be confused with the simple fact that two sets
        # can be allies without being in an established alliance

        # Create the `alliance_sets_map` table to track which sets belong to which alliances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliance_sets_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alliance_id INTEGER NOT NULL,  -- ID of the alliance
                set_id INTEGER NOT NULL,       -- ID of the set in the alliance
                FOREIGN KEY (alliance_id) REFERENCES alliances(id) ON DELETE CASCADE,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (alliance_id, set_id)  -- Ensure unique set-alliance pairs
            )
        ''')

        # Create the `members` table to store individual gang members
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,            -- Name of the member
                description TEXT,             -- Description of the member
                status TEXT NOT NULL CHECK (status IN ('dead', 'alive', 'locked_up', 'unknown')),  -- Member status
                release_date DATE,            -- Date of release (if applicable)
                release_date_approx TEXT DEFAULT 'unknown',  -- Approximate release date (unknown, YYYY, or 'life')
                death_date DATE,           -- Date of death (if applicable)
                death_date_approx TEXT DEFAULT 'unknown',    -- Approximate death date (unknown, YYYY, or 'life')
                set_id INTEGER,               -- ID of the set the member belongs to
                alliance_id INTEGER DEFAULT NULL,          -- ID of the alliance the member belongs to
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE SET NULL
            )
        ''')

        # Create the `shootings` table to track non-fatal shooting incidents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shootings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,  -- ID of the shooter
                victim_id INTEGER NOT NULL,   -- ID of the victim
                date DATE,                    -- Date of the shooting
                date_approx TEXT DEFAULT 'unknown',  -- if a precise date exists, the approx date is the year of the precise date, otherwise it's 'unknown' or 'YYYY' (if only the year is known)
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Create the `murders` table to track fatal shooting incidents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS murders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,  -- ID of the shooter
                victim_id INTEGER NOT NULL UNIQUE,  -- ID of the victim (unique to ensure one victim per murder)
                date DATE,                    -- Date of the murder
                date_approx TEXT DEFAULT 'unknown',  -- if a precise date exists, the approx date is the year of the precise date, otherwise it's 'unknown' or 'YYYY' (if only the year is known)
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Create the `assists` table to track collaborative attacks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,  -- ID of the shooter
                victim_id INTEGER NOT NULL,   -- ID of the victim
                date DATE,                    -- Date of the assist
                date_approx TEXT DEFAULT 'unknown',  -- if a precise date exists, the approx date is the year of the precise date, otherwise it's 'unknown' or 'YYYY' (if only the year is known)
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')
        # the date of an assist should always be the same as the murder it's tied to or the death date if the murder is not recorded yet

        # Create the `config` table to store configuration values (e.g., special set IDs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,  -- Configuration key
                value INTEGER UNIQUE   -- Configuration value
            )
        ''')

        # Create users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create a default admin user (username: admin, password: admin)
        # Note: In production, you should use a more secure password
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, is_admin)
            VALUES ('admin', '$2b$12$oGK0TrigRXOScvPUo3ysROaYq4fmQ5aKb55qL8JudwHLU6WX8D9Xa', 1)
        ''')
        
        # Also add a backup admin user with a simpler hash in case there are bcrypt compatibility issues
        # cursor.execute('''
        #     INSERT OR IGNORE INTO users (username, password_hash, is_admin)
        #     VALUES ('superadmin', 'admin', 1)
        # ''')

        # --- REST OF INITIALIZATION CODE ---

        # Initialize Default Sets
        cursor.execute('''
            INSERT OR IGNORE INTO sets (name, description, type, emoji)
            VALUES ('Unknown', 'Default set for members with unknown set affiliation', 'system', '❓')
        ''')
        cursor.execute('SELECT id FROM sets WHERE name = "Unknown"')
        unknown_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT OR IGNORE INTO sets (name, description, type, emoji)
            VALUES ('Civilian', 'Default set for non-gang affiliated victims', 'system', '👤')
        ''')
        cursor.execute('SELECT id FROM sets WHERE name = "Civilian"')
        civilian_id = cursor.fetchone()[0]

        # Retrieve and store special set IDs in the `config` table
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value)
            VALUES ('unknown_set_id', ?), ('civilian_set_id', ?)
        ''', (unknown_id, civilian_id))

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_members_set_id ON members (set_id)
        ''')
        # ... other indexes can be added here ...

        # Create triggers to protect special sets from deletion or modification
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS prevent_special_sets_delete
            BEFORE DELETE ON sets
            WHEN OLD.id IN (SELECT value FROM config)
            BEGIN
                SELECT RAISE(ABORT, 'Cannot delete system sets');
            END;
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS prevent_special_sets_update
            BEFORE UPDATE OF id, name ON sets
            WHEN OLD.id IN (SELECT value FROM config)
            BEGIN
                SELECT RAISE(ABORT, 'Cannot modify system sets');
            END;
        ''')

        # Use the same PRAGMA settings for all connections to ensure consistency
        cursor.execute("PRAGMA journal_mode = WAL")  # Write-ahead logging for better concurrency
        cursor.execute("PRAGMA foreign_keys = ON")   # Enforce foreign key constraints

        # Commit the transaction
        conn.commit()
        
        if settings.is_test():
            print(f"Database initialized successfully in TEST MODE: {settings.get_db_path()}")
        else:
            print(f"Database initialized successfully: {settings.get_db_path()}")

    except Exception as e:
        # Rollback in case of any errors
        conn.rollback()
        raise RuntimeError(f"Database initialization failed: {str(e)}")

    finally:
        # Close the database connection
        conn.close()


def get_special_set_id(set_type: str) -> int:
    """
    Retrieves the ID of a special set (e.g., unknown or civilian) from the `config` table.

    Args:
        set_type (str): The type of special set (e.g., 'unknown' or 'civilian').

    Returns:
        int: The ID of the special set.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value FROM config WHERE key = ?
        ''', (f'{set_type}_set_id',))
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_total_sets() -> int:
    """
    Returns the total number of sets (gangs/cliques) in the database.

    Returns:
        int: The total number of sets.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sets")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_total_members() -> int:
    """
    Returns the total number of members in the database.

    Returns:
        int: The total number of members.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def get_total_alliances() -> int:
    """
    Returns the total number of alliances in the database.

    Returns:
        int: The total number of alliances.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM alliances")
        return cursor.fetchone()[0]
    finally:
        conn.close()