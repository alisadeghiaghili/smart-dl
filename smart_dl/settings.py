"""Download settings — retry count, fragment threads."""
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.padding import Padding
from rich import box

from smart_dl.ui import console, success, warn

DL_SETTINGS = {
    "max_retries":   999,   # 0 = infinite
    "fragments":     4,     # concurrent fragment downloads (1-16)
}


def settings_menu():
    """Interactive download settings menu."""
    while True:
        console.print()
        r = DL_SETTINGS["max_retries"]
        f = DL_SETTINGS["fragments"]
        retry_label = "infinite" if r >= 999 else str(r)
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_row("1", "Max retries      [dim](current: [bold]" + retry_label + "[/bold]  \u00b7  default: infinite)[/dim]")
        t.add_row("2", "Fragment threads [dim](current: [bold]" + str(f) + "[/bold]  \u00b7  default: 4  \u00b7  range: 1-16)[/dim]")
        t.add_row("0", "Back")
        console.print(Panel(t, title="[bold cyan]  Download Settings[/bold cyan]",
                            border_style="cyan", padding=(0,1)))
        console.print(Padding(
            "[dim]  Tip: default values work best for most connections \u2014 "
            "change only if you know what you\'re doing.[/dim]", (0,2)))
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break

        elif ch == "1":
            console.print(Padding(
                "[dim]  Enter 0 or 999 for infinite retries.[/dim]", (0,2)))
            val = Prompt.ask(
                "  [bold yellow]Max retries[/bold yellow] [dim](default: 999 = infinite)[/dim]",
                default="999"
            ).strip()
            if val.isdigit():
                DL_SETTINGS["max_retries"] = int(val) if int(val) < 999 else 999
                lbl = "infinite" if DL_SETTINGS["max_retries"] >= 999 else str(DL_SETTINGS["max_retries"])
                success("Max retries set to: " + lbl)
            else:
                warn("Invalid value \u2014 keeping current setting.")

        elif ch == "2":
            console.print()
            console.print(Panel(
                "[bold yellow]  Recommendation:[/bold yellow] keep between [bold]2[/bold] and [bold]8[/bold].\n\n"
                "  [dim]\u00b7 Too low  (1-2) \u2192 slower downloads, especially on unstable connections.\n"
                "  \u00b7 Optimal  (3-6) \u2192 best balance for most networks including weak/mobile.\n"
                "  \u00b7 High     (8+)  \u2192 may cause rate-limiting or errors on some servers.\n"
                "  \u00b7 Max     (16)   \u2012 not recommended; often counterproductive.[/dim]",
                border_style="yellow", title="[bold yellow]  Fragment Threads[/bold yellow]", padding=(0,2)
            ))
            val = Prompt.ask(
                "  [bold yellow]Fragment threads[/bold yellow] [dim](1-16, default: 4)[/dim]",
                default="4"
            ).strip()
            if val.isdigit() and 1 <= int(val) <= 16:
                DL_SETTINGS["fragments"] = int(val)
                if int(val) > 8:
                    warn("Value " + val + " is high \u2014 this may cause rate-limiting on some servers.")
                success("Fragment threads set to: " + val)
            else:
                warn("Invalid value \u2014 must be between 1 and 16.")
        else:
            warn("Invalid selection.")
