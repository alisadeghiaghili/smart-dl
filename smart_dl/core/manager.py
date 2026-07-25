"""Download management — list, filter, sort, export, cleanup."""
import os
import json
from pathlib import Path
from typing import List, Optional

from smart_dl.core.history import get_history, get_history_stats, export_history, search_history
from smart_dl.ui import console, success, warn, error, info
from rich.table import Table
from rich.panel import Panel
from rich import box

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


def list_downloads(limit: int = 50, sort_by: str = "date", filter_by: str = None,
                   status_filter: str = None, search: str = None):
    """List download history with optional filters."""
    if search:
        rows = search_history(search, limit=limit)
    else:
        rows = get_history(limit=limit, platform=filter_by, status=status_filter)

    if not rows:
        info("No downloads found.")
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
        from datetime import datetime
        ts = r.get("downloaded_at", 0)
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
        size = fmt_size(r.get("file_size", 0))
        status = r.get("status", "?")
        status_style = "[green]" if status == "completed" else "[red]" if status == "failed" else "[yellow]"

        table.add_row(
            str(r.get("id", "?")),
            r.get("title", "?")[:40],
            r.get("platform", "?"),
            size,
            date_str,
            status_style + status + "[/]" if status != "completed" else status,
        )

    console.print(table)
    info(f"Showing {len(rows)} downloads")


def show_stats():
    """Show download statistics."""
    stats = get_history_stats()

    from smart_dl.utils import fmt_size, fmt_dur

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


def cleanup_downloads(dry_run: bool = False):
    """Remove failed/incomplete downloads."""
    from smart_dl.core.history import get_history, _get_conn

    rows = get_history(status="failed", limit=10000)
    if not rows:
        info("No failed downloads to clean up.")
        return

    files_to_remove = []
    for r in rows:
        fp = r.get("file_path", "")
        if fp and os.path.isfile(fp):
            files_to_remove.append(fp)

    if not files_to_remove:
        info("No files to clean up.")
        return

    if dry_run:
        info(f"Would remove {len(files_to_remove)} files:")
        for f in files_to_remove[:20]:
            info(f"  {f}")
        if len(files_to_remove) > 20:
            info(f"  ... and {len(files_to_remove) - 20} more")
        return

    removed = 0
    for f in files_to_remove:
        try:
            os.remove(f)
            removed += 1
        except Exception:
            pass

    success(f"Removed {removed}/{len(files_to_remove)} files")
