"""General extractor — handles any yt-dlp-supported site."""
import yt_dlp
from urllib.parse import urlparse
from rich.panel import Panel

from smart_dl.ui import console, success, warn, error, info, print_section
from smart_dl.ui.progress import stop_event, _progress_ctx, make_progress, yt_hook
from smart_dl.core.proxy import get_current_proxy
from smart_dl.core.cookies import get_cookie_browser
from smart_dl.core.retry import retry_with_backoff
from smart_dl.settings import DL_SETTINGS
from smart_dl.utils import fmt_size, fmt_dur

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


# Known Persian platforms and their yt-dlp extractors
PERSIAN_PLATFORMS = {
    "aparat.com": "Aparat",
    "filimo.com": "Filimo",
    "namasha.com": "Namasha",
    "radiojavan.com": "Radio Javan",
    "music.aparat.com": "Aparat Music",
    "trello.com": "Trello",
    "lenzmovie.com": "LenzMovie",
    "filmio.ir": "Filmio",
    "vidio.com": "Vidio",
    "abornet.ir": "Abornet",
    "aion.iran": "Aion",
    "moshaverfilm.com": "MoshaverFilm",
    "filmnet.com": "FilmNet",
    "hamrahweb.com": "HamrahWeb",
    "30namovies.com": "30NaMovies",
    "mfilm.cc": "MFilm",
    "filmox.org": "Filmox",
    "cinemakhd.com": "CinemaKHD",
    "cinemahez.ir": "CinemaHez",
    "downloadha.com": "DownloadHa",
}


def detect_platform(url):
    """Detect which platform a URL belongs to."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    for platform_domain, platform_name in PERSIAN_PLATFORMS.items():
        if domain == platform_domain or domain.endswith("." + platform_domain):
            return platform_name

    return None


def get_general_info(url):
    """Fetch video info for any yt-dlp-supported site."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    prx = get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx
    saved = get_cookie_browser()
    if saved:
        ydl_opts["cookiesfrombrowser"] = (saved, None, None, None)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        raise


def show_general_info(info_dict):
    """Display info panel for any video."""
    title = info_dict.get("title", "?")
    uploader = info_dict.get("uploader") or info_dict.get("channel") or "?"
    duration = fmt_dur(info_dict.get("duration"))
    views = info_dict.get("view_count")
    views_s = "{:,}".format(views) if views else "?"

    body = (
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Uploader:[/dim] [cyan]" + uploader + "[/cyan]   "
        "[dim]Duration:[/dim] [green]" + duration + "[/green]   "
        "[dim]Views:[/dim] [yellow]" + views_s + "[/yellow]"
    )
    console.print(Panel(body, border_style="cyan", title="[bold]Video Info[/bold]", padding=(0,2)))


def general_quality_menu(info_dict):
    """Quality menu for non-YouTube videos."""
    show_general_info(info_dict)
    fmts = info_dict.get("formats", [])
    if not fmts and info_dict.get("url"):
        fmts = [info_dict]

    from smart_dl.extractors.youtube import yt_quality_menu
    return yt_quality_menu(info_dict)


def download_general(url, out_folder, fmt=None, is_audio=False):
    """Download from any yt-dlp-supported site."""
    from smart_dl.extractors.youtube import get_yt_formats, yt_quality_menu, download_yt

    platform = detect_platform(url)
    platform_str = f" ({platform})" if platform else ""

    print_section(t("analyzing_video") + platform_str, "\U0001f50d")

    info_dict = get_yt_formats(url)
    if info_dict:
        if fmt is None:
            fmt, is_audio = yt_quality_menu(info_dict)
            if fmt is None:
                return

        download_yt(url, out_folder, fmt, is_audio)
    else:
        error("Could not extract video from this URL.")
        if platform:
            info(f"Detected platform: {platform}")
        info("Make sure the URL is valid and the content is public.")


def batch_download(urls, out_folder):
    """Download multiple URLs from a list."""
    from smart_dl.extractors.youtube import download_yt, get_yt_formats, yt_quality_menu
    from smart_dl.utils import is_youtube_url, is_aparat_url, is_podcast_url

    total = len(urls)
    success_list = []
    failed_list = []

    for i, url in enumerate(urls, 1):
        if stop_event.is_set():
            break

        print(f"\n[{i}/{total}] Processing: {url[:80]}...")

        try:
            if is_youtube_url(url) or is_aparat_url(url) or not is_podcast_url(url):
                info_dict = get_yt_formats(url)
                if info_dict:
                    fmt, is_audio = yt_quality_menu(info_dict)
                    if fmt:
                        download_yt(url, out_folder, fmt, is_audio)
                        success_list.append(url)
                    else:
                        failed_list.append((url, "Skipped by user"))
                else:
                    failed_list.append((url, "Could not extract info"))
            else:
                from smart_dl.extractors.podcast import handle_podcast
                handle_podcast(url, out_folder)
                success_list.append(url)
        except Exception as e:
            failed_list.append((url, str(e)[:80]))

    # Summary
    console.print()
    console.print(Panel(
        f"[bold green]\u2713 {len(success_list)}/{total} downloaded successfully[/bold green]"
        + (f"\n[dim]  {len(failed_list)} failed[/dim]" if failed_list else ""),
        border_style="green", title="[bold green]  Batch Complete[/bold green]", padding=(0,2)
    ))

    if failed_list:
        console.print()
        warn("Failed downloads:")
        for url, reason in failed_list:
            info(f"  {url[:60]}... \u2014 {reason}")
