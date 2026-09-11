"""Download queue with SQLite persistence and a sequential processor."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Callable, List, Optional

from smart_dl.core.paths import get_db_path

__all__ = [
    "add_to_queue",
    "clear_queue",
    "get_next_pending",
    "get_queue",
    "get_queue_stats",
    "init_db",
    "pause_queue",
    "process_queue",
    "remove_from_queue",
    "resume_queue",
    "update_queue_status",
]

_db_path_override: Optional[Path] = None


def set_queue_db_path_for_tests(path: Optional[Path]) -> None:
    """Override the queue DB path (tests only)."""
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def _get_db_path() -> Path:
    return _db_path_override if _db_path_override is not None else get_db_path("queue")


def _get_conn() -> sqlite3.Connection:
    db = _get_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create queue tables if they do not exist."""
    conn = _get_conn()
    try:
        conn.executescript(
            """
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
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_to_queue(
    urls: List[str],
    fmt: str = "best",
    is_audio: bool = False,
    priority: int = 0,
) -> int:
    """Add URLs to the queue, skipping duplicates that are still pending/active.

    Parameters
    ----------
    urls : list of str
        URLs to enqueue.
    fmt : str, optional
        Default format selector stored with each item.
    is_audio : bool, optional
        Whether items are audio-only.
    priority : int, optional
        Higher priority is processed first.

    Returns
    -------
    int
        Number of rows actually inserted.
    """
    conn = _get_conn()
    try:
        now = time.time()
        count = 0
        for url in urls:
            existing = conn.execute(
                "SELECT id FROM queue WHERE url=? AND status IN ('pending','active')",
                (url,),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO queue (url, status, priority, created_at, format_str, is_audio) "
                    "VALUES (?, 'pending', ?, ?, ?, ?)",
                    (url, priority, now, fmt, 1 if is_audio else 0),
                )
                count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def get_queue(status: Optional[str] = None) -> List[dict]:
    """Return queue items ordered by priority then age.

    Parameters
    ----------
    status : str, optional
        Optional status filter.

    Returns
    -------
    list of dict
        Queue rows.
    """
    conn = _get_conn()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM queue WHERE status=? ORDER BY priority DESC, created_at ASC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM queue ORDER BY priority DESC, created_at ASC"
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_next_pending() -> Optional[dict]:
    """Return the next pending item, or ``None`` when the queue is empty."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM queue WHERE status='pending' "
            "ORDER BY priority DESC, created_at ASC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_queue_status(
    item_id: int,
    status: str,
    error: str = "",
    output_path: str = "",
) -> None:
    """Update status and timestamps for one queue item.

    Parameters
    ----------
    item_id : int
        Queue row id.
    status : str
        New status (``pending``, ``active``, ``paused``, ``completed``, ``failed``).
    error : str, optional
        Error text when failing.
    output_path : str, optional
        Final file path when completed.
    """
    conn = _get_conn()
    try:
        now = time.time()
        if status == "active":
            conn.execute(
                "UPDATE queue SET status=?, started_at=? WHERE id=?",
                (status, now, item_id),
            )
        elif status in ("completed", "failed"):
            conn.execute(
                "UPDATE queue SET status=?, finished_at=?, error=?, output_path=? WHERE id=?",
                (status, now, error, output_path, item_id),
            )
        else:
            conn.execute("UPDATE queue SET status=? WHERE id=?", (status, item_id))
        conn.commit()
    finally:
        conn.close()


def clear_queue(status: Optional[str] = None) -> None:
    """Delete queue rows, optionally filtered by status."""
    conn = _get_conn()
    try:
        if status:
            conn.execute("DELETE FROM queue WHERE status=?", (status,))
        else:
            conn.execute("DELETE FROM queue")
        conn.commit()
    finally:
        conn.close()


def remove_from_queue(item_id: int) -> None:
    """Delete a single queue item by id."""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM queue WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def get_queue_stats() -> dict:
    """Count items by status.

    Returns
    -------
    dict
        Keys: ``pending``, ``active``, ``completed``, ``failed``, ``paused``, ``total``.
    """
    conn = _get_conn()
    try:
        stats: dict[str, int] = {}
        for status in ("pending", "active", "completed", "failed", "paused"):
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM queue WHERE status=?", (status,)
            ).fetchone()
            stats[status] = row["cnt"] or 0
        stats["total"] = sum(stats[s] for s in ("pending", "active", "completed", "failed", "paused"))
        return stats
    finally:
        conn.close()


def pause_queue() -> int:
    """Mark all active items as paused.

    Returns
    -------
    int
        Number of rows paused.
    """
    conn = _get_conn()
    try:
        cursor = conn.execute("UPDATE queue SET status='paused' WHERE status='active'")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def resume_queue() -> int:
    """Mark all paused items back to pending.

    Returns
    -------
    int
        Number of rows resumed.
    """
    conn = _get_conn()
    try:
        cursor = conn.execute("UPDATE queue SET status='pending' WHERE status='paused'")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def process_queue(
    download_fn: Callable[[dict], bool],
    *,
    max_items: Optional[int] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> dict:
    """Process pending queue items sequentially using *download_fn*.

    Parameters
    ----------
    download_fn : Callable[[dict], bool]
        Receives a queue row dict; returns ``True`` on success.
    max_items : int, optional
        Stop after this many items (``None`` = drain the queue).
    should_stop : Callable[[], bool], optional
        Polled before each item; when true, processing stops early.

    Returns
    -------
    dict
        ``processed``, ``completed``, ``failed``, ``stopped``.

    Examples
    --------
    >>> def fake(item):
    ...     return True
    >>> # process_queue(fake)  # doctest: +SKIP
    """
    init_db()
    processed = completed = failed = 0
    stopped = False

    while True:
        if should_stop is not None and should_stop():
            stopped = True
            break
        if max_items is not None and processed >= max_items:
            break
        item = get_next_pending()
        if item is None:
            break
        update_queue_status(item["id"], "active")
        try:
            ok = bool(download_fn(item))
        except KeyboardInterrupt:
            update_queue_status(item["id"], "pending")
            raise
        except Exception as exc:  # noqa: BLE001 — isolate per-item failures
            update_queue_status(item["id"], "failed", error=str(exc)[:200])
            failed += 1
            processed += 1
            continue
        if ok:
            update_queue_status(item["id"], "completed")
            completed += 1
        else:
            update_queue_status(item["id"], "failed", error="download reported failure")
            failed += 1
        processed += 1

    return {
        "processed": processed,
        "completed": completed,
        "failed": failed,
        "stopped": stopped,
    }
