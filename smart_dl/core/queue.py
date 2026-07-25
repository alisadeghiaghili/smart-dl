"""Download queue with SQLite persistence."""
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from smart_dl.core.config import load_config


def _get_db_path() -> Path:
    """Get the database file path."""
    cfg = load_config()
    data_dir = Path(cfg.get("data_dir", Path.home() / ".smartdl"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "queue.db"


def _get_conn():
    """Get a database connection."""
    db = _get_db_path()
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the queue database tables."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            created_at REAL DEFAULT 0,
            started_at REAL DEFAULT 0,
            finished_at REAL DEFAULT 0,
            error TEXT DEFAULT '',
            output_path TEXT DEFAULT '',
            format_str TEXT DEFAULT 'best',
            is_audio INTEGER DEFAULT 0,
            extra_opts TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
        CREATE INDEX IF NOT EXISTS idx_queue_priority ON queue(priority DESC);
    """)
    conn.commit()
    conn.close()


def add_to_queue(urls: List[str], fmt="best", is_audio=False, priority=0) -> int:
    """Add URLs to the download queue. Returns number added."""
    conn = _get_conn()
    now = time.time()
    count = 0
    for url in urls:
        # Skip duplicates that are pending/active
        existing = conn.execute(
            "SELECT id FROM queue WHERE url=? AND status IN ('pending','active')",
            (url,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO queue (url, status, priority, created_at, format_str, is_audio) VALUES (?, 'pending', ?, ?, ?, ?)",
                (url, priority, now, fmt, 1 if is_audio else 0)
            )
            count += 1
    conn.commit()
    conn.close()
    return count


def get_queue(status: Optional[str] = None) -> List[dict]:
    """Get queue items, optionally filtered by status."""
    conn = _get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM queue WHERE status=? ORDER BY priority DESC, created_at ASC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM queue ORDER BY priority DESC, created_at ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_next_pending() -> Optional[dict]:
    """Get the next pending item from the queue."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM queue WHERE status='pending' ORDER BY priority DESC, created_at ASC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_queue_status(item_id: int, status: str, error: str = "", output_path: str = ""):
    """Update the status of a queue item."""
    conn = _get_conn()
    now = time.time()
    if status == "active":
        conn.execute("UPDATE queue SET status=?, started_at=? WHERE id=?", (status, now, item_id))
    elif status in ("completed", "failed"):
        conn.execute("UPDATE queue SET status=?, finished_at=?, error=?, output_path=? WHERE id=?",
                      (status, now, error, output_path, item_id))
    else:
        conn.execute("UPDATE queue SET status=? WHERE id=?", (status, item_id))
    conn.commit()
    conn.close()


def clear_queue(status: Optional[str] = None):
    """Clear queue items. If status is None, clear all."""
    conn = _get_conn()
    if status:
        conn.execute("DELETE FROM queue WHERE status=?", (status,))
    else:
        conn.execute("DELETE FROM queue")
    conn.commit()
    conn.close()


def remove_from_queue(item_id: int):
    """Remove a specific item from the queue."""
    conn = _get_conn()
    conn.execute("DELETE FROM queue WHERE id=?", (item_id,))
    conn.commit()
    conn.close()


def get_queue_stats() -> dict:
    """Get queue statistics."""
    conn = _get_conn()
    stats = {}
    for status in ["pending", "active", "completed", "failed"]:
        row = conn.execute("SELECT COUNT(*) as cnt FROM queue WHERE status=?", (status,)).fetchone()
        stats[status] = row["cnt"]
    stats["total"] = sum(stats.values())
    conn.close()
    return stats
