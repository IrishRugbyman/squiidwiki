# SquiidWiki

A web application built with FastAPI backend and TypeScript frontend.

## Project Structure

- `backend/` - Python FastAPI backend
- `frontend/` - Frontend files
  - `src/ts/` - TypeScript source files
    - `app.ts` - Main application entry point
    - `modules/` - Feature modules
      - `ui.ts` - UI controls (sidebar, dark mode, etc.)
      - `forms.ts` - Form handling, validation, and submission
      - `notifications.ts` - Notification system
      - `dataTables.ts` - Data table functionality 
      - `search.ts` - Search functionality
    - `utils/` - Utility functions and helpers
      - `api.ts` - API communication utilities
    - `types/` - TypeScript type definitions
  - `static/` - Compiled JS, CSS, and other static assets
  - `templates/` - HTML templates

## Development Setup

### Backend

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend server:
```bash
uvicorn backend.server:app --reload
```

### Frontend

1. Make sure Node.js is installed (https://nodejs.org/)

2. Install Node.js dependencies:
```bash
npm install
```

3. Use the PowerShell scripts to run the build:

For development with watch mode (automatically recompiles on changes):
```powershell
.\dev.ps1
```

For production build:
```powershell
.\build.ps1
```

Both scripts will:
- Check if Node.js is in your PATH and add it if needed
- Create necessary directories
- Run the appropriate npm command

## TypeScript Architecture

The TypeScript codebase follows a modular architecture with these main components:

1. **Modules**: Feature-specific functionality organized into separate files
2. **Utils**: Shared utility functions
3. **Types**: TypeScript interface and type definitions

### Key Features

- **Form Validation**: Robust form validation with custom rules and error messages
- **Notifications**: Flexible notification system for success/error messages
- **Data Tables**: Sortable, filterable, and paginated tables
- **Search**: Advanced search functionality with highlighting
- **API Utilities**: Typed API communication with error handling

## Using the TypeScript API Utilities

The API utilities are exposed globally and can be used in HTML templates like this:

```javascript
// Example: Fetching members from the API
async function loadMembers() {
  // Generic type for response data
  const response = await api.get<Member[]>('/api/members');
  if (response.success) {
    // Process the data - fully typed!
    const members = response.data;
    console.log(members[0].name);
  } else {
    // Handle the error
    console.error(response.error);
  }
}

// Example: Posting data with type safety
async function createMember(memberData: Partial<Member>) {
  const response = await api.post<Member, Partial<Member>>('/api/members', memberData);
  if (response.success) {
    showNotification('Member created successfully!', 'success');
  }
}
```

## Troubleshooting

If you encounter issues with the TypeScript setup:

1. **Node.js not found**: Make sure Node.js is installed and run the build script with administrator privileges to add it to PATH permanently

2. **Type errors**: Update tsconfig.json if you add new module paths or change the directory structure

3. **Build errors**: Check the console output for specific errors; they're usually related to missing imports or type issues

## Project Structure

The project follows a modern structure with clear separation of concerns:

```
squiidwiki/
├── backend/              # Backend Python code
│   ├── auth/             # Authentication & authorization
│   ├── config/           # Configuration
│   ├── database/         # Database models and utilities
│   ├── errors/           # Error handling
│   ├── home/             # Home page routes
│   ├── members/          # Members-related routes
│   ├── sets/             # Sets-related routes
│   ├── alliances/        # Alliances-related routes
│   ├── events/           # Events-related routes
│   └── calendar/         # Calendar-related routes
├── frontend/             # Frontend assets
│   └── static/           # Static files (CSS, JS, images)
├── main.py               # Application entry point
├── init_test_db.py       # Script to initialize test database
├── backup_db.py          # Script to backup production database
└── squiidvault.db        # SQLite database file
```

## Configuration

The application uses a centralized configuration system in `backend/config/config.py`. Key settings can be controlled through environment variables:

- `APP_ENV`: The application environment (development, testing, production)
- `TEST_MODE`: Set to "1" to use the test database
- `DEBUG`: Set to "1" to enable debug mode
- `PORT`: Server port (default: 8002)
- `JWT_SECRET_KEY`: Secret key for JWT tokens

## Running the Application

### Development Mode

```bash
# Run with default settings
python main.py

# Run in test mode (uses a separate test database)
$env:TEST_MODE=1; python main.py
```

### Production Mode

```bash
$env:APP_ENV=production; python main.py
```

## Database Management

### Test Database

The application supports a separate test database to avoid affecting production data:

```bash
# Initialize the test database
python init_test_db.py

# Run the app with test database
$env:TEST_MODE=1; python main.py
```

### Database Backup

```bash
# Backup the production database
python backup_db.py
```

## Error Handling

The application uses a comprehensive error handling system that provides:

- Consistent error responses for both API and HTML endpoints
- Detailed error information in development mode
- Structured error logging

## API Endpoints

The application provides two ways to access data:

1. HTML endpoints for browser access
2. JSON API endpoints under `/api` for programmatic access

## Authentication

The application uses JWT-based authentication:

- Login at `/auth/login`
- Development bypass at `/auth/bypass` (only available in development mode)

## Development

For development, you can use auth bypass to skip authentication:

1. Visit `/auth/bypass` to set the bypass cookie
2. This will automatically log you in as an admin in development mode 