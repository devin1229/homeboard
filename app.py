from services.database import get_db_connection
from config import UPCOMING_DAYS, UPCOMING_LIMIT
from services.weather import get_weather
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

@app.template_filter("weather_symbol")
def weather_symbol(icon_name):
    symbols = {
        "clear": "☀︎",
        "mostly-clear": "☀︎",
        "partly-cloudy": "☁︎",
        "cloudy": "☁︎",
        "fog": "≋",
        "drizzle": "☂︎",
        "rain": "☂︎",
        "heavy-rain": "☂︎",
        "snow": "❄︎",
        "showers": "☂︎",
        "thunderstorm": "ϟ"
    }

    return symbols.get(icon_name, "☁︎")

@app.template_filter("format_time")
def format_time(time_value):
    if not time_value:
        return ""
    
    hour, minute = map(int, time_value.split(":"))

    period = "AM" if hour < 12 else "PM"

    display_hour = hour % 12

    if display_hour == 0:
        display_hour = 12

    return f"{display_hour}:{minute:02d} {period}"

@app.template_filter("weekday_short")
def weekday_short(date_value):
    event_date = date.fromisoformat(date_value)

    return event_date.strftime("%a").upper()

DATABASE = "homeboard.db"


def initialize_database():
    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS shopping_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            assignee TEXT NOT NULL DEFAULT 'Anyone',
            due_date TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )        
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        event_date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        person TEXT NOT NULL DEFAULT "Anyone",
        location TEXT,
        notes TEXT,
        all_day INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    item_count = connection.execute(
        "SELECT COUNT(*) FROM shopping_items"
    ).fetchone()[0]

    if item_count == 0:
        starter_items = [
            ("Milk",),
            ("Coffee",),
            ("Bananas",),
            ("Chicken",),
            ("Paper towels",),
            ("Dish soap",),
            ("Half-n-Half",)
        ]

        connection.executemany(
            """
            INSERT INTO shopping_items (name)
            VALUES (?)
            """,
            starter_items
        )

    connection.commit()
    connection.close()


@app.route("/")
def dashboard():
    connection = get_db_connection()

    weather = get_weather()

    shopping_items = connection.execute(
        """
        SELECT id, name
        FROM shopping_items
        WHERE completed = 0
        ORDER BY created_at ASC
        """
    ).fetchall()

    today = date.today().isoformat()

    today_events = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE event_date <= ?
        AND end_date >= ?
        ORDER BY
            all_day DESC,
            start_time ASC
        """,
        (today, today)
    ).fetchall()

    tomorrow = date.today() + timedelta(days=1)
    week_end = date.today() + timedelta(days=UPCOMING_DAYS)

    upcoming_events = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE event_date >= ?
            AND event_date <= ?
        ORDER BY
            event_date ASC,
            all_day DESC,
            start_time ASC
        LIMIT ?
        """,
        (
            tomorrow.isoformat(),
            week_end.isoformat(),
            UPCOMING_LIMIT
        )
    ).fetchall()

    next_event = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE
            event_date > ?
            OR (
                event_date = ?
                AND (
                all_day = 1
                OR start_time IS NULL
                OR start_time >= ?
                )
            )
        ORDER BY
            event_date ASC,
            all_day DESC,
            start_time ASC
        LIMIT 1
        """,
        (
            today,
            today,
            datetime.now().strftime("%H:%M")
        )
    ).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        shopping_items=shopping_items,
        today_events=today_events,
        upcoming_events=upcoming_events,
        weather=weather,
        next_event=next_event,
        today=today
    )

@app.route("/api/ambient")
def ambient_api():
    weather = get_weather()

    connection = get_db_connection()

    today = date.today().isoformat()
    current_time = datetime.now().strftime("%H:%M")

    current_event = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE
            event_date <= ?
            AND end_date >= ?
            AND (
                all_day = 1
                OR (
                    start_time IS NOT NULL
                    AND end_time IS NOT NULL
                    AND event_date = ?
                    AND start_time <= ?
                    AND end_time >= ?
                    )
                OR (
                    start_time IS NOT NULL
                    AND end_time IS NOT NULL
                    AND event_date < ?
                    AND end_date >= ?
                    )
                )
        ORDER BY
            event_date ASC,
            start_time ASC
        LIMIT 1
        """,
        (
            today,
            today,
            today,
            current_time,
            current_time,
            today,
            today,
        )
    ).fetchone()

    next_event = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE
            event_date > ?
            OR (
                event_date = ?
                AND (
                    all_day = 1
                    OR start_time IS NULL
                    OR start_time >= ?
                )
            )
        ORDER BY
            event_date ASC,
            all_day DESC,
            start_time ASC
        LIMIT 1
        """,
        (
            today,
            today,
            current_time
        )
    ).fetchone()

    connection.close()

    event_data = None

    current_event_data = None
    
    if next_event:
        event_data = {
            "title": next_event["title"],
            "event_date": next_event["event_date"],
            "start_time": next_event["start_time"],
            "all_day": next_event["all_day"],
        }

    if current_event:
        current_event_data = {
            "title": current_event["title"],
            "event_date": current_event["event_date"],
            "end_date": current_event["end_date"],
            "start_time": current_event["start_time"],
            "end_time": current_event["end_time"],
            "all_day": current_event["all_day"]
        }

    return jsonify({
        "weather": weather,
        "current_event": current_event_data,
        "next_event": event_data,
        "today": today,
    })

@app.route("/api/calendar-dashboard")
def calendar_dashboard_api():
    connection = get_db_connection()

    # today = TEST_DATE
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)

    today_events = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE event_date <= ?
        AND end_date >= ?
        ORDER BY
            all_day DESC,
            start_time ASC
        """,
        (today.isoformat(), today.isoformat())
    ).fetchall()

    upcoming_events = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE event_date >= ?
            AND event_date <= ?
        ORDER BY
            event_date ASC,
            all_day DESC,
            start_time ASC
        LIMIT 3
        """,
        (
            tomorrow.isoformat(),
            week_end.isoformat()
        )
    ).fetchall()

    connection.close()

    def event_to_dict(event):
        return {
            "id": event["id"],
            "title": event["title"],
            "event_date": event["event_date"],
            "end_date": event["end_date"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
            "person": event["person"],
            "location": event["location"],
            "notes": event["notes"],
            "all_day": bool(event["all_day"]),
        }
    
    return jsonify({
        "today_events": [
            event_to_dict(event)
            for event in today_events
        ],
        "upcoming_events": [
            event_to_dict(event)
            for event in upcoming_events
        ],
    })

@app.route("/shopping")
def shopping():
    connection = get_db_connection()

    shopping_items = connection.execute(
        """
        SELECT id, name, completed
        FROM shopping_items
        ORDER BY completed ASC, created_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "shopping.html",
        shopping_items=shopping_items
    )

@app.route("/shopping/add", methods=["POST"])
def add_shopping_item():
    item_name = request.form.get("item_name", "").strip()

    if item_name:
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO shopping_items (name)
            VALUES (?)
            """,
            (item_name,)
        )

        connection.commit()
        connection.close()

    return redirect(url_for("shopping"))

@app.route("/shopping/toggle/<int:item_id>", methods=["POST"])
def toggle_shopping_item(item_id):
    connection = get_db_connection()

    connection.execute(
        """
        UPDATE shopping_items
        SET completed =
            CASE
                WHEN completed = 0 THEN 1
                ELSE 0
            END
        WHERE id = ?
        """,
        (item_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("shopping"))

@app.route("/api/shopping")
def shopping_api():
    connection = get_db_connection()

    shopping_items = connection.execute(
        """
        SELECT id, name
        FROM shopping_items
        WHERE completed = 0
        ORDER BY created_at ASC
        """
    ).fetchall()

    connection.close()

    return jsonify([
        {
            "id": item["id"],
            "name": item["name"]
        }
        for item in shopping_items
    ])

@app.route("/shopping/clear-completed", methods=["POST"])
def clear_completed_shopping():
    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM shopping_items
        WHERE completed = 1
        """
    )

    connection.commit()
    connection.close()

    return redirect(url_for("shopping"))    

@app.route("/tasks")
def tasks():
    connection = get_db_connection()

    task_items = connection.execute(
        """
        SELECT id, name, assignee, due_date, completed
        FROM tasks
        ORDER BY completed ASC,
            CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
            due_date ASC,
            created_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "tasks.html",
        task_items=task_items
    )

@app.route("/tasks/add", methods=["POST"])
def add_task():
    task_name = request.form.get("task_name", "").strip()
    assignee = request.form.get("assignee", "Anyone").strip()
    due_date = request.form.get("due_date", "").strip()

    if not due_date:
        due_date = None

    if task_name:
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO tasks (
                name,
                assignee,
                due_date
            )
            VALUES (?, ?, ?)
            """,
            (
                task_name,
                assignee,
                due_date
            )
        )

        connection.commit()
        connection.close()

    return redirect(url_for("tasks"))

@app.route("/tasks/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    connection = get_db_connection()

    connection.execute(
        """
        UPDATE tasks
        SET completed =
            CASE
                WHEN completed = 0 THEN 1
                ELSE 0
            END
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("tasks"))

@app.route("/tasks/clear-completed", methods=["POST"])
def clear_completed_tasks():
    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM tasks
        WHERE completed = 1
        """
    )

    connection.commit()
    connection.close()

    return redirect(url_for("tasks"))

@app.route("/api/tasks")
def tasks_api():
    connection = get_db_connection()

    task_items = connection.execute(
        """
        SELECT id, name, assignee, due_date
        FROM tasks
        WHERE completed = 0
        ORDER BY
            CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
            due_date ASC,
            created_at DESC
        """
    ).fetchall()
    
    today = date.today()

    status_order = {
        "overdue": 0,
        "today": 1,
        "future": 2,
        "none": 3
    }

    tasks = []

    for task in task_items:
        task = dict(task)

        if task["due_date"]:
            due = date.fromisoformat(task["due_date"])

            if due < today:
                task["status"] = "overdue"
            elif due == today:
                task["status"] = "today"
            else:
                task["status"] = "future"
        else:
            task["status"] = "none"

        tasks.append(task)

    tasks.sort(
        key=lambda t: (
            status_order[t["status"]],
            t["due_date"] or "9999-12-31"
        )
    )

    connection.close()
    
    return jsonify([
        {
            "id": task["id"],
            "name": task["name"],
            "assignee": task["assignee"],
            "due_date": task["due_date"],
            "status": task["status"]
        }
        for task in tasks
    ])

@app.route("/calendar")
def calendar():
    connection = get_db_connection()

    today = date.today().isoformat()

    event_items = connection.execute(
        """
        SELECT
            id,
            title,
            event_date,
            end_date,
            start_time,
            end_time,
            person,
            location,
            notes,
            all_day
        FROM events
        WHERE end_date >= ?
        ORDER BY
            event_date ASC,
            all_day DESC,
            start_time ASC
        """,
        (today,)
    ).fetchall()

    edit_event = None
    
    edit_id = request.args.get("edit", type=int)

    if edit_id:
        edit_event = connection.execute(
            """
            SELECT
                id,
                title,
                event_date,
                end_date,
                start_time,
                end_time,
                person,
                location,
                notes,
                all_day
            FROM events
            WHERE id = ?
            """,
            (edit_id,)
        ).fetchone()

    connection.close()

    return render_template(
        "calendar.html",
        event_items=event_items,
        edit_event=edit_event
    )

@app.route("/calendar/add", methods=["POST"])
def add_event():
    title = request.form.get("title", "").strip()
    event_date = request.form.get("event_date", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_date = request.form.get("end_date", "").strip()
    end_time = request.form.get("end_time", "").strip()
    person = request.form.get("person", "Anyone").strip()
    location = request.form.get("location", "").strip()
    notes = request.form.get("notes", "").strip()

    all_day = 1 if request.form.get("all_day") else 0

    if all_day:
        start_time = None
        end_time = None

    if not start_time:
        start_time = None

    if not end_time:
        end_time = None

    if not end_date:
        end_date = event_date

    if not location:
        location = None

    if not notes:
        notes = None

    if title and event_date:
        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO events (
                title,
                event_date,
                end_date,
                start_time,
                end_time,
                person,
                location,
                notes,
                all_day
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                event_date,
                end_date,
                start_time,
                end_time,
                person,
                location,
                notes,
                all_day
            )
        )

        connection.commit()
        connection.close()

    return redirect(url_for("calendar"))

@app.route("/calendar/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    connection = get_db_connection()

    connection.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )
    
    connection.commit()
    connection.close()

    return redirect(url_for("calendar"))

@app.route("/calendar/update/<int:event_id>", methods=["POST"])
def update_event(event_id):
    title = request.form.get("title", "").strip()
    event_date = request.form.get("event_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    person = request.form.get("person", "Anyone").strip()
    location = request.form.get("location", "").strip()
    notes = request.form.get("notes", "").strip()

    all_day = 1 if request.form.get("all_day") else 0

    if all_day:
        start_time = None
        end_time = None

    if not start_time:
        start_time = None

    if not end_time:
        end_time = None

    if not end_date:
        end_date = event_date

    if not location:
        location = None

    if not notes:
        notes = None

    if title and event_date:
        connection = get_db_connection()

        connection.execute(
            """
            UPDATE events
            SET
                title = ?,
                event_date = ?,
                end_date = ?,
                start_time = ?,
                end_time = ?,
                person = ?,
                location = ?,
                notes = ?,
                all_day = ?
            WHERE id = ?
            """,
            (
                title,
                event_date,
                end_date,
                start_time,
                end_time,
                person,
                location,
                notes,
                all_day,
                event_id
            )
        )

        connection.commit()
        connection.close()

    return redirect(url_for("calendar"))

if __name__ == "__main__":
    initialize_database()

    app.run(host="0.0.0.0", port=5001, debug=False)
