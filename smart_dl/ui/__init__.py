"""UI package — console, panels, progress bars."""
from rich.console import Console
from rich.rule import Rule

console = Console(highlight=False)


def success(msg):
    console.print("[bold green]  \u2713  " + msg + "[/bold green]")

def warn(msg):
    console.print("[yellow]  \u26a0  " + msg + "[/yellow]")

def error(msg):
    console.print("[bold red]  \u2717  " + msg + "[/bold red]")

def info(msg):
    console.print("[dim]  \u00b7  " + msg + "[/dim]")

def print_section(title, icon=""):
    console.print()
    console.print(Rule("[bold cyan]" + icon + "  " + title + "[/bold cyan]", style="cyan"))
