import os
import subprocess
import sys
from pathlib import Path

def setup_project():
    """
    Set up the project by:
    1. Installing dependencies
    2. Creating necessary directories
    3. Initializing the database
    4. Creating a test database
    """
    print("Setting up SquiidWiki project...")
    
    # Install dependencies
    print("\n1. Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Create necessary directories
    print("\n2. Creating necessary directories...")
    Path("backups").mkdir(exist_ok=True)
    
    # Create templates directory for error pages if it doesn't exist
    templates_dir = Path("frontend/templates/errors")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create basic error templates if they don't exist
    error_template = templates_dir / "error.html"
    if not error_template.exists():
        with open(error_template, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Error {{ status_code }}</title>
</head>
<body>
    <h1>Error {{ status_code }}</h1>
    <p>{{ error_message }}</p>
    {% if debug %}
    <h2>Details:</h2>
    <pre>{{ error_details | tojson(indent=2) }}</pre>
    {% endif %}
</body>
</html>""")
    
    not_found_template = templates_dir / "404.html"
    if not not_found_template.exists():
        with open(not_found_template, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
</head>
<body>
    <h1>404 Not Found</h1>
    <p>The requested resource could not be found.</p>
</body>
</html>""")
    
    server_error_template = templates_dir / "500.html"
    if not server_error_template.exists():
        with open(server_error_template, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>500 Server Error</title>
</head>
<body>
    <h1>500 Server Error</h1>
    <p>An internal server error has occurred.</p>
</body>
</html>""")
    
    # Initialize the main database
    print("\n3. Initializing the database...")
    subprocess.run([sys.executable, "main.py"], env=dict(os.environ, APP_ENV="development"))
    
    # Initialize the test database
    print("\n4. Creating test database...")
    subprocess.run([sys.executable, "init_test_db.py"])
    
    print("\nSetup complete! You can now run the application with:")
    print("python main.py")
    print("\nFor development with the test database:")
    print("$env:TEST_MODE=1; python main.py")

if __name__ == "__main__":
    setup_project() 