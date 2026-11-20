"""
db.py
-----
SQLite layer for (1) each visitor's private history and (2) the community scam reports.

Privacy design: everything is tied to a random id kept in the visitor's own browser
cookie. We store only the job title and a short snippet, never the full posting.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "jobshield.db"
DAILY_REPORT_LIMIT = 20   # per browser, per 24 hours (slows down spam)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name: row["title"]
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id   TEXT NOT NULL,
                title        TEXT,
                snippet      TEXT,
                risk_percent INTEGER NOT NULL,
                verdict      TEXT NOT NULL,
                level        TEXT NOT NULL,
                flag_count   INTEGER NOT NULL,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_visitor ON analyses(visitor_id)")
        # UNIQUE(visitor_id, kind, value): one browser can report the same contact only once,
        # so one person cannot push a contact over the "confirmed" threshold alone.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                kind       TEXT NOT NULL,
                value      TEXT NOT NULL,
                category   TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (visitor_id, kind, value)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_report_value ON reports(kind, value)")


# ---------------- history ----------------
def save_analysis(visitor_id, title, snippet, result):
    # Parameterised query (?) protects against SQL injection. Never build SQL with f-strings.
    with connect() as conn:
        conn.execute(
            "INSERT INTO analyses (visitor_id, title, snippet, risk_percent, verdict, level, flag_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (visitor_id, title[:80], snippet[:120], result["risk_percent"],
             result["verdict"], result["level"], len(result["red_flags"])),
        )


def get_history(visitor_id, limit=50):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE visitor_id = ? ORDER BY id DESC LIMIT ?",
            (visitor_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def clear_history(visitor_id):
    with connect() as conn:
        conn.execute("DELETE FROM analyses WHERE visitor_id = ?", (visitor_id,))


# ---------------- community reports ----------------
def add_reports(visitor_id, entities, category):
    """Save reports for a list of (kind, value). Returns how many were newly added."""
    added = 0
    with connect() as conn:
        used = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE visitor_id = ? AND created_at >= datetime('now', '-1 day')",
            (visitor_id,),
        ).fetchone()[0]
        for kind, value in entities:
            if used + added >= DAILY_REPORT_LIMIT:
                break
            cur = conn.execute(
                "INSERT OR IGNORE INTO reports (visitor_id, kind, value, category) VALUES (?, ?, ?, ?)",
                (visitor_id, kind, value, category),
            )
            added += cur.rowcount
    return added


def report_counts(entities):
    """{(kind, value): number of different browsers that reported it}"""
    out = {}
    with connect() as conn:
        for kind, value in entities:
            out[(kind, value)] = conn.execute(
                "SELECT COUNT(*) FROM reports WHERE kind = ? AND value = ?", (kind, value)
            ).fetchone()[0]
    return out


def report_categories(kind, value):
    with connect() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS n FROM reports WHERE kind = ? AND value = ? GROUP BY category ORDER BY n DESC",
            (kind, value),
        ).fetchall()
    return {r["category"]: r["n"] for r in rows}


def community_stats():
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        unique = conn.execute("SELECT COUNT(*) FROM (SELECT 1 FROM reports GROUP BY kind, value)").fetchone()[0]
        week = conn.execute("SELECT COUNT(*) FROM reports WHERE created_at >= datetime('now', '-7 day')").fetchone()[0]
    return {"total": total, "unique": unique, "week": week}


def top_reported(limit=8, min_reports=2):
    """Public list. A contact needs at least 2 separate reports to appear, so one report never publicly names anyone."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT kind, value, COUNT(*) AS n, MAX(created_at) AS last FROM reports "
            "GROUP BY kind, value HAVING n >= ? ORDER BY n DESC, last DESC LIMIT ?",
            (min_reports, limit),
        ).fetchall()
    return [dict(r) for r in rows]