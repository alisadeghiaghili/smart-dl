"""CLI handlers for scheduler (R5) and subscription automation (R6)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

__all__ = ["handle_schedule", "handle_subs_check"]


def _fmt_ts(ts: float) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


def handle_schedule(cmds: Optional[Sequence[str]]) -> None:
    """Handle ``--schedule`` subcommands.

    Commands
    --------
    add URL [--at HH:MM]
        Schedule a URL (default: +2 hours if ``--at`` omitted).
    list
        Show pending jobs.
    clear
        Delete all schedule rows.
    remove ID
        Delete one job.
    start [--once]
        Enqueue due jobs and optionally process the download queue.

    Parameters
    ----------
    cmds : sequence of str or None
        Tokens after ``--schedule``.

    Returns
    -------
    None
    """
    from smart_dl.core import scheduler
    from smart_dl.ui import error, info, success, warn

    tokens = list(cmds or [])
    if not tokens:
        warn(
            "Usage: --schedule add URL [--at HH:MM] | list | clear | remove ID | start [--once]"
        )
        return

    action = tokens[0].lower()

    if action == "add":
        url = None
        run_at = None
        rest = tokens[1:]
        i = 0
        while i < len(rest):
            if rest[i] == "--at" and i + 1 < len(rest):
                run_at = rest[i + 1]
                i += 2
                continue
            if url is None:
                url = rest[i]
            i += 1
        if not url:
            error("Usage: --schedule add URL [--at HH:MM]")
            return
        target = run_at if run_at else "+2h"
        try:
            job_id = scheduler.add_scheduled_url(url, target)
        except ValueError as exc:
            error(str(exc))
            return
        rows = scheduler.get_schedule("pending")
        when = next((r["run_at"] for r in rows if r["id"] == job_id), None)
        success(f"Scheduled #{job_id} at {_fmt_ts(when) if when else '?'} → {url[:80]}")
        return

    if action == "list":
        rows = scheduler.get_schedule("pending")
        if not rows:
            info("Schedule is empty.")
            return
        info(f"{len(rows)} pending job(s):")
        for row in rows:
            info(f"  #{row['id']}  {_fmt_ts(row['run_at'])}  {row['url'][:70]}")
        return

    if action == "clear":
        n = scheduler.clear_schedule()
        success(f"Cleared {n} schedule row(s).")
        return

    if action == "remove":
        if len(tokens) < 2 or not str(tokens[1]).isdigit():
            error("Usage: --schedule remove ID")
            return
        ok = scheduler.remove_scheduled(int(tokens[1]))
        if ok:
            success(f"Removed schedule #{tokens[1]}")
        else:
            error(f"Schedule #{tokens[1]} not found")
        return

    if action == "start":
        result = scheduler.process_due()
        info(f"Schedule due: {result['due']}, enqueued: {result['enqueued']}")
        if "--once" in tokens[1:] or result["enqueued"] == 0:
            if result["enqueued"] == 0:
                info("Nothing due — queue not started.")
            return
        from smart_dl.commands.downloads import queue_download_item
        from smart_dl.commands.queue_cmds import handle_queue

        handle_queue(["start"], queue_download_item)
        return

    warn("Unknown schedule command. Usage: --schedule add|list|clear|remove|start")


def handle_subs_check(*, once: bool = True) -> None:
    """Run subscription update check (automation-friendly).

    Parameters
    ----------
    once : bool, optional
        Reserved for future loop mode; currently always one pass.

    Returns
    -------
    None
    """
    from smart_dl.commands.subscriptions import handle_check_updates

    del once
    handle_check_updates()


WINDOWS_TASK_SNIPPET = r"""
# Windows Task Scheduler — nightly SmartDL check (PowerShell)
# schtasks /Create /TN "SmartDL Night" /SC DAILY /ST 02:30 ^
#   /TR "powershell -NoProfile -WindowStyle Hidden -Command smart-dl --schedule start --once; smart-dl --check-updates"
"""
