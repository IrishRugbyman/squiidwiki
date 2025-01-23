from pathlib import Path
from fastapi.templating import Jinja2Templates
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Adjust path as needed
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

def format_datetime(value, format="%Y-%m-%d"):
    try:
        # Handle year-only format from database
        if isinstance(value, str) and len(value) == 4 and value.isdigit():
            return value
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except (ValueError, TypeError):
        return value  # Return raw value if parsing fails

# Initialize templates with the filter
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters["datetime"] = format_datetime