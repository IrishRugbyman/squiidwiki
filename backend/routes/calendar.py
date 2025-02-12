from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timedelta

from starlette.responses import HTMLResponse

from backend.database.database import get_db
from backend.config.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/events", response_class=HTMLResponse)
def list_events(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    events = []
    try:
        # Query for releases
        cursor.execute("""
            SELECT id, name, release_date
            FROM members
            WHERE release_date IS NOT NULL
        """)
        for row in cursor.fetchall():
            if row["release_date"]:
                events.append({
                    "title": f"{row['name']}",
                    "date": row["release_date"],
                    "color": "green",
                    "eventType": "release",
                    "memberId": row["id"]
                })

        # Query for murders
        cursor.execute("""
            SELECT mur.date, shooter.name AS shooter_name, victim.name AS victim_name,
                   mur.shooter_id, mur.victim_id
            FROM murders mur
            JOIN members shooter ON mur.shooter_id = shooter.id
            JOIN members victim ON mur.victim_id = victim.id
        """)
        for row in cursor.fetchall():
            if row["date"]:
                events.append({
                    "title": f"{row['shooter_name']} killed {row['victim_name']}",
                    "date": row["date"],
                    "color": "darkred",
                    "eventType": "murder",
                    "shooterId": row["shooter_id"],
                    "victimId": row["victim_id"]
                })

        # Query for deaths (non-murder)
        cursor.execute("""
            SELECT id, name, death_date
            FROM members
            WHERE death_date IS NOT NULL
            AND id NOT IN (SELECT victim_id FROM murders)
        """)
        for row in cursor.fetchall():
            if row["death_date"]:
                events.append({
                    "title": f"{row['name']}",
                    "date": row["death_date"],
                    "color": "red",
                    "eventType": "death",
                    "memberId": row["id"]
                })

        # Query for shootings
        cursor.execute("""
            SELECT sh.date, shooter.name AS shooter_name, victim.name AS victim_name,
                   sh.shooter_id, sh.victim_id
            FROM shootings sh
            JOIN members shooter ON sh.shooter_id = shooter.id
            JOIN members victim ON sh.victim_id = victim.id
        """)
        for row in cursor.fetchall():
            if row["date"]:
                events.append({
                    "title": f"{row['shooter_name']} shot {row['victim_name']}",
                    "date": row["date"],
                    "color": "orange",
                    "eventType": "shooting",
                    "shooterId": row["shooter_id"],
                    "victimId": row["victim_id"]
                })

        # Categorize events into "upcoming" and "latest past"
        today = datetime.today().date()
        upcoming_events = [
            e for e in events
            if e["date"] and datetime.strptime(e["date"], "%Y-%m-%d").date() > today
        ]
        latest_past_events = [
            e for e in events
            if e["date"] and datetime.strptime(e["date"], "%Y-%m-%d").date() <= today
        ]

        # Sort events by date
        upcoming_events.sort(key=lambda x: x["date"])
        latest_past_events.sort(key=lambda x: x["date"], reverse=True)

    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse(
        "calendar/calendar_events.html",
        {
            "request": request,
            "upcoming_events": upcoming_events[:10],  # Show top 10 upcoming events
            "latest_past_events": latest_past_events[:10]  # Show top 10 latest past events
        }
    )

@router.get("/", response_class=HTMLResponse)
def show_calendar(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    events = []

    try:
        # Query for releases
        cursor.execute("""
            SELECT id, name, release_date
            FROM members
            WHERE release_date IS NOT NULL
        """)
        for row in cursor.fetchall():
            events.append({
                "title": f"{row['name']}",
                "date": row["release_date"],
                "color": "green",
                "extendedProps": {
                    "eventType": "release",
                    "memberId": row["id"]
                }
            })

        # Query for murders
        cursor.execute("""
            SELECT mur.date, shooter.name AS shooter_name, victim.name AS victim_name,
                   mur.shooter_id, mur.victim_id
            FROM murders mur
            JOIN members shooter ON mur.shooter_id = shooter.id
            JOIN members victim ON mur.victim_id = victim.id
        """)
        for row in cursor.fetchall():
            events.append({
                "title": f"{row['shooter_name']} killed {row['victim_name']}",
                "date": row["date"],
                "color": "darkred",
                "extendedProps": {
                    "eventType": "murder",
                    "shooterId": row["shooter_id"],
                    "victimId": row["victim_id"]
                }
            })

        # Query for deaths (non-murder)
        cursor.execute("""
            SELECT id, name, death_date
            FROM members
            WHERE death_date IS NOT NULL
              AND id NOT IN (SELECT victim_id FROM murders)
        """)
        for row in cursor.fetchall():
            events.append({
                "title": f"{row['name']}",
                "date": row["death_date"],
                "color": "red",
                "extendedProps": {
                    "eventType": "death",
                    "memberId": row["id"]
                }
            })

            # Add death anniversaries
            try:
                death_year = int(row["death_date"].split("-")[0])
                for year in range(death_year + 1, death_year + 11):  # Next 10 years
                    events.append({
                        "title": f"{row['name']}",
                        "date": f"{year}-{row['death_date'][5:]}",
                        "color": "black",
                        "extendedProps": {
                            "eventType": "anniversary",
                            "memberId": row["id"]
                        }
                    })
            except Exception:
                logger.warning(f"Invalid death date format for member {row['id']}")

        # Query for shootings
        cursor.execute("""
            SELECT sh.date, shooter.name AS shooter_name, victim.name AS victim_name,
                   sh.shooter_id, sh.victim_id
            FROM shootings sh
            JOIN members shooter ON sh.shooter_id = shooter.id
            JOIN members victim ON sh.victim_id = victim.id
        """)
        for row in cursor.fetchall():
            events.append({
                "title": f"{row['shooter_name']} shot {row['victim_name']}",
                "date": row["date"],
                "color": "orange",
                "extendedProps": {
                    "eventType": "shooting",
                    "shooterId": row["shooter_id"],
                    "victimId": row["victim_id"]
                }
            })

    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        conn.close()

    return templates.TemplateResponse("calendar/calendar.html", {"request": request, "events": events})