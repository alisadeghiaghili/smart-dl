"""Download management — list, filter, sort, export, cleanup."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, List, Optional, Set

from rich import box
from rich.panel import Panel
from rich.table import Table

from smart_dl.core.history import (
    HistoryStatus,
    export_history,
    get_history,
    get_history_stats,
    search_history,
)
from smart_dl.ui import console, info, success, warn

try:
    from smart_dl.lang import t
except ImportError:

    def t(key: str, **kwargs: Any) -> str:
        return key


def list_downloads(
    limit: int = 50,
    sort_by: str = "date",
    filter_by: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
) -> None:
    """List download history with optional filters.

    Parameters
    ----------
    limit : int, optional
        Maximum rows to display.
    sort_by : str, optional
        ``date``, ``name``, or ``size``.
    filter_by : str, optional
        Platform slug filter.
    status_filter : str, optional
        Canonical history status (``HistoryStatus``).
    search : str, optional
        Substring search across title/uploader/url.

    Returns
    -------
    None
        Prints a table to the console.
    """
    if search:
        rows = search_history(search, limit=limit)
    else:
        rows = get_history(limit=limit, platform=filter_by, status=status_filter)

    if not rows:
        info(t("no_downloads") if t("no_downloads") != "no_downloads" else "No downloads found.")
        return

    # Sort
    if sort_by == "name":
        rows.sort(key=lambda r: r.get("title", "").lower())
    elif sort_by == "size":
        rows.sort(key=lambda r: r.get("file_size", 0), reverse=True)
    elif sort_by == "date":
        rows.sort(key=lambda r: r.get("downloaded_at", 0), reverse=True)

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta",
                  border_style="dim", padding=(0,1))
    table.add_column("#", style="bold cyan", width=6, justify="right")
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Platform", style="dim", width=10)
    table.add_column("Size", style="blue", width=10)
    table.add_column("Date", style="dim", width=12)
    table.add_column("Status", width=10)

    from smart_dl.utils import fmt_size

    for r in rows:
        ts = r.get("downloaded_at", 0)
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
        size = fmt_size(r.get("file_size", 0))
        status = r.get("status", "?")
        if status == HistoryStatus.COMPLETED:
            status_style = ""
        elif status == HistoryStatus.FAILED:
            status_style = "[red]"
        else:
            status_style = "[yellow]"
        status_cell = status if not status_style else status_style + status + "[/]"

        table.add_row(
            str(r.get("id", "?")),
            r.get("title", "?")[:40],
            r.get("platform", "?"),
            size,
            date_str,
            status_cell,
        )

    console.print(table)
    info(f"{t('showing_downloads') if t('showing_downloads') != 'showing_downloads' else 'Showing'} {len(rows)} downloads")


def show_stats():
    """Show download statistics."""
    stats = get_history_stats()

    from smart_dl.utils import fmt_dur, fmt_size

    body = (
        f"[bold cyan]Total Downloads:[/bold cyan] {stats['total_downloads']}\n"
        f"[bold cyan]Total Size:[/bold cyan] {fmt_size(stats['total_size'])}\n"
        f"[bold cyan]Total Watch Time:[/bold cyan] {fmt_dur(stats['total_duration'])}\n"
        f"[bold cyan]This Week:[/bold cyan] {stats['this_week']} downloads\n"
    )

    if stats.get("by_platform"):
        body += "\n[bold cyan]By Platform:[/bold cyan]\n"
        for platform, count in sorted(stats["by_platform"].items(), key=lambda x: -x[1]):
            body += f"  {platform or 'unknown'}: {count}\n"

    console.print(Panel(body, title="[bold cyan]  Download Statistics[/bold cyan]",
                        border_style="cyan", padding=(0,2)))


def export_downloads(output_path: str = "downloads.json"):
    """Export download history to JSON file."""
    data = export_history()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(data)
    success(f"Exported to {output_path}")


def _history_file_paths(status: str) -> Set[str]:
    """Collect non-empty ``file_path`` values for one history status.

    Parameters
    ----------
    status : str
        Canonical status value from :class:`HistoryStatus`.

    Returns
    -------
    set of str
        Absolute or recorded file paths present in history for that status.
    """
    rows = get_history(status=status, limit=10000)
    return {r.get("file_path", "") for r in rows if r.get("file_path")}


def cleanup_downloads(dry_run: bool = False) -> int:
    """Remove files recorded under failed downloads.

    A file is skipped when any history row marks it ``HistoryStatus.COMPLETED``
    so a later successful re-download is not deleted. Uses the production
    status vocabulary only — never a synonym such as ``success``.

    Parameters
    ----------
    dry_run : bool, optional
        When ``True``, only report what would be removed.

    Returns
    -------
    int
        Number of files actually removed (``0`` when ``dry_run`` is ``True``).

    Examples
    --------
    >>> cleanup_downloads(dry_run=True)  # doctest: +SKIP
    0
    """
    failed_rows = get_history(status=HistoryStatus.FAILED, limit=10000)
    if not failed_rows:
        info(t("no_failed_downloads") if t("no_failed_downloads") != "no_failed_downloads" else "No failed downloads to clean up.")
        return 0

    completed_paths = _history_file_paths(HistoryStatus.COMPLETED)

    files_to_remove: List[str] = []
    for record in failed_rows:
        file_path = record.get("file_path", "")
        if (
            file_path
            and file_path not in completed_paths
            and os.path.isfile(file_path)
        ):
            files_to_remove.append(file_path)

    if not files_to_remove:
        info(t("no_cleanup_files") if t("no_cleanup_files") != "no_cleanup_files" else "No files to clean up.")
        return 0

    if dry_run:
        info(f"Would remove {len(files_to_remove)} files:")
        for path in files_to_remove[:20]:
            info(f"  {path}")
        if len(files_to_remove) > 20:
            info(f"  ... and {len(files_to_remove) - 20} more")
        return 0

    removed = 0
    errors = 0
    for path in files_to_remove:
        try:
            os.remove(path)
            removed += 1
        except OSError as exc:
            errors += 1
            info(f"Could not remove {path}: {exc}")
    if errors:
        warn(f"Removed {removed}/{len(files_to_remove)} files ({errors} error(s))")
    else:
        success(f"Removed {removed}/{len(files_to_remove)} files")
    return removed
