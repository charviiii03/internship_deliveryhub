"""
One-off migration script: adds tracking_number column to shipments.
Run this INSIDE the app-manager container so it uses the exact same
DB connection settings as the running app (host, user, password, db name).

Usage:
    docker compose exec app-manager python migrate_add_tracking_number.py
"""

from db import get_db_connection

conn = get_db_connection()
if not conn:
    print("FAILED: could not get a DB connection. Check db.py / .env settings.")
    raise SystemExit(1)

cur = conn.cursor()

try:
    cur.execute("SHOW COLUMNS FROM shipments LIKE 'tracking_number';")
    exists = cur.fetchone()
    if exists:
        print("Column tracking_number already exists. Nothing to do.")
    else:
        cur.execute("ALTER TABLE shipments ADD COLUMN tracking_number VARCHAR(100) NULL;")
        conn.commit()
        print("SUCCESS: tracking_number column added.")

    cur.execute("DESCRIBE shipments;")
    print("\nCurrent shipments columns:")
    for row in cur.fetchall():
        print(" -", row[0])

except Exception as e:
    print("ERROR:", e)

finally:
    cur.close()
    conn.close()