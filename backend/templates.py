from datetime import date, datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "templates"


def format_special_date(date_value, precision=None):
    """Format a date based on its precision and value for template rendering."""
    try:
        if not date_value:
            return Markup('<span class="date-unknown">Unknown</span>')

        if isinstance(date_value, (date, datetime)):
            formatted_date = date_value.strftime("%d/%m/%Y")
            return Markup(f'<span class="date-exact">{formatted_date}</span>')

        if precision == "exact":
            try:
                d = datetime.strptime(date_value, "%Y-%m-%d")
                return Markup(f'<span class="date-exact">{d.strftime("%d/%m/%Y")}</span>')
            except ValueError:
                return Markup('<span class="date-unknown">Unknown</span>')

        elif precision == "year":
            if date_value.isdigit() and len(date_value) == 4:
                return Markup(f'<span class="date-year">{date_value}</span> (approx)')
            return Markup('<span class="date-unknown">Unknown</span>')

        elif ":" in date_value:
            parts = date_value.split(":", 1)
            if len(parts) == 2:
                prefix, value = parts
                if prefix == "circa" and value.isdigit() and len(value) == 4:
                    return Markup(f'<span class="date-year">{value}</span> (approx)')
            return Markup('<span class="date-unknown">Unknown</span>')

        else:
            try:
                d = datetime.strptime(date_value, "%Y-%m-%d")
                return Markup(f'<span class="date-exact">{d.strftime("%d/%m/%Y")}</span>')
            except ValueError:
                if date_value.isdigit() and len(date_value) == 4:
                    return Markup(f'<span class="date-year">{date_value}</span>')
                return Markup(f'<span class="date-text">{date_value}</span>')

    except Exception:
        return Markup('<span class="date-unknown">Unknown</span>')


def format_datetime(value, format="%Y-%m-%d"):
    try:
        if isinstance(value, str) and len(value) == 4 and value.isdigit():
            return value
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except (ValueError, TypeError):
        return value


templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.filters["format_special_date"] = format_special_date
templates.env.filters["format_datetime"] = format_datetime
templates.env.globals["current_year"] = datetime.now().year
templates.env.globals["year"] = datetime.now().year
