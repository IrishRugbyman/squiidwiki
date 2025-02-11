from pathlib import Path
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
from markupsafe import Markup

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"


def format_special_date(date_value, precision=None):
    """
    Formats a date based on its precision and value.

    Args:
        date_value (str or datetime.date): The date value (e.g., '2023-05-15' or 'circa 2020').
        precision (str): The precision ('exact', 'year', or None).

    Returns:
        Markup: HTML-formatted date string.
    """
    try:
        if not date_value:
            return Markup('<span class="date-unknown">Unknown</span>')

        # Convert datetime.date to string if necessary
        if isinstance(date_value, (date, datetime)):
            date_value = date_value.strftime("%Y-%m-%d")

        # Handle exact dates
        if precision == "exact":
            try:
                d = datetime.strptime(date_value, "%Y-%m-%d")
                return Markup(f'<span class="date-exact">{d.strftime("%d/%m/%Y")}</span>')
            except ValueError:
                return Markup('<span class="date-error">Invalid exact date</span>')

        # Handle year-only dates
        elif precision == "year":
            if date_value.isdigit() and len(date_value) == 4:
                return Markup(f'<span class="date-year">{date_value}</span> (approx)')
            else:
                return Markup('<span class="date-error">Invalid year</span>')

        # Handle approximate metadata (e.g., 'circa 2020')
        elif ":" in date_value:
            parts = date_value.split(":", 1)
            if len(parts) == 2:
                prefix, value = parts
                if prefix == "circa" and value.isdigit() and len(value) == 4:
                    return Markup(f'<span class="date-year">{value}</span> (approx)')
                else:
                    return Markup('<span class="date-error">Invalid metadata</span>')
            else:
                return Markup('<span class="date-error">Invalid metadata format</span>')

        # Fallback for legacy dates (if any)
        else:
            try:
                d = datetime.strptime(date_value, "%Y-%m-%d")
                return Markup(f'<span class="date-exact">{d.strftime("%d/%m/%Y")}</span>')
            except ValueError:
                return Markup('<span class="date-error">Invalid legacy date</span>')

    except Exception as e:
        return Markup(f'<span class="date-error">Error formatting date: {str(e)}</span>')




# Initialize templates and register the filter
templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters["format_special_date"] = format_special_date


# Keep existing datetime filter for general formatting
def format_datetime(value, format="%Y-%m-%d"):
    try:
        if isinstance(value, str) and len(value) == 4 and value.isdigit():
            return value
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except (ValueError, TypeError):
        return value


print(templates.env.filters)