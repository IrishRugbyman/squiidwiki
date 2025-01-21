import sqlite3

def get_db():
    conn = sqlite3.connect('squiidvault.db')
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS set_allies_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            ally_id INTEGER NOT NULL,
            FOREIGN KEY (set_id) REFERENCES sets (id),
            FOREIGN KEY (ally_id) REFERENCES sets (id),
            UNIQUE (set_id, ally_id) -- Prevent duplicate ally relationships
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS set_enemies_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id INTEGER NOT NULL,
            enemy_id INTEGER NOT NULL,
            FOREIGN KEY (set_id) REFERENCES sets (id),
            FOREIGN KEY (enemy_id) REFERENCES sets (id),
            UNIQUE (set_id, enemy_id) -- Prevent duplicate enemy relationships
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alliances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alliance_member_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alliance_id INTEGER NOT NULL,
            set_id INTEGER NOT NULL,
            role TEXT, -- Optional: Role of the set in the alliance
            join_date TEXT, -- Optional: ISO 8601 format YYYY-MM-DD
            FOREIGN KEY (alliance_id) REFERENCES alliances (id),
            FOREIGN KEY (set_id) REFERENCES sets (id),
            UNIQUE (alliance_id, set_id) -- Prevent duplicate mappings
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT CHECK (status IN ('alive', 'dead', 'unknown')),
            release_date TEXT, -- ISO 8601 format YYYY-MM-DD
            date_of_death TEXT, -- ISO 8601 format YYYY-MM-DD
            set_id INTEGER,
            FOREIGN KEY (set_id) REFERENCES sets (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shootings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shooter_id INTEGER NOT NULL,
            victim_id INTEGER NOT NULL,
            date TEXT NOT NULL, -- Store as year (e.g., '2025')
            FOREIGN KEY (shooter_id) REFERENCES members (id),
            FOREIGN KEY (victim_id) REFERENCES members (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS murders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shooter_id INTEGER NOT NULL,
            victim_id INTEGER NOT NULL,
            date TEXT NOT NULL, -- Store as year (e.g., '2025')
            FOREIGN KEY (shooter_id) REFERENCES members (id),
            FOREIGN KEY (victim_id) REFERENCES members (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shooter_id INTEGER NOT NULL,
            victim_id INTEGER NOT NULL,
            date TEXT NOT NULL, -- Store as year (e.g., '2025')
            FOREIGN KEY (shooter_id) REFERENCES members (id),
            FOREIGN KEY (victim_id) REFERENCES members (id)
        )
    ''')

    # Adding indexes for optimized queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_members_set_id ON members (set_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_shootings_date ON shootings (date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_murders_date ON murders (date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_assists_date ON assists (date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alliance_member_map ON alliance_member_map (alliance_id, set_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_set_allies_map ON set_allies_map (set_id, ally_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_set_enemies_map ON set_enemies_map (set_id, enemy_id)
    ''')

    conn.commit()
    conn.close()

# Initialize the database
if __name__ == "__main__":
    init_db()
