"""Main entry point — the interactive download loop."""
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

import smart_dl.ui.progress as _prog_mod
from smart_dl.core.cookies import cookie_settings_menu
from smart_dl.core.installer import install_menu
from smart_dl.core.proxy import proxy_menu, proxy_step
from smart_dl.core.retry import diagnose_error
from smart_dl.extractors.aparat import download_aparat, handle_aparat_playlist
from smart_dl.extractors.general import detect_platform
from smart_dl.extractors.podcast import handle_podcast
from smart_dl.extractors.youtube import download_yt, get_yt_formats, handle_playlist, yt_quality_menu
from smart_dl.settings import settings_menu
from smart_dl.ui import console, error, info, print_section, success, warn
from smart_dl.ui.logo import bye, print_header
from smart_dl.ui.progress import stop_event
from smart_dl.utils import is_aparat_url, is_playlist_url, is_podcast_url, is_youtube_url


def _pick_output_folder():
    """Let user choose output directory."""
    default = Path.home() / "Downloads" / "SmartDL"
    console.print()
    console.print(Panel(
        "[dim]  Default folder:[/dim]\n    [bold cyan]" + str(default) + "[/bold cyan]\n\n"
        "    Press [bold]Enter[/bold] to accept the default\n"
        "    or type a new path to change it.",
        title="[bold]  Output Folder[/bold]", border_style="white", padding=(0,2)
    ))
    while True:
        raw = Prompt.ask("  [bold]\U0001f4c1 Path[/bold]", default=str(default)).strip()
        p = Path(raw)
        try:
            p.mkdir(parents=True, exist_ok=True)
            files = list(p.iterdir())
            if files:
                info("Folder exists \u2014 " + str(len(files)) + " file(s) inside")
            success("Output folder: " + str(p))
            return p
        except Exception as e:
            error("Cannot use that folder: " + str(e))


def main():
    """Main interactive loop."""
    print_header()

    console.print(Panel(
        "\n"
        "  [bold cyan]YouTube[/bold cyan]        Video or playlist URL \u2192 choose video/audio quality\n"
        "  [bold cyan]Aparat[/bold cyan]         Iranian video platform \u2192 videos + playlists\n"
        "  [bold cyan]Podcast[/bold cyan]        Direct MP3 link | RSS feed | SoundCloud | ...\n"
        "  [bold cyan]Stop[/bold cyan]           Ctrl+C \u2014 partial file is saved and resumable\n"
        "  [bold cyan]P / p[/bold cyan]          Open proxy settings at any URL prompt\n"
        "  [bold cyan]S / s[/bold cyan]          Open download settings (retries, fragment threads)\n"
        "  [bold cyan]C / c[/bold cyan]          Cookie settings (browser auth for bot detection)\n"
        "  [bold cyan]I / i[/bold cyan]          Install dependencies (ffmpeg, Node.js)\n"
        "\n",
        title="[bold]  Quick Guide[/bold]", border_style="white", padding=(0,2)
    ))

    try:
        out_folder = _pick_output_folder()
        proxy_step()
    except (KeyboardInterrupt, EOFError):
        bye()
        return

    while True:
        stop_event.clear()
        _prog_mod._no_internet_shown = False
        console.print()
        console.print(Rule(style="dim"))
        console.print()
        try:
            url = Prompt.ask(
                "  [bold cyan]\U0001f517 URL[/bold cyan] "
                "[dim](q = quit  \u00b7  p = proxy  \u00b7  s = settings  \u00b7  i = install  \u00b7  c = cookies)[/dim]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            bye()
            return

        if url.lower() == "q":
            bye()
            break

        if url.lower() == "p":
            proxy_menu()
            continue

        if url.lower() == "s":
            settings_menu()
            continue

        if url.lower() == "i":
            install_menu()
            continue

        if url.lower() == "c":
            cookie_settings_menu()
            continue

        if not url.startswith(("http://","https://","ftp://")):
            warn("Not a valid URL. Start with http:// or https://")
            continue

        try:
            if is_playlist_url(url):
                if is_aparat_url(url):
                    handle_aparat_playlist(url, out_folder)
                else:
                    handle_playlist(url, out_folder)

            elif is_aparat_url(url):
                download_aparat(url, out_folder)

            elif is_youtube_url(url):
                print_section("Analyzing YouTube link", "\U0001f3a5")
                vid_info = get_yt_formats(url)
                if vid_info:
                    fmt, is_audio = yt_quality_menu(vid_info)
                    if fmt is not None:
                        download_yt(url, out_folder, fmt, is_audio)

            elif is_podcast_url(url):
                handle_podcast(url, out_folder)

            else:
                # Generic: try yt-dlp, then check if it's a podcast
                print_section("Analyzing video", "\U0001f50d")
                platform = detect_platform(url)
                if platform:
                    info("Detected platform: " + platform)
                vid_info = get_yt_formats(url)
                if vid_info:
                    fmt, is_audio = yt_quality_menu(vid_info)
                    if fmt is not None:
                        download_yt(url, out_folder, fmt, is_audio)
                elif vid_info is None and not _prog_mod._no_internet_shown:
                    try:
                        import requests
                        ct = ""
                        resp = requests.head(url, timeout=10, allow_redirects=True)
                        ct = resp.headers.get("Content-Type", "")
                    except Exception:
                        pass
                    if is_podcast_url(url, ct=ct):
                        handle_podcast(url, out_folder)
                    else:
                        error("Cannot handle this URL \u2014 yt-dlp could not extract any media.")
        except KeyboardInterrupt:
            warn("Interrupted.")
        except Exception as e:
            _estr = str(e)
            _emsg = _estr.lower()
            if any(x in _emsg for x in ["getaddrinfo", "failed to resolve",
                                          "network is unreachable", "transporterror"]):
                pass
            elif any(x in _emsg for x in ["connection", "timeout", "unreachable"]):
                console.print(Panel(
                    "[bold red]\u2717  Network error[/bold red]\n\n"
                    "  Check your internet connection or proxy settings (press [bold]P[/bold]).",
                    border_style="red", title="[bold red] Connection Error[/bold red]",
                    padding=(0, 2)
                ))
            else:
                hint = diagnose_error(e)
                console.print(Panel(
                    "[bold red]\u2717  " + _estr[:200] + "[/bold red]"
                    + ("\n\n  [dim]" + hint + "[/dim]" if hint else ""),
                    border_style="red", title="[bold red] Error[/bold red]",
                    padding=(0, 2)
                ))

        console.print()
        while True:
            try:
                again = Prompt.ask(
                    " [bold yellow]Download another?[/bold yellow] [dim](y / n)[/dim]",
                    default="y"
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                bye()
                return
            if again in ("", "y", "n"):
                break
            warn("Please enter y or n.")
        if again == "n":
            bye()
            break
