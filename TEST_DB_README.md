# Test Database Setup

This document explains how to use the test database setup to safely test your application without risking your production data.

## How It Works

The application now supports a test mode that uses a separate database file (`squiidvault_test.db`) instead of your production database (`squiidvault.db`). This allows you to freely experiment with and test your application without any risk to your real data.

## Using Test Mode

### 1. Initialize the Test Database

Run the following command to create and initialize the test database with sample data:

```bash
python init_test_db.py
```

This script will:
- Create a new `squiidvault_test.db` file (or overwrite it if it exists)
- Apply all database schema migrations
- Populate it with test data from the `add_test_data()` function

### 2. Run the Application in Test Mode

To run your application using the test database, set the `TEST_MODE` environment variable to `1`:

**On Windows (PowerShell):**
```powershell
$env:TEST_MODE=1; python main.py
```

**On Windows (Command Prompt):**
```cmd
set TEST_MODE=1
python main.py
```

**On Linux/macOS:**
```bash
TEST_MODE=1 python main.py
```

The application will start and display a message confirming it's using the test database.

### 3. Reset Test Data

If you want to reset the test database to its initial state with fresh test data, simply run the initialization script again:

```bash
python init_test_db.py
```

## Test Database vs. Production Database

- Test Database: `squiidvault_test.db` (used when `TEST_MODE=1`)
- Production Database: `squiidvault.db` (used by default)

The test database is completely separate from your production database, so any changes you make in test mode will not affect your real data.

## Best Practices

1. **Always use test mode for development and testing**:
   ```
   TEST_MODE=1 python main.py
   ```

2. **Keep regular backups of your production database**:
   ```
   copy squiidvault.db squiidvault_backup_YYYY_MM_DD.db
   ```

3. **Reset the test database when needed**:
   ```
   python init_test_db.py
   ```

4. **Verify which database you're connected to** by checking the startup message in the console, which will display which database file is being used. 