"""CLI command handlers for Wave 1–2 features (R2/C-Auth/R8/R4/R7)."""

from __future__ import annotations

from typing import Optional

__all__ = [
    "handle_clipboard_watch",
    "handle_config_export",
    "handle_config_import",
    "handle_notify_test",
    "handle_set_cookie_browser",
    "handle_update_ytdlp",
]


def handle_update_ytdlp(flag: Optional[bool] = None) -> bool:
    """Run opt-in yt-dlp update when requested.

    Parameters
    ----------
    flag : bool, optional
        CLI flag value.

    Returns
    -------
    bool
        ``True`` if an update was attempted and succeeded; ``False`` otherwise
        (including when not requested).
    """
    from smart_dl.core.ytdlp_updater import should_update_ytdlp, update_yt_dlp
    from smart_dl.ui import info

    if not should_update_ytdlp(flag):
        return False
    ok, _msg = update_yt_dlp()
    if not ok:
        info("Continuing with the currently installed yt-dlp.")
    return ok


def handle_set_cookie_browser(browser: Optional[str], *, list_only: bool = False) -> None:
    """Set or list cookie browser for downloads.

    Parameters
    ----------
    browser : str or None
        Browser key (``firefox``, ``edge``, ...).
    list_only : bool, optional
        Print supported browsers and current setting.

    Returns
    -------
    None
    """
    from smart_dl.core.cookie_diag import cookie_diagnose_report
    from smart_dl.core.cookies import (
        BROWSERS_TO_TRY,
        clear_cookie_browser,
        get_cookie_browser,
        set_cookie_browser,
    )
    from smart_dl.ui import console, info, success, warn

    if list_only or not browser:
        current = get_cookie_browser() or "(unset)"
        console.print("[bold cyan]Cookie browsers[/bold cyan]")
        console.print(f"  Current : {current}")
        console.print("  Supported: " + ", ".join(BROWSERS_TO_TRY))
        console.print("  Tip: firefox works best on Windows; or use --cookies-file cookies.txt")
        report = cookie_diagnose_report()
        if isinstance(report, dict) and report.get("configured"):
            by_domain = report.get("by_domain") or {}
            yt_count = by_domain.get("youtube.com", 0) if isinstance(by_domain, dict) else 0
            console.print(
                f"  Diagnose: {report.get('browser')} extract_ok={report.get('extract_ok')} "
                f"total={report.get('total_cookies')} youtube={yt_count}"
            )
        return

    key = browser.strip().lower()
    if key in {"none", "off", "clear", ""}:
        clear_cookie_browser()
        success("Cookie browser cleared.")
        return
    if key not in BROWSERS_TO_TRY:
        warn(f"Unknown browser '{key}'. Supported: {', '.join(BROWSERS_TO_TRY)}")
        return
    set_cookie_browser(key)
    success(f"Cookie browser set to {key}")
    report = cookie_diagnose_report(browser=key)
    if isinstance(report, dict) and report.get("extract_ok"):
        by_domain = report.get("by_domain") or {}
        yt_count = by_domain.get("youtube.com", 0) if isinstance(by_domain, dict) else 0
        info(f"Extracted {report.get('total_cookies')} cookies (youtube={yt_count})")
    elif isinstance(report, dict):
        warn(f"Browser set, but extraction failed: {report.get('error')}")


def handle_config_export(path: Optional[str]) -> None:
    """Export portable config keys to a JSON file.

    Parameters
    ----------
    path : str or None
        Destination path.

    Returns
    -------
    None
    """
    from smart_dl.core.config_io import export_config
    from smart_dl.ui import error, success

    if not path:
        error("Usage: --export-config PATH")
        return
    try:
        out = export_config(path)
        success(f"Exported portable config → {out}")
    except OSError as exc:
        error(f"Export failed: {exc}")


def handle_config_import(path: Optional[str]) -> None:
    """Import portable config keys from a JSON file.

    Parameters
    ----------
    path : str or None
        Source path.

    Returns
    -------
    None
    """
    from smart_dl.core.config_io import import_config
    from smart_dl.ui import error, info, success

    if not path:
        error("Usage: --import-config PATH")
        return
    try:
        applied = import_config(path, merge=True)
        if not applied:
            info("No portable keys found in file.")
        else:
            success(f"Imported {len(applied)} key(s): {', '.join(sorted(applied))}")
    except (OSError, ValueError) as exc:
        error(f"Import failed: {exc}")


def handle_notify_test() -> None:
    """Send a Telegram test notification.

    Returns
    -------
    None
    """
    from smart_dl.core.telegram_notify import notify_test
    from smart_dl.ui import error, success

    if notify_test():
        success("Telegram test message sent.")
    else:
        error("Telegram test failed (check telegram_bot_token / telegram_chat_id).")


def handle_clipboard_watch(
    *,
    interval: float = 2.0,
    max_items: Optional[int] = 10,
    enqueue: bool = True,
) -> None:
    """Watch clipboard for media URLs and optionally enqueue them.

    Parameters
    ----------
    interval : float, optional
        Poll interval seconds.
    max_items : int, optional
        Stop after N new URLs (``None`` runs until Ctrl+C).
    enqueue : bool, optional
        Add discovered URLs to the download queue.

    Returns
    -------
    None
    """
    from smart_dl.core.clipboard import watch_clipboard
    from smart_dl.ui import info, success, warn
    from smart_dl.ui.progress import stop_event

    info(f"Clipboard watcher started (interval={interval}s, max={max_items}). Copy a media URL…")

    def _on_url(url: str) -> None:
        info(f"Grabbed: {url}")
        if enqueue:
            from smart_dl.core.queue import add_to_queue, init_db

            init_db()
            added = add_to_queue([url])
            if added:
                info(f"Queued #{url[:60]}")
            else:
                info("Already in queue.")

    try:
        found = watch_clipboard(
            interval=float(interval) or 1.0,
            max_items=max_items,
            on_url=_on_url,
            should_stop=stop_event.is_set,
        )
    except KeyboardInterrupt:
        warn("Clipboard watcher stopped.")
        return
    success(f"Clipboard watcher finished: {len(found)} URL(s)")
    if enqueue:
        info("Start queue with: smart-dl --queue start")
