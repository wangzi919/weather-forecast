"""
Task 2: Database Storage
Reads weather data (via task1_fetch_weather.py) and stores it in
a SQLite3 database "data.db" → table "TemperatureForecasts".

Also includes a verification query that prints all "Central Taiwan" rows.
"""

import sqlite3
import sys
import os

# Reuse the fetch + parse logic from Task 1
sys.path.insert(0, os.path.dirname(__file__))
from task1_fetch_weather import fetch_raw_data, parse_records

DB_PATH    = os.path.join(os.path.dirname(__file__), "data.db")
TABLE_NAME = "TemperatureForecasts"


# ── Database helpers ──────────────────────────────────────────────────────────

def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (or create) the SQLite database and return the connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


def create_table(conn: sqlite3.Connection) -> None:
    """Create the TemperatureForecasts table if it does not already exist."""
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT    NOT NULL,
        dataDate   TEXT    NOT NULL,
        mint       INTEGER NOT NULL,
        maxt       INTEGER NOT NULL
    );
    """
    conn.execute(ddl)
    conn.commit()
    print(f"[DB] Table '{TABLE_NAME}' ready.")


def clear_table(conn: sqlite3.Connection) -> None:
    """Drop all existing rows so we start fresh on each run."""
    conn.execute(f"DELETE FROM {TABLE_NAME}")
    conn.commit()
    print(f"[DB] Existing rows cleared.")


def insert_records(conn: sqlite3.Connection, records: list[dict]) -> None:
    """Bulk-insert all forecast records."""
    sql = f"""
    INSERT INTO {TABLE_NAME} (regionName, dataDate, mint, maxt)
    VALUES (:regionName, :dataDate, :mint, :maxt)
    """
    conn.executemany(sql, records)
    conn.commit()
    print(f"[DB] Inserted {len(records)} rows into '{TABLE_NAME}'.")


# ── Verification ──────────────────────────────────────────────────────────────

def verify_central_taiwan(conn: sqlite3.Connection) -> None:
    """Print all rows where regionName = '中部地區'."""
    print("\n" + "=" * 55)
    print("VERIFICATION — 中部地區 data in data.db:")
    print("=" * 55)
    rows = conn.execute(
        f"SELECT * FROM {TABLE_NAME} WHERE regionName = '中部地區' ORDER BY dataDate"
    ).fetchall()

    if not rows:
        print("  [WARNING] No 'Central Taiwan' rows found!")
    else:
        header = f"{'id':>4}  {'regionName':<20}  {'dataDate':<12}  {'mint':>6}  {'maxt':>6}"
        print(header)
        print("-" * len(header))
        for row in rows:
            print(f"{row['id']:>4}  {row['regionName']:<20}  {row['dataDate']:<12}  "
                  f"{row['mint']:>5}°C  {row['maxt']:>5}°C")
    print("=" * 55 + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Step 1 – fetch & parse
    print("[INFO] Fetching weather data from CWA API …")
    raw_data = fetch_raw_data()
    records  = parse_records(raw_data)

    # Step 2 – store in SQLite
    conn = create_connection()
    create_table(conn)
    clear_table(conn)
    insert_records(conn, records)

    # Step 3 – verify Central Taiwan
    verify_central_taiwan(conn)

    conn.close()
    print(f"[DONE] Database saved to: {DB_PATH}")


if __name__ == "__main__":
    main()
