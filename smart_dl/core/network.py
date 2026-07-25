"""Network error display and internet connectivity panels."""
from rich.panel import Panel

from smart_dl.ui import console, info
from smart_dl.ui.progress import _no_internet_shown
import smart_dl.ui.progress as _prog_mod


def show_no_internet_panel(host: str = "www.youtube.com"):
    """Show a one-time panel explaining the connection error."""
    if _prog_mod._no_internet_shown:
        return
    _prog_mod._no_internet_shown = True
    from smart_dl.core.proxy import get_current_proxy
    prx = get_current_proxy()
    prx_hint = (
        "\n\n [dim]Active proxy: [cyan]" + prx + "[/cyan]\n"
        " If your proxy is off, press [bold]P[/bold] to clear it.[/dim]"
    ) if prx else (
        "\n\n [dim]No proxy is set.\n"
        " Press [bold cyan]P[/bold cyan] at the URL prompt to configure one.[/dim]"
    )
    console.print()
    console.print(Panel(
        "[bold red]\u2717 Cannot reach [bold]" + host + "[/bold].[/bold red]\n\n"
        " Connection failed \u2014 this usually means:\n\n"
        " [bold]1.[/bold] No internet connection\n"
        " [bold]2.[/bold] Host is blocked (common in Iran / restricted networks)\n"
        " [bold]3.[/bold] Your proxy/VPN is off or misconfigured"
        + prx_hint,
        border_style="red",
        title="[bold red] Connection Error[/bold red]",
        padding=(0, 2)
    ))
