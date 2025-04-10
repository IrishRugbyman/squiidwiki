from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Create engine and session
engine = create_engine('sqlite:///squiidvault.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate():
    db = SessionLocal()
    try:
        # Drop any existing views
        db.execute(text("DROP VIEW IF EXISTS groups"))
        
        # Check if the sets table exists
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='sets'"))
        if result.fetchone() is None:
            # If the table doesn't exist, create it with the new schema
            db.execute(text("""
                CREATE TABLE sets (
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK(type IN ('active', 'extinct', 'system')) DEFAULT 'active',
                    id INTEGER PRIMARY KEY,
                    description TEXT,
                    emoji TEXT
                )
            """))
            print("Created new sets table with system type support")
        else:
            # If the table exists, migrate it
            # Create a temporary table with the new schema
            db.execute(text("""
                CREATE TABLE sets_new (
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK(type IN ('active', 'extinct', 'system')) DEFAULT 'active',
                    id INTEGER PRIMARY KEY,
                    description TEXT,
                    emoji TEXT
                )
            """))
            
            # Copy data from old table to new table
            db.execute(text("""
                INSERT INTO sets_new (name, type, id, description, emoji)
                SELECT name, 
                       CASE 
                           WHEN type NOT IN ('active', 'extinct', 'system') THEN 'active'
                           ELSE type 
                       END as type,
                       id, description, emoji
                FROM sets
            """))
            
            # Drop the old table
            db.execute(text("DROP TABLE sets"))
            
            # Rename the new table to the original name
            db.execute(text("ALTER TABLE sets_new RENAME TO sets"))
            print("Migrated existing sets table to support system type")
        
        # Recreate the related tables if they don't exist
        tables = ['alliance_sets_map', 'set_allies_map', 'set_enemies_map', 'members']
        for table in tables:
            result = db.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
            if result.fetchone() is None:
                if table == 'alliance_sets_map':
                    db.execute(text("""
                        CREATE TABLE alliance_sets_map (
                            alliance_id INTEGER NOT NULL,
                            set_id INTEGER NOT NULL,
                            id INTEGER PRIMARY KEY,
                            UNIQUE(alliance_id, set_id),
                            FOREIGN KEY (alliance_id) REFERENCES alliances(id) ON DELETE CASCADE,
                            FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE
                        )
                    """))
                elif table == 'set_allies_map':
                    db.execute(text("""
                        CREATE TABLE set_allies_map (
                            set_id INTEGER NOT NULL,
                            ally_id INTEGER NOT NULL,
                            id INTEGER PRIMARY KEY,
                            UNIQUE(set_id, ally_id),
                            FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                            FOREIGN KEY (ally_id) REFERENCES sets(id) ON DELETE CASCADE
                        )
                    """))
                elif table == 'set_enemies_map':
                    db.execute(text("""
                        CREATE TABLE set_enemies_map (
                            set_id INTEGER NOT NULL,
                            enemy_id INTEGER NOT NULL,
                            id INTEGER PRIMARY KEY,
                            UNIQUE(set_id, enemy_id),
                            FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                            FOREIGN KEY (enemy_id) REFERENCES sets(id) ON DELETE CASCADE
                        )
                    """))
                elif table == 'members':
                    db.execute(text("""
                        CREATE TABLE members (
                            name TEXT NOT NULL,
                            status TEXT NOT NULL,
                            id INTEGER PRIMARY KEY,
                            description TEXT,
                            release_date DATE,
                            release_date_approx TEXT DEFAULT 'unknown',
                            death_date DATE,
                            death_date_approx TEXT DEFAULT 'unknown',
                            set_id INTEGER,
                            alliance_id INTEGER DEFAULT NULL,
                            FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE SET NULL
                        )
                    """))
                print(f"Created new {table} table")
        
        # Recreate the groups view
        db.execute(text("""
            CREATE VIEW IF NOT EXISTS groups AS
            SELECT s.*, COUNT(m.id) as member_count
            FROM sets s
            LEFT JOIN members m ON s.id = m.set_id
            GROUP BY s.id
        """))
        print("Recreated groups view")
        
        db.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate() 