import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "squiidvault.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db(drop_existing: bool = False):
    conn = get_db()
    cursor = conn.cursor()

    try:
        if drop_existing:
            # Disable foreign keys temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Clean slate removal (development only!)
            cursor.execute('DROP TABLE IF EXISTS config')
            cursor.execute('DROP TABLE IF EXISTS set_allies_map')
            cursor.execute('DROP TABLE IF EXISTS set_enemies_map')
            cursor.execute('DROP TABLE IF EXISTS alliance_member_map')
            cursor.execute('DROP TABLE IF EXISTS alliances')
            cursor.execute('DROP TABLE IF EXISTS members')
            cursor.execute('DROP TABLE IF EXISTS shootings')
            cursor.execute('DROP TABLE IF EXISTS murders')
            cursor.execute('DROP TABLE IF EXISTS assists')
            cursor.execute('DROP TABLE IF EXISTS sets')

            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

        # --- RECREATE ALL TABLES PROPERLY ---
        # Create main sets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                type TEXT NOT NULL CHECK (type IN ('active', 'extinct')) DEFAULT 'active'
            )
        ''')

        # Create relationship tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_allies_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                ally_id INTEGER NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (ally_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, ally_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_enemies_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                enemy_id INTEGER NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (enemy_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, enemy_id)
            )
        ''')

        # Create alliances tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliance_member_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alliance_id INTEGER NOT NULL,
                set_id INTEGER NOT NULL,
                role TEXT,
                join_date TEXT,
                FOREIGN KEY (alliance_id) REFERENCES alliances(id) ON DELETE CASCADE,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (alliance_id, set_id)
            )
        ''')

        # Create members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL CHECK (status IN ('dead', 'alive', 'locked_up', 'unknown')),
                release_date TEXT,
                date_of_death TEXT,
                set_id INTEGER,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE SET NULL
            )
        ''')

        # Create incident tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shootings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS murders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Create configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value INTEGER UNIQUE
            )
        ''')

        # --- REST OF INITIALIZATION CODE ---
        # Insert special sets
        special_sets = [
            ('?', 'Default set for unknown affiliations'),
            ('Civilians', 'Default set for non-gang members')
        ]

        for name, desc in special_sets:
            cursor.execute('''
                INSERT OR IGNORE INTO sets (name, description, type)
                VALUES (?, ?, 'active')
            ''', (name, desc))

        # Get and store special IDs
        cursor.execute('SELECT id FROM sets WHERE name = "?"')
        unknown_id = cursor.fetchone()[0]

        cursor.execute('SELECT id FROM sets WHERE name = "Civilians"')
        civilian_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value)
            VALUES ('unknown_set_id', ?), ('civilian_set_id', ?)
        ''', (unknown_id, civilian_id))

        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_members_set_id ON members (set_id)
        ''')
        # ... other indexes ...

        # Create protection triggers
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

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Database initialization failed: {str(e)}")

    finally:
        conn.close()


def get_special_set_id(set_type: str) -> int:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value FROM config WHERE key = ?
        ''', (f'{set_type}_set_id',))
        return cursor.fetchone()[0]
    finally:
        conn.close()