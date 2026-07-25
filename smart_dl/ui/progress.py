"""Progress bar wrapper and yt-dlp progress hook."""
import threading
from pathlib import Path

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from smart_dl.ui import console

# Module-level state shared between yt-dlp hook and progress context
stop_event = threading.Event()
_no_internet_shown = False

_progress_ctx: dict = {"obj": None, "task": None, "last": 0}


def yt_hook(d):
    """yt-dlp progress hook — updates the Rich progress bar."""
    if stop_event.is_set():
        import yt_dlp
        raise yt_dlp.utils.DownloadError("Stopped by user")
    p = _progress_ctx
    if d["status"] == "downloading" and p["obj"] and p["task"] is not None:
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or None
        done  = d.get("downloaded_bytes", 0)
        fname = Path(d.get("filename","")).name
        p["obj"].update(p["task"], completed=done, total=total,
                        description="[cyan]" + fname[:50] + "[/cyan]")
        p["last"] = done
    elif d["status"] == "finished" and p["obj"] and p["task"] is not None:
        t = d.get("total_bytes", p["last"])
        p["obj"].update(p["task"], completed=t, total=t)


def make_progress():
    """Create a Rich Progress bar for downloads."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=32, style="cyan", complete_style="bold green"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )
