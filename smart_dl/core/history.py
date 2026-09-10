"""Download history with SQLite persistence."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, List, Optional

from smart_dl.core.paths import get_db_path

__all__ = [
    "add_to_history",
    "export_history",
    "get_history",
    "get_history_by_id",
    "get_history_stats",
    "init_db",
    "search_history",
]

_db_path_override: Optional[Path] = None


def set_history_db_path_for_tests(path: Optional[Path]) -> None:
    """Override the history DB path (tests only)."""
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def _get_db_path() -> Path:
    return _db_path_override if _db_path_override is not None else get_db_path("history")


def _get_conn() -> sqlite3.Connection:
    db = _get_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create history tables if they do not exist."""
    conn = _get_conn()
    try:
        conn.executescript(
            """
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
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_to_history(
    url: str,
    title: str = "",
    uploader: str = "",
    platform: str = "",
    file_path: str = "",
    file_size: int = 0,
    duration: float = 0,
    format_str: str = "",
    is_audio: bool = False,
    status: str = "completed",
    error: str = "",
    extra_data: Optional[dict] = None,
) -> int:
    """Append one download record.

    Parameters
    ----------
    url : str
        Source URL.
    title : str, optional
        Media title.
    uploader : str, optional
        Channel/uploader name.
    platform : str, optional
        Platform slug (``youtube``, ``aparat``, ...).
    file_path : str, optional
        Local filesystem path if known.
    file_size : int, optional
        Size in bytes.
    duration : float, optional
        Duration in seconds.
    format_str : str, optional
        yt-dlp format selector used.
    is_audio : bool, optional
        Whether the download was audio-only.
    status : str, optional
        ``completed`` or ``failed``.
    error : str, optional
        Error message when status is ``failed``.
    extra_data : dict, optional
        Extra JSON-serializable metadata.

    Returns
    -------
    int
        Row id of the inserted record.
    """
    conn = _get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO history (
                url, title, uploader, platform, file_path, file_size,
                duration, format_str, is_audio, status, error, downloaded_at, extra_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                title,
                uploader,
                platform,
                file_path,
                int(file_size or 0),
                float(duration or 0),
                format_str,
                1 if is_audio else 0,
                status,
                error,
                time.time(),
                json.dumps(extra_data or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def get_history(
    limit: int = 50,
    offset: int = 0,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[dict]:
    """Fetch history rows with optional filters.

    Parameters
    ----------
    limit : int, optional
        Maximum rows (default ``50``).
    offset : int, optional
        Rows to skip.
    platform : str, optional
        Filter by platform slug.
    status : str, optional
        Filter by status.
    search : str, optional
        Substring match on title/uploader/url.

    Returns
    -------
    list of dict
        Newest-first history entries.
    """
    conn = _get_conn()
    try:
        query = "SELECT * FROM history WHERE 1=1"
        params: list[Any] = []
        if platform:
            query += " AND platform=?"
            params.append(platform)
        if status:
            query += " AND status=?"
            params.append(status)
        if search:
            query += " AND (title LIKE ? OR uploader LIKE ? OR url LIKE ?)"
            token = f"%{search}%"
            params.extend([token, token, token])
        query += " ORDER BY downloaded_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def search_history(query: str, limit: int = 50) -> List[dict]:
    """Search history by keyword.

    Parameters
    ----------
    query : str
        Substring to match.
    limit : int, optional
        Maximum rows.

    Returns
    -------
    list of dict
        Matching entries.
    """
    return get_history(limit=limit, search=query)


def get_history_stats() -> dict:
    """Aggregate download statistics.

    Returns
    -------
    dict
        Keys: ``total_downloads``, ``total_size``, ``total_duration``,
        ``by_platform``, ``this_week``.
    """
    conn = _get_conn()
    try:
        stats: dict[str, Any] = {}
        row = conn.execute(
            "SELECT COUNT(*) AS cnt, SUM(file_size) AS total_size, "
            "SUM(duration) AS total_dur FROM history WHERE status='completed'"
        ).fetchone()
        stats["total_downloads"] = row["cnt"] or 0
        stats["total_size"] = row["total_size"] or 0
        stats["total_duration"] = row["total_dur"] or 0

        rows = conn.execute(
            "SELECT platform, COUNT(*) AS cnt FROM history "
            "WHERE status='completed' GROUP BY platform"
        ).fetchall()
        stats["by_platform"] = {r["platform"]: r["cnt"] for r in rows}

        week_ago = time.time() - 7 * 86400
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM history "
            "WHERE status='completed' AND downloaded_at > ?",
            (week_ago,),
        ).fetchone()
        stats["this_week"] = row["cnt"] or 0
        return stats
    finally:
        conn.close()


def get_history_by_id(hist_id: int) -> Optional[dict]:
    """Fetch a single history row by primary key.

    Parameters
    ----------
    hist_id : int
        History row id.

    Returns
    -------
    dict or None
        The row, or ``None`` if missing.
    """
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM history WHERE id=?", (hist_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def export_history(limit: int = 10000) -> str:
    """Export history as a JSON array string.

    Parameters
    ----------
    limit : int, optional
        Maximum rows to export.

    Returns
    -------
    str
        Pretty-printed JSON.
    """
    rows = get_history(limit=limit)
    data = [
        {
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
        }
        for r in rows
    ]
    return json.dumps(data, indent=2, ensure_ascii=False)
