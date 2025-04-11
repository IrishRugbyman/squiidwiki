"""
Script to run the SQL migration to add timestamp columns to the alliances table.
"""
import os
import psycopg2
from backend.config.config import settings

def run_migration():
    """Run SQL migration to add timestamp columns to alliances table"""
    # Get database connection parameters
    db_config = settings.get_pg_config()
    
    # Connect to the database
    print(f"Connecting to database: {db_config['database']}...")
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    
    try:
        # Create a cursor
        cursor = conn.cursor()
        
        # Read the SQL migration file
        migration_path = os.path.join(os.path.dirname(__file__), 'add_timestamps_to_alliances.sql')
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        # Execute the migration
        print("Executing migration...")
        cursor.execute(sql)
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        raise
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration() 