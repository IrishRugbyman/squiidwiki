import os

from backend.server import app
from backend.database.database import init_db, get_db
import uvicorn


def add_test_data():
    """
    Inserts test data into the database for development or testing purposes.
    This version adds members with every type of status and a variety of date fields,
    as well as sample events (shootings, murders, assists).
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        # --- Example: Insert additional sets ---
        test_sets = [
            ("Test Gang A", "A sample gang for testing", "active"),
            ("Test Gang B", "Another sample gang", "active"),
            ("Test Gang C", "Yet another sample gang", "extinct"),
        ]
        for name, desc, set_type in test_sets:
            cursor.execute('''
                INSERT OR IGNORE INTO sets (name, description, type)
                VALUES (?, ?, ?)
            ''', (name, desc, set_type))

        # Retrieve IDs for the test sets
        def get_set_id(name):
            cursor.execute('SELECT id FROM sets WHERE name = ?', (name,))
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Set '{name}' not found after insertion.")
            return result['id']  # Access by column name

        test_gang_a_id = get_set_id("Test Gang A")
        test_gang_b_id = get_set_id("Test Gang B")
        test_gang_c_id = get_set_id("Test Gang C")

        # --- Example: Insert test members with various statuses and date values ---
        test_members = [
            # Existing members
            (
                "Alice", "Alive member with no extra date info", "alive", test_gang_a_id, None, None, None,
                None
            ),
            (
                "Bob", "Locked up member with a precise release date", "locked_up", test_gang_a_id, "2023-01-15", None,
                None, None
            ),
            (
                "Charlie", "Locked up member with an approximate release year", "locked_up", test_gang_b_id, None,
                "2023", None, None
            ),
            (
                "Diana", "Dead member with a precise death date", "dead", test_gang_b_id, None, None, "2022-10-31",
                None
            ),
            (
                "Evan", "Dead member with an approximate death year", "dead", test_gang_a_id, None, None, None,
                "2021"
            ),
            (
                "Frank", "Locked up member serving life in prison", "locked_up", test_gang_a_id, None, "life", None,
                None
            ),
            (
                "Grace", "Member with dead status and no dates", "dead", test_gang_b_id, None, None, None,
                "unknown"
            ),

            # Additional alive members for testing
            (
                "Henry", "A new alive member affiliated with Test Gang A", "alive", test_gang_a_id, None, None, None,
                None
            ),
            (
                "Ivy", "A new alive member affiliated with Test Gang B", "alive", test_gang_b_id, None, None, None,
                None
            ),
            (
                "Jack", "A new alive member affiliated with Test Gang C", "alive", test_gang_c_id, None, None, None,
                None
            ),
            (
                "Kara", "A new alive member with no gang affiliation", "alive", 1, None, None, None,
                None
            ),
            (
                "Liam", "A new alive member with a detailed description", "alive", test_gang_a_id, None, None, None,
                None
            ),
            (
                "Mia", "A new alive member who recently joined Test Gang B", "alive", test_gang_b_id, None, None, None,
                None
            ),
        ]

        # Insert each test member with all date fields.
        for member in test_members:
            cursor.execute('''
                INSERT INTO members (name, description, status, set_id, release_date, release_date_approx, death_date, death_date_approx)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', member)

        # Helper function to retrieve member IDs safely
        def get_member_id(name):
            cursor.execute('SELECT id FROM members WHERE name = ?', (name,))
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Member '{name}' not found after insertion.")
            return result['id']  # Access by column name

        # Retrieve member IDs for later use in events
        alice_id = get_member_id("Alice")
        bob_id = get_member_id("Bob")
        diana_id = get_member_id("Diana")
        evan_id = get_member_id("Evan")
        henry_id = get_member_id("Henry")
        ivy_id = get_member_id("Ivy")
        jack_id = get_member_id("Jack")

        # --- Example: Insert test alliances ---
        cursor.execute('''
            INSERT OR IGNORE INTO alliances (name, description, status)
            VALUES (?, ?, 'active')
        ''', ("Test Alliance", "A sample alliance for testing"))

        # Retrieve alliance ID safely
        def get_alliance_id(name):
            cursor.execute('SELECT id FROM alliances WHERE name = ?', (name,))
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Alliance '{name}' not found after insertion.")
            return result['id']  # Access by column name

        alliance_id = get_alliance_id("Test Alliance")

        # Map one of the test gangs to the alliance
        cursor.execute('''
            INSERT OR IGNORE INTO alliance_sets_map (alliance_id, set_id)
            VALUES (?, ?)
        ''', (alliance_id, test_gang_a_id))

        # --- Example: Insert test events (shootings, murders, assists) ---
        test_events = [
            # Shooting event: Alice shoots Diana on an exact date
            ("shooting", alice_id, diana_id, "2021-03-15", None),
            # Murder event: Bob kills Evan on an exact date
            ("murder", bob_id, evan_id, "2023-04-10", None),
            # Assist event: Alice assists Bob in shooting Diana with an approximate date (year)
            ("assist", alice_id, diana_id, None, "2023"),
            # New event: Henry shoots Ivy on an exact date
            ("shooting", henry_id, ivy_id, "2023-05-20", None),
        ]

        # Insert each test event
        for event_type, shooter_id, victim_id, date_exact, date_approx in test_events:
            if event_type == "murder":
                cursor.execute('''
                    INSERT INTO murders (shooter_id, victim_id, date, date_approx)
                    VALUES (?, ?, ?, ?)
                ''', (shooter_id, victim_id, date_exact, date_approx))
                # Update victim's status and death_date
                update_query = '''
                    UPDATE members
                    SET status = 'dead',
                        death_date = CASE
                            WHEN death_date IS NULL OR death_date > ? THEN ?
                            ELSE death_date
                        END,
                        death_date_approx = ?
                    WHERE id = ?
                '''
                cursor.execute(update_query,
                               (date_exact or date_approx, date_exact or date_approx, date_approx, victim_id))
            else:
                cursor.execute(f'''
                    INSERT INTO {event_type}s (shooter_id, victim_id, date, date_approx)
                    VALUES (?, ?, ?, ?)
                ''', (shooter_id, victim_id, date_exact, date_approx))

        # Commit test data insertion
        conn.commit()
        print("Test data added successfully.")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to add test data: {str(e)}")
    finally:
        conn.close()


drop_existing = True
init_db(drop_existing=drop_existing)
if drop_existing:
    add_test_data()
os.system("tree /F /A > project_tree.txt")
print("Project tree saved to project_tree.txt")
# os.system("pip freeze > requirements.txt")
# print("Requirements saved to requirements.txt")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
