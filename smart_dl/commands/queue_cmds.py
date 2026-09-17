"""CLI queue command handlers."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

__all__ = ["handle_queue"]


def handle_queue(cmds: Optional[Sequence[str]], download_item: Callable[..., bool]) -> None:
    """Handle ``--queue`` subcommands.

    Parameters
    ----------
    cmds : sequence of str or None
        Subcommand tokens, e.g. ``["add", url1, url2]``.
    download_item : Callable
        Function ``(item, out_folder) -> bool`` used by ``start``.

    Returns
    -------
    None
    """
    from smart_dl.core.queue import (
        add_to_queue,
        clear_queue,
        get_queue,
        get_queue_stats,
        init_db,
        pause_queue,
        process_queue,
        resume_queue,
    )

    init_db()

    if not cmds:
        from smart_dl.ui import warn

        warn("Usage: --queue add URL... | start | pause | resume | list | stats | clear")
        return

    action = cmds[0].lower()

    if action == "add":
        urls = list(cmds[1:])
        if not urls:
            from smart_dl.ui import warn

            warn("Usage: --queue add URL1 URL2 ...")
            return
        count = add_to_queue(urls)
        from smart_dl.ui import success

        success(f"Added {count} URL(s) to queue 📥.")
        return

    if action == "start":
        from smart_dl.core.paths import get_default_download_dir
        from smart_dl.ui import info, success
        from smart_dl.ui.progress import stop_event

        out_folder = get_default_download_dir()
        out_folder.mkdir(parents=True, exist_ok=True)
        info(f"Processing queue → {out_folder}")

        result = process_queue(
            lambda item: download_item(item, out_folder),
            should_stop=stop_event.is_set,
        )
        success(
            f"Queue done: {result['completed']} ok, {result['failed']} failed"
            + (", stopped early" if result["stopped"] else "")
        )
        return

    if action == "pause":
        from smart_dl.ui import info
        from smart_dl.ui.progress import stop_event

        stop_event.set()
        paused = pause_queue()
        info(f"Pause requested; {paused} active item(s) marked paused.")
        return

    if action == "resume":
        from smart_dl.ui import info
        from smart_dl.ui.progress import stop_event

        stop_event.clear()
        resumed = resume_queue()
        info(f"Resumed {resumed} paused item(s). Re-run --queue start to process.")
        return

    if action == "list":
        items = get_queue()
        if not items:
            print("Queue is empty.")
            return
        from rich import box
        from rich.table import Table

        from smart_dl.ui import console

        table = Table(box=box.ROUNDED, show_header=True, border_style="cyan")
        table.add_column("#", width=5)
        table.add_column("URL", max_width=50)
        table.add_column("Status", width=10)
        table.add_column("Priority", width=8)
        for item in items:
            status_style = {
                "pending": "[yellow]",
                "active": "[cyan]",
                "completed": "[green]",
                "failed": "[red]",
                "paused": "[magenta]",
            }.get(item["status"], "")
            table.add_row(
                str(item["id"]),
                item["url"][:50],
                status_style + item["status"] + "[/]",
                str(item["priority"]),
            )
        console.print(table)
        return

    if action == "clear":
        clear_queue()
        from smart_dl.ui import success

        success("Queue cleared 🧹.")
        return

    if action == "stats":
        stats = get_queue_stats()
        from smart_dl.ui import console

        console.print(
            f"📊 [bold cyan]Queue Stats:[/bold cyan] {stats['total']} total, "
            f"[yellow]{stats['pending']} pending[/yellow], "
            f"[blue]{stats['active']} active[/blue], "
            f"[green]{stats['completed']} completed[/green], "
            f"[red]{stats['failed']} failed[/red], "
            f"[magenta]{stats.get('paused', 0)} paused[/magenta]"
        )
        return

    from smart_dl.ui import warn

    warn("Unknown queue command. Usage: --queue add|start|pause|resume|list|stats|clear")
