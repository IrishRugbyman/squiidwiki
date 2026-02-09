# SquiidWiki

A comprehensive Detroit gang research database built with FastAPI, SQLAlchemy, and modern web technologies. Designed for organized crime research with a focus on data integrity, relational tracking, and visual network analysis.

![SquiidWiki Dashboard](docs/dashboard-screenshot.png)

## Features

- **Comprehensive Data Model**: Track members, sets, alliances, incidents, and sources with full relationship mapping
- **FuzzyDate System**: Handle dates with varying precision (year-only, year-month, or full date)
- **Network Visualization**: Interactive graph showing relationships between sets, alliances, and members
- **Dark-Themed UI**: Professional dark interface optimized for extended research sessions
- **HTMX-Powered**: Dynamic search and filtering without JavaScript complexity
- **RESTful API**: Full JSON API for programmatic access
- **Source Citations**: Link all data to sources for research credibility

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Pydantic v2
- **Frontend**: Jinja2 + HTMX + Tailwind CSS
- **Database**: SQLite (easily switchable to PostgreSQL)
- **Visualization**: vis.js for network graphs
- **Auth**: Simple password-based authentication

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd squiidwiki
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and set your SECRET_KEY and ADMIN_PASSWORD
```

4. Initialize database:
```bash
alembic upgrade head
```

5. (Optional) Seed with sample data:
```bash
python seed.py
```

6. Run the application:
```bash
python run.py
```

7. Access the application:
```
http://127.0.0.1:8000
```

Default password: See `.env` file (default: `admin`)

## Data Model

### Entities

- **Members**: Individuals with names, nicknames, status, affiliations, dates, and biographical information
- **Sets**: Gang sets with names, territories, colors, members, allies, and enemies
- **Alliances**: Larger organizations containing multiple sets
- **Incidents**: Events (shootings, stabbings, beatings) with participants in different roles
- **Sources**: Citations for all data (news articles, court documents, social media, etc.)

### Key Features

- **Bilateral Relationships**: Ally/enemy relationships are symmetric and mutually exclusive
- **Computed Stats**: Kills, assists, shootings automatically calculated from incident data
- **Flexible Dates**: FuzzyDate system handles incomplete date information
- **Validation**: Cross-field validation ensures data integrity

## Project Structure

```
squiidwiki/
├── app/
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── crud/            # Database operations
│   ├── routes/          # API and page routes
│   ├── templates/       # Jinja2 HTML templates
│   ├── static/          # CSS and JavaScript
│   ├── config.py        # Application settings
│   ├── database.py      # Database setup
│   ├── auth.py          # Authentication
│   └── main.py          # FastAPI app
├── alembic/             # Database migrations
├── requirements.txt     # Python dependencies
├── seed.py              # Sample data script
└── run.py               # Application entry point
```

## API Documentation

Once running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Key Endpoints

- `GET /api/members` - List members
- `GET /api/sets` - List sets
- `GET /api/alliances` - List alliances
- `GET /api/incidents` - List incidents
- `GET /api/graph` - Network graph data
- `POST /api/sets/{id}/allies/{other_id}` - Add ally relationship
- `POST /api/sets/{id}/enemies/{other_id}` - Add enemy relationship

## Development

### Adding a New Entity

1. Create model in `app/models/`
2. Create schemas in `app/schemas/`
3. Create CRUD operations in `app/crud/`
4. Create API routes in `app/routes/`
5. Create templates in `app/templates/`
6. Generate migration: `alembic revision --autogenerate -m "description"`
7. Apply migration: `alembic upgrade head`

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Security Considerations

- Change `SECRET_KEY` and `ADMIN_PASSWORD` in production
- Use HTTPS in production
- Consider implementing proper user management for multi-user access
- Regularly backup the database
- Review and sanitize all inputs

## Research Ethics

This tool is designed for legitimate research purposes including:
- Academic research on organized crime
- Journalism and investigative reporting
- Law enforcement intelligence gathering
- Sociological studies

**Important**: Always verify information through multiple sources and respect privacy laws.

## License

[Add your license here]

## Contributing

[Add contribution guidelines]

## Contact

[Add contact information]

---

**Disclaimer**: This software is for research and educational purposes only. Users are responsible for ensuring their use complies with all applicable laws and regulations.
