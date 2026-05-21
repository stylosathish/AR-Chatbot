import sqlite3
import os

# =========================
# SAFE DB LOCATION (FIXED)
# =========================

# Preferred: user profile folder (SAFE for Windows permissions)
try:
    DB_PATH = os.path.join(os.environ["USERPROFILE"], "ar_history.db")
except Exception:
    DB_PATH = "ar_history.db"


# =========================
# CREATE TABLE
# =========================

def create_table():

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            correspondence TEXT,
            bucket TEXT,
            a1 TEXT,
            created_at TEXT
        )
        """)

        # Index for fast lookup
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_correspondence
        ON history (correspondence)
        """)

        conn.commit()
        conn.close()

    except Exception as e:
        print("DB INIT ERROR:", e)


create_table()


# =========================
# SAVE HISTORY
# =========================

def save_history(username, correspondence, bucket, a1, created_at):

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO history (user, correspondence, bucket, a1, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (username, correspondence, bucket, a1, created_at))

        conn.commit()
        conn.close()

    except Exception as e:
        print("SAVE HISTORY ERROR:", e)


# =========================
# FIND PREVIOUS MATCH
# =========================

def find_previous_match(correspondence):

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Partial match (better than exact match)
        cur.execute("""
        SELECT user, bucket, created_at
        FROM history
        WHERE correspondence LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """, (f"%{correspondence}%",))

        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "user": row[0],
                "bucket": row[1],
                "time": row[2]
            }

        return None

    except Exception as e:
        print("FIND MATCH ERROR:", e)
        return None