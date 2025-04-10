import os
import sys

# Set the test mode environment variable
os.environ["TEST_MODE"] = "1"

# Import after setting the environment variable
from backend.database.database import init_db
from main import add_test_data
from backend.config.config import settings

def initialize_test_database():
    """
    Initialize a test database with sample data.
    This creates a separate database file that won't affect your production data.
    """
    print(f"Initializing test database: {settings.get_db_path()}")
    
    # Always drop existing test database to start fresh
    init_db(drop_existing=True)
    
    # Add the test data from main.py
    add_test_data()
    
    print("Test database successfully initialized!")
    print("To run your application in test mode, set TEST_MODE=1 in your environment")
    print("Example: TEST_MODE=1 python main.py")
    print(f"Or modify the TEST_MODE setting in backend/config/config.py")

if __name__ == "__main__":
    initialize_test_database() 