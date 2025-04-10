import shutil
import os
from datetime import datetime
from pathlib import Path
from backend.config.config import settings

def backup_database():
    """
    Creates a backup of the production database with a timestamp.
    """
    # Don't backup test database
    if settings.is_test():
        print("ERROR: Cannot backup test database. Set TEST_MODE=0 to backup the production database.")
        return False
    
    # Get the current date and time for the backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define source and destination paths
    source_path = Path(settings.get_db_path())
    backup_dir = settings.BACKUP_DIR
    backup_path = backup_dir / f"squiidvault_backup_{timestamp}.db"
    
    # Ensure the backup directory exists
    backup_dir.mkdir(exist_ok=True)
    
    try:
        # Check if the source database exists
        if not source_path.exists():
            print(f"Error: Source database '{source_path}' not found!")
            return False
        
        # Create the backup
        shutil.copy2(source_path, backup_path)
        
        print(f"Backup created successfully: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False

if __name__ == "__main__":
    backup_database() 