"""Channel subscriptions — follow creators and auto-download new uploads."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from smart_dl.core.paths import get_db_path

_db_path_override: Optional[Path] = None


def set_subscriptions_db_path_for_tests(path: Optional[Path]) -> None:
    """Override the subscriptions DB path (tests only)."""
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def _get_db_path() -> Path:
    if _db_path_override is not None:
        return _db_path_override
    return get_db_path("subscriptions")


def _get_conn():
    db = _get_db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            name TEXT DEFAULT '',
            platform TEXT DEFAULT 'youtube',
            last_checked REAL DEFAULT 0,
            last_video_id TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            auto_download INTEGER DEFAULT 0,
            output_dir TEXT DEFAULT '',
            created_at REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS subscription_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_id INTEGER NOT NULL,
            video_url TEXT NOT NULL,
            video_title TEXT DEFAULT '',
            video_id TEXT DEFAULT '',
            downloaded_at REAL DEFAULT 0,
            FOREIGN KEY (sub_id) REFERENCES subscriptions(id)
        );
    """)
    conn.commit()
    conn.close()


def add_subscription(url: str, name: str = "", platform: str = "youtube",
                     auto_download: bool = False, output_dir: str = "") -> int:
    """Add a channel/playlist subscription."""
    conn = _get_conn()
    now = time.time()
    try:
        cursor = conn.execute(
            """INSERT INTO subscriptions (url, name, platform, auto_download, output_dir, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (url, name, platform, 1 if auto_download else 0, output_dir, now)
        )
        conn.commit()
        sub_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Already subscribed
        row = conn.execute("SELECT id FROM subscriptions WHERE url=?", (url,)).fetchone()
        sub_id = row["id"] if row else -1
    conn.close()
    return sub_id


def get_subscriptions(enabled_only: bool = True) -> List[dict]:
    """Get all subscriptions.

    Parameters
    ----------
    enabled_only : bool, optional
        When True, only enabled rows are returned.

    Returns
    -------
    list of dict
        Subscription rows, newest first.
    """
    conn = _get_conn()
    try:
        if enabled_only:
            rows = conn.execute(
                "SELECT * FROM subscriptions WHERE enabled=1 ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM subscriptions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_subscription_by_id(sub_id: int) -> Optional[dict]:
    """Fetch one subscription by id.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.

    Returns
    -------
    dict or None
        The row, or ``None`` if missing.
    """
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM subscriptions WHERE id=?", (sub_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_subscription_video_ids(sub_id: int) -> List[str]:
    """Return video ids already recorded for a subscription.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.

    Returns
    -------
    list of str
        Video ids (may contain empty strings from incomplete rows).
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT video_id FROM subscription_history WHERE sub_id=?",
            (sub_id,),
        ).fetchall()
        return [r["video_id"] for r in rows if r["video_id"]]
    finally:
        conn.close()


def remove_subscription(sub_id: int):
    """Remove a subscription.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.
    """
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM subscriptions WHERE id=?", (sub_id,))
        conn.execute("DELETE FROM subscription_history WHERE sub_id=?", (sub_id,))
        conn.commit()
    finally:
        conn.close()


def update_last_checked(sub_id: int, video_id: str = ""):
    """Update the last checked time and newest video id.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.
    video_id : str, optional
        Newest video id seen at check time.
    """
    conn = _get_conn()
    try:
        now = time.time()
        conn.execute(
            "UPDATE subscriptions SET last_checked=?, last_video_id=? WHERE id=?",
            (now, video_id, sub_id),
        )
        conn.commit()
    finally:
        conn.close()


def add_subscription_video(sub_id: int, video_url: str, video_title: str = "", video_id: str = ""):
    """Record a downloaded video for a subscription.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.
    video_url : str
        Video URL.
    video_title : str, optional
        Display title.
    video_id : str, optional
        Platform video id.
    """
    conn = _get_conn()
    try:
        now = time.time()
        conn.execute(
            "INSERT INTO subscription_history "
            "(sub_id, video_url, video_title, video_id, downloaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (sub_id, video_url, video_title, video_id, now),
        )
        conn.commit()
    finally:
        conn.close()


def toggle_subscription(sub_id: int, enabled: bool = None):
    """Toggle or set subscription enabled state.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.
    enabled : bool, optional
        Explicit state; toggles current value when ``None``.
    """
    conn = _get_conn()
    try:
        if enabled is None:
            row = conn.execute(
                "SELECT enabled FROM subscriptions WHERE id=?", (sub_id,)
            ).fetchone()
            enabled = not bool(row["enabled"]) if row else True
        conn.execute(
            "UPDATE subscriptions SET enabled=? WHERE id=?",
            (1 if enabled else 0, sub_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_subscription_stats() -> dict:
    """Get subscription statistics.

    Returns
    -------
    dict
        Keys ``active``, ``total``, ``videos_downloaded``.
    """
    conn = _get_conn()
    try:
        stats = {}
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM subscriptions WHERE enabled=1"
        ).fetchone()
        stats["active"] = row["cnt"] or 0
        row = conn.execute("SELECT COUNT(*) AS cnt FROM subscriptions").fetchone()
        stats["total"] = row["cnt"] or 0
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM subscription_history"
        ).fetchone()
        stats["videos_downloaded"] = row["cnt"] or 0
        return stats
    finally:
        conn.close()
