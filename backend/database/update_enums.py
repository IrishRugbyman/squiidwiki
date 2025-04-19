"""
Migration script to update existing enum columns with named enums.
"""
import logging
import psycopg2
from backend.config.config import settings

logger = logging.getLogger(__name__)

def update_enum_types():
    """
    Update existing enum columns to use named enums.
    This script carefully modifies existing tables without data loss.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Get database connection parameters
    db_config = settings.get_pg_config()
    
    logger.info(f"Connecting to database: {db_config['database']}...")
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        
        cursor = conn.cursor()
        
        # Migration operations
        operations = [
            """
            -- Create new enum types
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'set_type_enum') THEN
                    CREATE TYPE set_type_enum AS ENUM ('active', 'extinct', 'system');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'member_status_enum') THEN
                    CREATE TYPE member_status_enum AS ENUM ('dead', 'alive', 'locked_up', 'unknown');
                END IF;
            END$$;
            """,
            """
            -- Update sets table - add new column, copy data, drop old column, rename new column
            ALTER TABLE sets ADD COLUMN type_new set_type_enum;
            UPDATE sets SET type_new = type::text::set_type_enum;
            ALTER TABLE sets ALTER COLUMN type_new SET NOT NULL;
            ALTER TABLE sets ALTER COLUMN type_new SET DEFAULT 'active';
            ALTER TABLE sets DROP COLUMN type;
            ALTER TABLE sets RENAME COLUMN type_new TO type;
            """,
            """
            -- Update members table - add new column, copy data, drop old column, rename new column
            ALTER TABLE members ADD COLUMN status_new member_status_enum;
            UPDATE members SET status_new = status::text::member_status_enum;
            ALTER TABLE members ALTER COLUMN status_new SET NOT NULL;
            ALTER TABLE members DROP COLUMN status;
            ALTER TABLE members RENAME COLUMN status_new TO status;
            """
        ]
        
        # Execute each operation as a separate transaction
        for operation in operations:
            try:
                cursor.execute(operation)
                conn.commit()
                logger.info(f"Successfully executed: {operation.strip().split('--')[1] if '--' in operation else operation.strip()[:40]+'...'}")
            except psycopg2.Error as e:
                logger.warning(f"Operation failed (may already be applied): {str(e)}")
                conn.rollback()
        
        logger.info("Enum type migration completed")
        return True
            
    except Exception as e:
        logger.error(f"Error updating enum types: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_enum_types() 