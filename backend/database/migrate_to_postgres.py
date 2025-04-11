import os
import sys
import psycopg2
import psycopg2.extras
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

def migrate_structure():
    """
    Crée ou met à jour la structure de la base de données PostgreSQL.
    Initialise toutes les tables, index, et contraintes nécessaires.
    """
    try:
        print("Début de la migration de la structure vers PostgreSQL...")
        
        # Configuration de la connexion
        conn = psycopg2.connect(
            dbname="squiidvault",
            user="postgres",
            password="F$Stagiaire42",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        # Commencer une transaction
        cursor.execute("BEGIN;")

        # Supprimer les tables existantes si elles existent
        cursor.execute("DROP TABLE IF EXISTS config CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS set_allies_map CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS set_enemies_map CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS alliance_sets_map CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS alliances CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS members CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS shootings CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS murders CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS assists CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS sets CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE;")

        # Créer les tables
        # Table sets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sets (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                type TEXT NOT NULL DEFAULT 'active' CHECK (type IN ('active', 'extinct', 'system')),
                emoji TEXT
            )
        ''')

        # Table set_allies_map
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_allies_map (
                id SERIAL PRIMARY KEY,
                set_id INTEGER NOT NULL,
                ally_id INTEGER NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (ally_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, ally_id)
            )
        ''')

        # Table set_enemies_map
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS set_enemies_map (
                id SERIAL PRIMARY KEY,
                set_id INTEGER NOT NULL,
                enemy_id INTEGER NOT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                FOREIGN KEY (enemy_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (set_id, enemy_id)
            )
        ''')

        # Table alliances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliances (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        ''')

        # Table alliance_sets_map
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliance_sets_map (
                id SERIAL PRIMARY KEY,
                alliance_id INTEGER NOT NULL,
                set_id INTEGER NOT NULL,
                FOREIGN KEY (alliance_id) REFERENCES alliances(id) ON DELETE CASCADE,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE,
                UNIQUE (alliance_id, set_id)
            )
        ''')

        # Table members
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL CHECK (status IN ('dead', 'alive', 'locked_up', 'unknown')),
                release_date DATE,
                release_date_approx TEXT DEFAULT 'unknown',
                death_date DATE,
                death_date_approx TEXT DEFAULT 'unknown',
                set_id INTEGER,
                alliance_id INTEGER DEFAULT NULL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE SET NULL
            )
        ''')

        # Table shootings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shootings (
                id SERIAL PRIMARY KEY,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                date DATE,
                date_approx TEXT DEFAULT 'unknown',
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Table murders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS murders (
                id SERIAL PRIMARY KEY,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL UNIQUE,
                date DATE,
                date_approx TEXT DEFAULT 'unknown',
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Table assists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assists (
                id SERIAL PRIMARY KEY,
                shooter_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                date DATE,
                date_approx TEXT DEFAULT 'unknown',
                FOREIGN KEY (shooter_id) REFERENCES members(id),
                FOREIGN KEY (victim_id) REFERENCES members(id)
            )
        ''')

        # Table config
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value INTEGER UNIQUE
            )
        ''')

        # Table users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Valider la transaction
        conn.commit()
        print("Migration de la structure terminée avec succès!")
        print("Base de données: squiidvault")
        print("Toutes les tables ont été créées avec leurs contraintes et index.")
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"Erreur lors de la migration: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_structure() 