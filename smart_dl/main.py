"""Main entry point — the interactive download loop."""

from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

import smart_dl.ui.progress as _prog_mod
from smart_dl.core.cookies import cookie_settings_menu
from smart_dl.core.installer import install_menu
from smart_dl.core.paths import get_default_download_dir
from smart_dl.core.proxy import proxy_menu, proxy_step
from smart_dl.core.retry import diagnose_error
from smart_dl.extractors.aparat import download_aparat, handle_aparat_playlist
from smart_dl.extractors.courses import download_course, is_course_url
from smart_dl.extractors.education import (
    download_education_course,
    is_education_url,
)
from smart_dl.extractors.general import detect_platform
from smart_dl.extractors.podcast import handle_podcast
from smart_dl.extractors.youtube import (
    download_yt,
    get_yt_formats,
    handle_playlist,
    yt_quality_menu,
)
from smart_dl.lang import t
from smart_dl.settings import settings_menu
from smart_dl.ui import console, error, info, print_section, success, warn
from smart_dl.ui.logo import bye, print_header
from smart_dl.ui.progress import stop_event
from smart_dl.utils import (
    is_aparat_url,
    is_http_url,
    is_playlist_url,
    is_podcast_url,
    is_youtube_url,
)


def _pick_output_folder() -> Path:
    """Let the user choose the output directory.

    Returns
    -------
    pathlib.Path
        Selected directory (created if missing).
    """
    default = get_default_download_dir()
    console.print()
    console.print(
        Panel(
            "[dim]  "
            + t("default_folder")
            + "[/dim]\n    [bold cyan]"
            + str(default)
            + "[/bold cyan]\n\n"
            "    Press [bold]Enter[/bold] to accept the default\n"
            "    or type a new path to change it.",
            title="[bold]  " + t("output_folder") + "[/bold]",
            border_style="white",
            padding=(0, 2),
        )
    )
    while True:
        raw = Prompt.ask("  [bold]\U0001f4c1 Path[/bold]", default=str(default)).strip()
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            files = list(path.iterdir())
            if files:
                info(t("folder_exists") + " " + str(len(files)) + " " + t("folder_files"))
            success(t("output_set") + " " + str(path))
            return path
        except Exception as exc:
            error("Cannot use that folder: " + str(exc))


def main() -> None:
    """Run the interactive download loop."""
    print_header()

    console.print(
        Panel(
            "\n"
            "  [bold cyan]YouTube[/bold cyan]        "
            + t("guide_youtube")
            + "\n"
            "  [bold cyan]Aparat[/bold cyan]         "
            + t("guide_aparat")
            + "\n"
            "  [bold cyan]Podcast[/bold cyan]        "
            + t("guide_podcast")
            + "\n"
            "  [bold cyan]Stop[/bold cyan]           "
            + t("guide_stop")
            + "\n"
            "  [bold cyan]P / p[/bold cyan]          "
            + t("guide_proxy")
            + "\n"
            "  [bold cyan]S / s[/bold cyan]          "
            + t("guide_settings")
            + "\n"
            "  [bold cyan]C / c[/bold cyan]          "
            + t("guide_cookies")
            + "\n"
            "  [bold cyan]I / i[/bold cyan]          "
            + t("guide_install")
            + "\n"
            "\n",
            title="[bold]  " + t("guide_title") + "[/bold]",
            border_style="white",
            padding=(0, 2),
        )
    )

    try:
        out_folder = _pick_output_folder()
        proxy_step()
    except (KeyboardInterrupt, EOFError):
        bye()
        return

    while True:
        stop_event.clear()
        _prog_mod.reset_no_internet("")
        console.print()
        console.print(Rule(style="dim"))
        console.print()
        try:
            url = Prompt.ask("  [bold cyan]\U0001f517 " + t("url_prompt") + "[/bold cyan]").strip()
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

        if not is_http_url(url):
            warn(t("invalid_url"))
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
                print_section(t("analyzing_youtube"), "\U0001f3a5")
                vid_info = get_yt_formats(url)
                if vid_info:
                    fmt, is_audio = yt_quality_menu(vid_info)
                    if fmt is not None:
                        download_yt(url, out_folder, fmt, is_audio)

            elif is_podcast_url(url):
                handle_podcast(url, out_folder)

            elif is_education_url(url):
                download_education_course(url, out_folder)

            else:
                from smart_dl.extractors.persian import (
                    download_persian_platform,
                    is_persian_platform,
                )

                if is_persian_platform(url):
                    download_persian_platform(url, out_folder)
                elif is_course_url(url):
                    download_course(url, out_folder)
                else:
                    print_section(t("analyzing_video"), "\U0001f50d")
                    platform = detect_platform(url)
                    if platform:
                        info("Detected platform: " + platform)
                    vid_info = get_yt_formats(url)
                    if vid_info:
                        fmt, is_audio = yt_quality_menu(vid_info)
                        if fmt is not None:
                            download_yt(url, out_folder, fmt, is_audio)
                    elif vid_info is None:
                        from urllib.parse import urlparse

                        host = urlparse(url).netloc or url
                        already = host in _prog_mod._no_internet_hosts
                        if not already:
                            try:
                                import requests

                                resp = requests.head(url, timeout=10, allow_redirects=True)
                                ct = resp.headers.get("Content-Type", "")
                            except Exception:
                                ct = ""
                            if is_podcast_url(url, ct=ct):
                                handle_podcast(url, out_folder)
                            else:
                                error(t("cannot_handle"))
        except KeyboardInterrupt:
            warn(t("stopped_by_user"))
        except Exception as exc:
            estr = str(exc)
            emsg = estr.lower()
            if any(
                token in emsg
                for token in (
                    "getaddrinfo",
                    "failed to resolve",
                    "network is unreachable",
                    "transporterror",
                )
            ):
                pass
            elif any(token in emsg for token in ("connection", "timeout", "unreachable")):
                console.print(
                    Panel(
                        "[bold red]✗  " + t("network_error") + "[/bold red]\n\n"
                        "  " + t("network_error_hint"),
                        border_style="red",
                        title="[bold red] " + t("connection_error") + "[/bold red]",
                        padding=(0, 2),
                    )
                )
            else:
                hint = diagnose_error(exc)
                console.print(
                    Panel(
                        "[bold red]✗  " + estr[:200] + "[/bold red]"
                        + ("\n\n  [dim]" + hint + "[/dim]" if hint else ""),
                        border_style="red",
                        title="[bold red] " + t("error") + "[/bold red]",
                        padding=(0, 2),
                    )
                )

        console.print()
        while True:
            try:
                again = (
                    Prompt.ask(
                        " [bold yellow]"
                        + t("download_another")
                        + "[/bold yellow] [dim](y / n)[/dim]",
                        default="y",
                    )
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                bye()
                return
            if again in ("", "y", "n"):
                break
            warn("Please enter y or n.")
        if again == "n":
            bye()
            break
