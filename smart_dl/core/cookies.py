"""Browser cookie authentication for YouTube bot detection."""
import sys
import webbrowser
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

from smart_dl.ui import console, success, warn, error, info, print_section
from smart_dl.core.config import load_config, save_config

BROWSERS_TO_TRY = ["firefox", "edge", "chrome", "chromium", "brave"]


class SilentLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def get_cookie_browser() -> str:
    return load_config().get("cookie_browser", "")

def set_cookie_browser(browser: str):
    cfg = load_config()
    cfg["cookie_browser"] = browser
    save_config(cfg)

def clear_cookie_browser():
    cfg = load_config()
    cfg["cookie_browser"] = ""
    save_config(cfg)


def try_browser_cookies(url: str, ydl_opts: dict, browser: str) -> bool:
    """
    Returns True  -> browser found + logged in -> cookies injected into ydl_opts
    Returns False -> browser found but video still blocked (not logged in)
    Raises        -> browser not installed / permission / keyring error
    """
    import yt_dlp
    test_opts = {k: v for k, v in ydl_opts.items()}
    test_opts["cookiesfrombrowser"] = (browser, None, None, None)
    test_opts["quiet"] = True
    test_opts["no_warnings"] = True
    test_opts["logger"] = SilentLogger()
    try:
        with yt_dlp.YoutubeDL(test_opts) as ydl:
            ydl.extract_info(url, download=False)
        ydl_opts["cookiesfrombrowser"] = (browser, None, None, None)
        return True
    except yt_dlp.utils.DownloadError as _e:
        _em = str(_e).lower()
        if "challenge solving failed" in _em or "requested format is not available" in _em or "only images are available" in _em:
            raise RuntimeError("js_challenge")
        return False
    except Exception:
        raise


def handle_bot_detection(url: str, ydl_opts: dict) -> bool:
    """Handle YouTube bot detection by trying browser cookies."""
    from smart_dl.core.installer import fix_youtube_deps
    console.print()
    console.print(Panel(
        "[bold yellow]\u26a0  YouTube is asking for a sign-in / bot check.[/bold yellow]\n\n"
        "  SmartDL will fix this by reading cookies directly\n"
        "  from your browser \u2014 [bold]no extension or export needed[/bold].\n\n"
        "  [dim]\u00b7 Firefox and Edge work best on Windows\n"
        "  \u00b7 Chrome may not work due to Google's encryption[/dim]",
        border_style="yellow",
        title="[bold yellow] Bot Detection[/bold yellow]",
        padding=(0, 2)
    ))

    saved = get_cookie_browser()
    if saved:
        info("Trying saved browser: " + saved.capitalize() + "...")
        if try_browser_cookies(url, ydl_opts, saved):
            success("Fixed via " + saved.capitalize() + " cookies.")
            return True
        warn("Saved browser (" + saved.capitalize() + ") didn't work \u2014 trying others...")

    info("Scanning installed browsers for a logged-in YouTube session...")
    any_browser_found = False
    js_challenge_hit = False
    _js_challenge_browser = ""
    for browser in BROWSERS_TO_TRY:
        if browser == saved:
            continue
        try:
            sys.stdout.write(" \u00b7 " + browser.capitalize() + "... ")
            sys.stdout.flush()
            result = try_browser_cookies(url, ydl_opts, browser)
            if result:
                sys.stdout.write("\u2713\n")
                sys.stdout.flush()
                set_cookie_browser(browser)
                success("Fixed via " + browser.capitalize() + " \u2014 saved for future use.")
                return True
            else:
                sys.stdout.write("\u2717 (not logged in)\n")
                sys.stdout.flush()
                any_browser_found = True
        except RuntimeError as _rte:
            if str(_rte) == "js_challenge":
                sys.stdout.write("\u2713 (cookies ok \u2014 Node.js missing)\n")
                sys.stdout.flush()
                set_cookie_browser(browser)
                _js_challenge_browser = browser
                any_browser_found = True
                js_challenge_hit = True
            else:
                sys.stdout.write("\u2717 (not found)\n")
                sys.stdout.flush()
        except Exception:
            sys.stdout.write("\u2717 (not found)\n")
            sys.stdout.flush()

    if js_challenge_hit:
        console.print()
        console.print(Panel(
            "[bold yellow]\u26a0 Cookies found in " + _js_challenge_browser.capitalize() + ", but Node.js is missing.[/bold yellow]\n\n"
            " YouTube's bot check requires a JavaScript runtime to solve challenges.\n"
            " [dim]Without it, only thumbnails are available \u2014 no video or audio.[/dim]",
            border_style="yellow",
            title="[bold yellow] Node.js Required[/bold yellow]",
            padding=(0, 2)
        ))
        ans = Prompt.ask(
            " [bold yellow]Install Node.js now?[/bold yellow] [dim](y / n)[/dim]",
            default="y"
        ).strip().lower()
        if ans != "n":
            fix_youtube_deps()
            console.print()
            console.print(Panel(
                "[bold green] Node.js installation attempted.[/bold green]\n\n"
                " [bold]Next steps:[/bold]\n\n"
                " [bold]1.[/bold] Close this window completely\n"
                " [bold]2.[/bold] Reopen SmartDL\n"
                " [bold]3.[/bold] Paste the same URL again\n\n"
                " [dim]PATH needs to refresh for Node.js to be recognized.[/dim]",
                border_style="green",
                title="[bold green] Almost there![/bold green]",
                padding=(0, 2)
            ))
        return False

    if not any_browser_found:
        console.print()
        console.print(Panel(
            "[bold red] No compatible browser found on this system.[/bold red]\n\n"
            "  Install [bold]Firefox[/bold] or [bold]Edge[/bold], sign in to YouTube,\n"
            "  then try downloading again.",
            border_style="red",
            title="[bold red] No Browser Found[/bold red]",
            padding=(0, 2)
        ))
        return False

    ans = Prompt.ask(
        "  [bold yellow]Would you like to fix YouTube dependencies (yt-dlp + Node.js)?[/bold yellow] [dim](y / n)[/dim]",
        default="y"
    ).strip().lower()
    if ans == "y":
        fix_youtube_deps()
        return False

    console.print()
    console.print(Panel(
        "[bold cyan] No logged-in browser found.[/bold cyan]\n\n"
        "  SmartDL will open YouTube in your browser.\n"
        "  Please [bold]sign in[/bold] to your Google account, then come back here.",
        border_style="cyan",
        title="[bold cyan] Action Required[/bold cyan]",
        padding=(0, 2)
    ))

    t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 2))
    t.add_column(style="bold cyan", width=4, justify="right")
    t.add_column(style="white")
    t.add_column(style="dim")
    for i, b in enumerate(BROWSERS_TO_TRY, 1):
        note = ("[yellow]may not work \u2014 Google encrypts Chrome cookies on Windows[/yellow]"
                if b == "chrome" else "")
        t.add_row(str(i), b.capitalize(), note)
    t.add_row("0", "Cancel", "")
    console.print(Panel(t,
        title="[bold cyan] Which browser will you use?[/bold cyan]",
        border_style="cyan", padding=(0, 1)
    ))

    try:
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()
    except (KeyboardInterrupt, EOFError):
        return False

    if not ch.isdigit() or int(ch) == 0:
        return False
    idx = int(ch) - 1
    if idx >= len(BROWSERS_TO_TRY):
        return False
    chosen = BROWSERS_TO_TRY[idx]

    info("Opening YouTube sign-in page in " + chosen.capitalize() + "...")
    try:
        webbrowser.open("https://accounts.google.com/ServiceLogin?service=youtube")
    except Exception:
        warn("Could not open browser automatically.")
        info("Please manually open YouTube in " + chosen.capitalize() + " and sign in.")

    console.print()
    console.print(Panel(
        "  [bold]1.[/bold] Sign in to your Google account in [bold cyan]"
        + chosen.capitalize() + "[/bold cyan]\n"
        "  [bold]2.[/bold] Come back here and press [bold green]Enter[/bold green]\n\n"
        "  [dim]Keep the browser open \u2014 SmartDL reads cookies from the live session.[/dim]",
        border_style="green",
        title="[bold green] Waiting for login...[/bold green]",
        padding=(0, 2)
    ))

    try:
        Prompt.ask("  [bold yellow]Press Enter when done[/bold yellow]", default="")
    except (KeyboardInterrupt, EOFError):
        return False

    info("Reading cookies from " + chosen.capitalize() + "...")
    if try_browser_cookies(url, ydl_opts, chosen):
        set_cookie_browser(chosen)
        success("Cookies loaded from " + chosen.capitalize() + " \u2014 saved for future downloads.")
        return True

    error("Could not read cookies from " + chosen.capitalize() + ".")
    if chosen == "chrome":
        warn("Chrome encrypts its cookies on Windows \u2014 try Firefox or Edge instead.")
    else:
        warn("Make sure you are fully logged in to YouTube in "
             + chosen.capitalize() + " and try again.")
    return False


def cookie_settings_menu():
    """Interactive cookie browser settings menu."""
    print_section("Cookie Settings", "\U0001f36a")
    current = get_cookie_browser()
    if current:
        console.print(Panel(
            "[bold green] Active:[/bold green] reading cookies from [bold cyan]"
            + current.capitalize() + "[/bold cyan]\n\n"
            "  [dim]Type [bold]clear[/bold] to reset, or press Enter to keep it.[/dim]",
            border_style="green",
            title="[bold green] Browser Cookie Source[/bold green]",
            padding=(0, 2)
        ))
        try:
            ch = Prompt.ask(
                "  [bold yellow]> (Enter to keep / clear to reset)[/bold yellow]",
                default=""
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            return
        if ch == "clear":
            clear_cookie_browser()
            success("Cookie browser cleared.")
        else:
            info("Keeping: " + current.capitalize())
    else:
        console.print(Panel(
            "  [dim]No browser cookie source is set.\n\n"
            "  This will be configured automatically the next time\n"
            "  YouTube triggers a bot-detection or sign-in error.[/dim]",
            border_style="dim",
            title="[dim] Browser Cookie Source[/dim]",
            padding=(0, 2)
        ))
