"""CLI history command handlers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

__all__ = ["handle_history"]


def handle_history(cmds: Optional[Sequence[str]]) -> None:
    """Handle ``--history`` subcommands.

    Parameters
    ----------
    cmds : sequence of str or None
        Subcommand tokens, e.g. ``["search", "keyword"]``.

    Returns
    -------
    None
    """
    from smart_dl.core.history import init_db

    init_db()

    if not cmds:
        from smart_dl.ui import warn

        warn("Usage: --history list | search QUERY | stats | re-download ID")
        return

    action = cmds[0].lower()

    if action == "list":
        from smart_dl.core.manager import list_downloads

        list_downloads()
        return

    if action == "search":
        query = " ".join(cmds[1:])
        if not query:
            print("Usage: --history search KEYWORD")
            return
        from smart_dl.core.manager import list_downloads

        list_downloads(search=query)
        return

    if action == "stats":
        from smart_dl.core.manager import show_stats

        show_stats()
        return

    if action == "re-download":
        if len(cmds) < 2:
            print("Usage: --history re-download ID")
            return
        try:
            hist_id = int(cmds[1])
        except ValueError:
            print("Invalid ID.")
            return
        from smart_dl.core.history import get_history_by_id
        from smart_dl.extractors.youtube import download_yt
        from smart_dl.ui import info

        entry = get_history_by_id(hist_id)
        if not entry:
            print(f"History entry {hist_id} not found.")
            return
        info(f"Re-downloading: {entry['title']}")
        download_yt(
            entry["url"],
            Path.home() / "Downloads" / "SmartDL",
            "bestvideo+bestaudio/best",
        )
        return

    from smart_dl.ui import warn

    warn("Unknown history command. Usage: --history list|search|stats|re-download")
