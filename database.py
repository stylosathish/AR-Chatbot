import sqlite3

DB_NAME = "history.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            correspondence TEXT,
            bucket TEXT,
            a1 TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_history(
    username,
    correspondence,
    bucket,
    a1,
    created_at
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history (
            username,
            correspondence,
            bucket,
            a1,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        correspondence,
        bucket,
        a1,
        created_at
    ))

    conn.commit()
    conn.close()


def find_previous_match(correspondence):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            username,
            bucket,
            a1,
            created_at
        FROM history
        WHERE correspondence = ?
        ORDER BY id DESC
        LIMIT 1
    """, (correspondence,))

    row = cursor.fetchone()

    conn.close()

    if row:

        return {
            "user": row[0],
            "bucket": row[1],
            "a1": row[2],
            "created_at": row[3]
        }

    return None


init_db()