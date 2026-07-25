"""Download history with SQLite persistence."""
import json
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
    return data_dir / "history.db"


def _get_conn():
    """Get a database connection."""
    db = _get_db_path()
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the history database tables."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT DEFAULT '',
            uploader TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            file_size INTEGER DEFAULT 0,
            duration REAL DEFAULT 0,
            format_str TEXT DEFAULT '',
            is_audio INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            error TEXT DEFAULT '',
            downloaded_at REAL DEFAULT 0,
            extra_data TEXT DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_history_url ON history(url);
        CREATE INDEX IF NOT EXISTS idx_history_platform ON history(platform);
        CREATE INDEX IF NOT EXISTS idx_history_downloaded ON history(downloaded_at DESC);
    """)
    conn.commit()
    conn.close()


def add_to_history(url: str, title: str = "", uploader: str = "", platform: str = "",
                   file_path: str = "", file_size: int = 0, duration: float = 0,
                   format_str: str = "", is_audio: bool = False, status: str = "completed",
                   error: str = "", extra_data: dict = None) -> int:
    """Add a download to history. Returns the history ID."""
    conn = _get_conn()
    now = time.time()
    cursor = conn.execute(
        """INSERT INTO history (url, title, uploader, platform, file_path, file_size,
           duration, format_str, is_audio, status, error, downloaded_at, extra_data)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (url, title, uploader, platform, file_path, file_size, duration,
         format_str, 1 if is_audio else 0, status, error, now,
         json.dumps(extra_data or {}))
    )
    conn.commit()
    hist_id = cursor.lastrowid
    conn.close()
    return hist_id


def get_history(limit: int = 50, offset: int = 0, platform: str = None,
                status: str = None, search: str = None) -> List[dict]:
    """Get download history with optional filters."""
    conn = _get_conn()
    query = "SELECT * FROM history WHERE 1=1"
    params = []

    if platform:
        query += " AND platform=?"
        params.append(platform)
    if status:
        query += " AND status=?"
        params.append(status)
    if search:
        query += " AND (title LIKE ? OR uploader LIKE ? OR url LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])

    query += " ORDER BY downloaded_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_history(query: str, limit: int = 50) -> List[dict]:
    """Search history by keyword."""
    return get_history(limit=limit, search=query)


def get_history_stats() -> dict:
    """Get download statistics."""
    conn = _get_conn()
    stats = {}

    row = conn.execute("SELECT COUNT(*) as cnt, SUM(file_size) as total_size, SUM(duration) as total_dur FROM history WHERE status='completed'").fetchone()
    stats["total_downloads"] = row["cnt"] or 0
    stats["total_size"] = row["total_size"] or 0
    stats["total_duration"] = row["total_dur"] or 0

    # By platform
    rows = conn.execute("SELECT platform, COUNT(*) as cnt FROM history WHERE status='completed' GROUP BY platform").fetchall()
    stats["by_platform"] = {r["platform"]: r["cnt"] for r in rows}

    # By date (last 7 days)
    now = time.time()
    week_ago = now - 7 * 86400
    row = conn.execute("SELECT COUNT(*) as cnt FROM history WHERE status='completed' AND downloaded_at > ?", (week_ago,)).fetchone()
    stats["this_week"] = row["cnt"] or 0

    conn.close()
    return stats


def get_history_by_id(hist_id: int) -> Optional[dict]:
    """Get a specific history entry."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM history WHERE id=?", (hist_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def export_history(format: str = "json") -> str:
    """Export history as JSON string."""
    rows = get_history(limit=10000)
    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "uploader": r["uploader"],
            "platform": r["platform"],
            "file_path": r["file_path"],
            "file_size": r["file_size"],
            "duration": r["duration"],
            "format": r["format_str"],
            "is_audio": bool(r["is_audio"]),
            "status": r["status"],
            "downloaded_at": r["downloaded_at"],
        })
    return json.dumps(data, indent=2, ensure_ascii=False)
