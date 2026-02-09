# SquiidWiki - Quick Start Guide

## Installation Complete! ✓

Your Detroit gang research database is now running at **http://127.0.0.1:8000**

## First Steps

1. **Login**
   - Navigate to: http://127.0.0.1:8000
   - You'll be redirected to the login page
   - Default password: `admin` (change this in `.env`)

2. **Explore the Dashboard**
   - View summary statistics
   - See recent incidents
   - Navigate using the sidebar

## Key Features

### Navigation
- **Dashboard** - Summary stats and recent activity
- **Members** - Individual gang members
- **Sets** - Gang sets/crews
- **Alliances** - Larger organizations
- **Incidents** - Shootings, beatings, etc.
- **Sources** - Research citations
- **Network Graph** - Visual relationship map

### Sample Data Included
The database has been seeded with example data:
- 1 alliance (Eastside Alliance)
- 3 sets (7 Mile Bloods, 6 Mile Chedda Grove, 8 Mile Crips)
- 4 members with various affiliations
- 2 incidents with participants
- 1 source citation

### Using the App

#### Viewing Data
- Click any entity in a list to view detailed information
- Use search bars (HTMX-powered) to filter results in real-time
- Click linked entities to navigate between related records

#### Network Graph
- View visual relationships between sets, alliances, and members
- Click nodes to navigate to detail pages
- Use toggles to show/hide members and alliances
- Green lines = allies, Red dashed lines = enemies

#### API Access
- Full REST API available at: http://127.0.0.1:8000/docs
- Interactive API documentation via Swagger UI
- All CRUD operations + special endpoints for relationships

## Next Steps

### Customization
1. **Change Password**
   - Edit `.env` file
   - Update `ADMIN_PASSWORD=your-secure-password`
   - Restart the app

2. **Add Real Data**
   - Use the web interface (forms to be implemented)
   - Use the API directly
   - Import via custom scripts

### Development
```bash
# Stop the server (CTRL+C in terminal)

# Apply new migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "Description"

# Clear database (start fresh)
# Delete squiidwiki.db file, then run:
alembic upgrade head
python seed.py
```

## Project Structure
```
squiidwiki/
├── app/
│   ├── models/      # Database models
│   ├── schemas/     # API schemas
│   ├── crud/        # Database operations
│   ├── routes/      # API & page routes
│   ├── templates/   # HTML pages
│   └── static/      # CSS & JS
├── alembic/         # Migrations
├── squiidwiki.db    # SQLite database
└── run.py           # Start script
```

## Features Implemented

✓ Complete data model (Members, Sets, Alliances, Incidents, Sources)
✓ FuzzyDate system for flexible date precision
✓ Bilateral ally/enemy relationships
✓ Computed statistics (kills, assists, shootings)
✓ Dark-themed professional UI
✓ HTMX-powered search and filtering
✓ Full REST API with documentation
✓ Network graph visualization
✓ Source citation system
✓ Authentication system

## Features Not Yet Implemented

- Create/Edit forms (currently API-only)
- Additional validation rules
- Data export functionality
- Advanced filtering options
- Image upload for members
- Multi-user support
- Audit logging

## Troubleshooting

**Port already in use:**
```bash
# Kill existing server, then restart
python run.py
```

**Database errors:**
```bash
# Reset database
del squiidwiki.db
alembic upgrade head
python seed.py
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Security Notes

⚠️ **Important**: This is a development setup. For production use:
- Change SECRET_KEY in `.env`
- Use a strong ADMIN_PASSWORD
- Enable HTTPS
- Use PostgreSQL instead of SQLite
- Implement proper user management
- Add rate limiting
- Review all security best practices

## Support

For issues or questions:
- Check README.md for detailed documentation
- Review API docs at /docs
- Check the plan file for architecture details

---

**Enjoy researching with SquiidWiki!**
