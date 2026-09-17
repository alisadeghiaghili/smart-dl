"""Night download scheduler (roadmap R5).

SQLite-backed scheduled URLs. Due items are pushed into the normal queue
when :func:`process_due` runs (``smart-dl --schedule start``).
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

from smart_dl.core.paths import get_db_path

__all__ = [
    "add_scheduled_url",
    "clear_schedule",
    "get_schedule",
    "init_db",
    "parse_run_at",
    "process_due",
    "remove_scheduled",
    "set_schedule_db_path_for_tests",
]

_db_path_override: Optional[Path] = None


def set_schedule_db_path_for_tests(path: Optional[Path]) -> None:
    """Override the schedule DB path (tests only)."""
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def _get_db_path() -> Path:
    return _db_path_override if _db_path_override is not None else get_db_path("schedule")


def _get_conn() -> sqlite3.Connection:
    db = _get_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create the schedule table if missing."""
    conn = _get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                run_at REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at REAL DEFAULT 0,
                finished_at REAL DEFAULT 0,
                error TEXT DEFAULT '',
                format_str TEXT DEFAULT 'best',
                is_audio INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_schedule_status_run
                ON schedule(status, run_at);
            """
        )
        conn.commit()
    finally:
        conn.close()


def parse_run_at(value: str, *, now: Optional[float] = None) -> float:
    """Parse a human run time into a Unix timestamp.

    Accepted forms:
      - ``HH:MM`` / ``HH:MM:SS`` → next occurrence (today or tomorrow)
      - ISO ``YYYY-MM-DD HH:MM`` or ``YYYY-MM-DDTHH:MM``
      - integer/float epoch seconds

    Parameters
    ----------
    value : str
        Time expression.
    now : float, optional
        Reference timestamp (default ``time.time()``).

    Returns
    -------
    float
        Unix timestamp for the run.

    Raises
    ------
    ValueError
        When the expression cannot be parsed.

    Examples
    --------
    >>> parse_run_at("00:00", now=0) > 0
    True
    """
    if value is None:
        raise ValueError("run time required")
    text = str(value).strip()
    if not text:
        raise ValueError("run time required")
    base = float(now if now is not None else time.time())

    if text.replace(".", "", 1).isdigit():
        return float(text)

    # Relative offsets: +2h, +30m, +1d
    if text.startswith("+") and len(text) > 2:
        rel = text[1:].lower()
        unit = rel[-1]
        try:
            amount = float(rel[:-1])
        except ValueError as exc:
            raise ValueError(f"unrecognized time: {value!r}") from exc
        mult = {"h": 3600, "m": 60, "d": 86400, "s": 1}.get(unit)
        if mult is None:
            raise ValueError(f"unrecognized time unit in: {value!r}")
        return base + amount * mult

    fmt_candidates = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M")
    for fmt in fmt_candidates:
        try:
            dt = datetime.strptime(text, fmt)
            return dt.timestamp()
        except ValueError:
            continue

    time_fmt = "%H:%M:%S" if text.count(":") == 2 else "%H:%M"
    try:
        tod = datetime.strptime(text, time_fmt)
    except ValueError as exc:
        raise ValueError(f"unrecognized time: {value!r}") from exc

    base_dt = datetime.fromtimestamp(base)
    candidate = base_dt.replace(
        hour=tod.hour,
        minute=tod.minute,
        second=tod.second,
        microsecond=0,
    )
    if candidate.timestamp() <= base:
        candidate = candidate + timedelta(days=1)
    return candidate.timestamp()


def add_scheduled_url(
    url: str,
    run_at: str | float,
    *,
    fmt: str = "best",
    is_audio: bool = False,
    now: Optional[float] = None,
) -> int:
    """Schedule a URL for later download.

    Parameters
    ----------
    url : str
        Media URL.
    run_at : str or float
        Human time or epoch seconds (see :func:`parse_run_at`).
    fmt : str, optional
        Format string stored with the job.
    is_audio : bool, optional
        Audio-only flag.
    now : float, optional
        Reference time for ``HH:MM`` parsing.

    Returns
    -------
    int
        Schedule row id.
    """
    ts = run_at if isinstance(run_at, (int, float)) else parse_run_at(str(run_at), now=now)
    init_db()
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO schedule (url, run_at, status, created_at, format_str, is_audio) "
            "VALUES (?, ?, 'pending', ?, ?, ?)",
            (url, float(ts), time.time(), fmt, 1 if is_audio else 0),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)
    finally:
        conn.close()


def get_schedule(status: Optional[str] = "pending") -> List[Dict]:
    """Return schedule rows.

    Parameters
    ----------
    status : str, optional
        Filter by status; ``None`` returns all rows.

    Returns
    -------
    list of dict
        Rows ordered by ``run_at`` ascending.
    """
    init_db()
    conn = _get_conn()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM schedule WHERE status=? ORDER BY run_at ASC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM schedule ORDER BY run_at ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def remove_scheduled(job_id: int) -> bool:
    """Delete one schedule row.

    Parameters
    ----------
    job_id : int
        Schedule primary key.

    Returns
    -------
    bool
        ``True`` when a row was deleted.
    """
    init_db()
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM schedule WHERE id=?", (job_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def clear_schedule(status: Optional[str] = None) -> int:
    """Delete schedule rows.

    Parameters
    ----------
    status : str, optional
        Delete only this status; ``None`` deletes all.

    Returns
    -------
    int
        Number of rows deleted.
    """
    init_db()
    conn = _get_conn()
    try:
        if status:
            cursor = conn.execute("DELETE FROM schedule WHERE status=?", (status,))
        else:
            cursor = conn.execute("DELETE FROM schedule")
        conn.commit()
        return int(cursor.rowcount or 0)
    finally:
        conn.close()


def process_due(
    *,
    now: Optional[float] = None,
    enqueue: Optional[Callable[[List[str]], int]] = None,
) -> Dict[str, int]:
    """Mark due pending jobs as active and enqueue their URLs.

    Parameters
    ----------
    now : float, optional
        Reference timestamp (default ``time.time()``).
    enqueue : Callable[[list[str]], int], optional
        Queue inserter; defaults to :func:`smart_dl.core.queue.add_to_queue`.

    Returns
    -------
    dict
        Counts: ``due``, ``enqueued``.
    """
    from smart_dl.core.queue import add_to_queue

    init_db()
    ts = float(now if now is not None else time.time())
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM schedule WHERE status='pending' AND run_at<=? ORDER BY run_at ASC",
            (ts,),
        ).fetchall()
        due = [dict(r) for r in rows]
        if not due:
            return {"due": 0, "enqueued": 0}
        ids = [int(r["id"]) for r in due]
        urls = [str(r["url"]) for r in due]
        placeholders = ",".join("?" for _ in ids)
        conn.execute(
            f"UPDATE schedule SET status='enqueued', finished_at=? WHERE id IN ({placeholders})",
            (ts, *ids),
        )
        conn.commit()
    finally:
        conn.close()

    sink = enqueue or add_to_queue
    try:
        added = int(sink(urls))
    except Exception:
        # Leave rows enqueued; caller can inspect queue.
        added = 0
    return {"due": len(due), "enqueued": added}
