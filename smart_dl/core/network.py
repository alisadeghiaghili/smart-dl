"""Network error display and internet connectivity panels."""
from rich.panel import Panel

from smart_dl.ui import console
from smart_dl.ui.progress import mark_no_internet


def show_no_internet_panel(host: str = "www.youtube.com"):
    """Show a one-time-per-host panel explaining the connection error."""
    if not mark_no_internet(host):
        return
    from smart_dl.core.proxy import peek_current_proxy
    prx = peek_current_proxy()
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
