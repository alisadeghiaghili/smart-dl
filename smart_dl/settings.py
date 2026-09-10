"""Download settings — retry count, fragment threads (persisted)."""

from __future__ import annotations

from typing import Any, Dict

from rich import box
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from smart_dl.core.config import load_config, save_config
from smart_dl.ui import console, success, warn

__all__ = ["DL_SETTINGS", "load_dl_settings", "save_dl_settings", "settings_menu"]

_DEFAULTS: Dict[str, Any] = {
    "max_retries": 999,
    "fragments": 4,
}

# In-memory mirror of persisted settings; loaded at import and after saves.
DL_SETTINGS: Dict[str, Any] = dict(_DEFAULTS)


def load_dl_settings() -> Dict[str, Any]:
    """Load download settings from config, merging defaults.

    Returns
    -------
    dict
        Keys ``max_retries`` and ``fragments``.
    """
    cfg = load_config()
    stored = cfg.get("download_settings") or {}
    DL_SETTINGS["max_retries"] = int(stored.get("max_retries", _DEFAULTS["max_retries"]))
    DL_SETTINGS["fragments"] = int(stored.get("fragments", _DEFAULTS["fragments"]))
    return dict(DL_SETTINGS)


def save_dl_settings() -> bool:
    """Persist the current in-memory settings to config.

    Returns
    -------
    bool
        ``True`` if the config write succeeded.
    """
    cfg = load_config()
    cfg["download_settings"] = {
        "max_retries": int(DL_SETTINGS["max_retries"]),
        "fragments": int(DL_SETTINGS["fragments"]),
    }
    return save_config(cfg)


# Initialize from disk on import (safe: missing config → defaults).
load_dl_settings()


def settings_menu() -> None:
    """Interactive download settings menu (persisted on exit of each change)."""
    while True:
        console.print()
        retries = DL_SETTINGS["max_retries"]
        fragments = DL_SETTINGS["fragments"]
        retry_label = "infinite" if retries >= 999 else str(retries)
        table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 2))
        table.add_column(style="bold cyan", width=4, justify="right")
        table.add_column(style="white")
        table.add_row(
            "1",
            "Max retries      [dim](current: [bold]"
            + retry_label
            + "[/bold]  ·  default: infinite)[/dim]",
        )
        table.add_row(
            "2",
            "Fragment threads [dim](current: [bold]"
            + str(fragments)
            + "[/bold]  ·  default: 4  ·  range: 1-16)[/dim]",
        )
        table.add_row("0", "Back")
        console.print(
            Panel(
                table,
                title="[bold cyan]  Download Settings[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        )
        console.print(
            Padding(
                "[dim]  Tip: default values work best for most connections — "
                "change only if you know what you're doing.[/dim]",
                (0, 2),
            )
        )
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break
        if ch == "1":
            console.print(Padding("[dim]  Enter 0 or 999 for infinite retries.[/dim]", (0, 2)))
            val = Prompt.ask(
                "  [bold yellow]Max retries[/bold yellow] [dim](default: 999 = infinite)[/dim]",
                default="999",
            ).strip()
            if val.isdigit():
                DL_SETTINGS["max_retries"] = min(int(val), 999)
                save_dl_settings()
                label = (
                    "infinite"
                    if DL_SETTINGS["max_retries"] >= 999
                    else str(DL_SETTINGS["max_retries"])
                )
                success("Max retries set to: " + label)
            else:
                warn("Invalid value — keeping current setting.")
        elif ch == "2":
            console.print()
            console.print(
                Panel(
                    "[bold yellow]  Recommendation:[/bold yellow] keep between [bold]2[/bold] and [bold]8[/bold].\n\n"
                    "  [dim]· Too low  (1-2) → slower downloads, especially on unstable connections.\n"
                    "  · Optimal  (3-6) → best balance for most networks including weak/mobile.\n"
                    "  · High     (8+)  → may cause rate-limiting or errors on some servers.\n"
                    "  · Max     (16)  – not recommended; often counterproductive.[/dim]",
                    border_style="yellow",
                    title="[bold yellow]  Fragment Threads[/bold yellow]",
                    padding=(0, 2),
                )
            )
            val = Prompt.ask(
                "  [bold yellow]Fragment threads[/bold yellow] [dim](1-16, default: 4)[/dim]",
                default="4",
            ).strip()
            if val.isdigit() and 1 <= int(val) <= 16:
                DL_SETTINGS["fragments"] = int(val)
                save_dl_settings()
                if int(val) > 8:
                    warn(
                        "Value "
                        + val
                        + " is high — this may cause rate-limiting on some servers."
                    )
                success("Fragment threads set to: " + val)
            else:
                warn("Invalid value — must be between 1 and 16.")
        else:
            warn("Invalid selection.")
