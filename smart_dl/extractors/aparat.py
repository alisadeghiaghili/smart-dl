"""Aparat extractor — native support for Aparat videos and playlists."""
import re
from urllib.parse import urlparse

import requests
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

from smart_dl.core.proxy import get_current_proxy
from smart_dl.ui import console, error, info, print_section, warn
from smart_dl.ui.progress import stop_event

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


def _extract_aparat_id(url):
    """Extract video ID from Aparat URL."""
    parsed = urlparse(url)
    path = parsed.path
    # Aparat URLs: /v/VIDEOID or /v/VIDEOID/title
    match = re.search(r'/v/(\w+)', path)
    if match:
        return match.group(1)
    return None


def _extract_aparat_playlist_id(url):
    """Extract playlist ID from Aparat URL."""
    parsed = urlparse(url)
    path = parsed.path
    # /playlist/PLAYLISTID or /playlist/PLAYLISTID/title
    match = re.search(r'/playlist/(\w+)', path)
    if match:
        return match.group(1)
    # Also check query param: ?playlist=ID
    qs = parsed.query
    match = re.search(r'playlist=(\w+)', qs)
    if match:
        return match.group(1)
    return None


def get_aparat_info(url):
    """Fetch Aparat video metadata via API."""
    video_id = _extract_aparat_id(url)
    if not video_id:
        return None

    # Try multiple API endpoints
    api_urls = [
        f"https://api.aparat.com/api/video/videoinfo/v1/videoHash/{video_id}",
        f"https://api.aparat.com/api/video/videoinfo/v1/videoId/{video_id}",
    ]

    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None

    for api_url in api_urls:
        try:
            resp = requests.get(api_url, timeout=15, proxies=proxies,
                              headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            data = resp.json()
            if data.get("data"):
                return data["data"]
        except Exception:
            continue

    return None


def get_aparat_playlist_info(url):
    """Fetch Aparat playlist metadata via API."""
    playlist_id = _extract_aparat_playlist_id(url)
    if not playlist_id:
        return None

    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None

    api_url = f"https://api.aparat.com/api/playlist/playlistinfo/v1/playlistId/{playlist_id}"
    try:
        resp = requests.get(api_url, timeout=15, proxies=proxies,
                          headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = resp.json()
        if data.get("data"):
            return data["data"]
    except Exception:
        pass

    return None


def is_aparat_playlist(url):
    """Check if URL is an Aparat playlist."""
    parsed = urlparse(url)
    return "aparat.com" in parsed.netloc and (
        "/playlist/" in parsed.path.lower() or
        "playlist=" in parsed.query.lower()
    )


def download_aparat(url, out_folder):
    """Download Aparat video with quality selection."""
    print_section(t("analyzing_aparat"), "\U0001f3ac")

    # Try native API first for better quality info
    aparat_info = get_aparat_info(url)

    # Use yt-dlp for actual download (it handles Aparat)
    from smart_dl.extractors.youtube import download_yt, get_yt_formats, yt_quality_menu

    info_dict = get_yt_formats(url)
    if info_dict:
        # Show Aparat-specific info if available
        if aparat_info:
            _show_aparat_info(aparat_info)

        fmt, is_audio = yt_quality_menu(info_dict)
        if fmt is not None:
            download_yt(url, out_folder, fmt, is_audio)
        return

    error("Could not extract video from this Aparat URL.")
    info("Make sure the URL is valid and the video is public.")


def _show_aparat_info(aparat_info):
    """Display Aparat video info panel."""
    title = aparat_info.get("title", "?")
    owner = aparat_info.get("owner", {}).get("name", "?") if isinstance(aparat_info.get("owner"), dict) else "?"
    views = aparat_info.get("view", 0)
    likes = aparat_info.get("like", 0)
    duration = aparat_info.get("sabka", 0)  # duration in seconds

    views_s = "{:,}".format(views) if views else "?"
    likes_s = "{:,}".format(likes) if likes else "?"

    from smart_dl.utils import fmt_dur
    dur_s = fmt_dur(duration) if duration else "?"

    body = (
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Channel:[/dim] [cyan]" + owner + "[/cyan]   "
        "[dim]Duration:[/dim] [green]" + dur_s + "[/green]   "
        "[dim]Views:[/dim] [yellow]" + views_s + "[/yellow]   "
        "[dim]Likes:[/dim] [magenta]" + likes_s + "[/magenta]"
    )
    console.print(Panel(body, border_style="cyan", title="[bold]Aparat Video[/bold]", padding=(0,2)))


def handle_aparat_playlist(url, out_folder):
    """Handle Aparat playlist download with native API support."""
    print_section(t("analyzing_playlist"), "\U0001f4cb")

    # Try native API first
    playlist_data = get_aparat_playlist_info(url)

    if playlist_data and playlist_data.get("videos"):
        _download_aparat_playlist_native(playlist_data, out_folder)
        return

    # Fallback: use yt-dlp
    from smart_dl.extractors.youtube import handle_playlist
    info("Using yt-dlp for Aparat playlist...")
    handle_playlist(url, out_folder)


def _download_aparat_playlist_native(playlist_data, out_folder):
    """Download Aparat playlist using native API data."""
    title = playlist_data.get("title", "Aparat Playlist")
    videos = playlist_data.get("videos", [])
    total = len(videos)

    if total == 0:
        error("Playlist is empty.")
        return

    console.print(Panel(
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Videos:[/dim] [cyan]" + str(total) + "[/cyan]",
        border_style="cyan", title="[bold cyan] Aparat Playlist[/bold cyan]", padding=(0,2)
    ))

    # Ask for quality mode
    t_menu = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
    t_menu.add_column(style="bold cyan", width=4, justify="right")
    t_menu.add_column(style="white")
    t_menu.add_column(style="dim")
    t_menu.add_row("1", "Same quality for all",   "Choose once \u2014 download all")
    t_menu.add_row("2", "Best quality (auto)",     "Download best available for each")
    t_menu.add_row("0", "Cancel", "")
    console.print(Panel(t_menu, title="[bold cyan]  Download Mode[/bold cyan]",
                        border_style="cyan", padding=(0,1)))
    mode = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="2").strip()
    if mode == "0":
        return

    skipped = []
    for i, video in enumerate(videos, 1):
        if stop_event.is_set():
            break

        vid_id = video.get("id") or video.get("hash", "")
        vid_title = video.get("title", f"Video {i}")

        # Build URL from ID
        vid_url = f"https://www.aparat.com/v/{vid_id}"

        console.print()
        console.print(Rule(
            "[dim cyan]" + str(i) + "/" + str(total) + "  \u2014  " + vid_title[:60] + "[/dim cyan]",
            style="dim"
        ))

        try:
            # Use yt-dlp for download
            from smart_dl.extractors.youtube import download_yt
            fmt = "bestvideo+bestaudio/best" if mode == "2" else None
            if mode == "1" and i == 1:
                # Ask quality on first video
                from smart_dl.extractors.youtube import get_yt_formats, yt_quality_menu
                vid_info = get_yt_formats(vid_url)
                if vid_info:
                    fmt, _ = yt_quality_menu(vid_info)
                else:
                    warn("Could not fetch formats, using best quality.")
                    fmt = "bestvideo+bestaudio/best"

            if fmt:
                download_yt(vid_url, out_folder, fmt)
        except Exception as e:
            warn("Skipped: " + str(e)[:80])
            skipped.append((i, vid_title, str(e)[:80]))

    # Summary
    console.print()
    done = total - len(skipped)
    console.print(Panel(
        "[bold green]\u2713  " + str(done) + "/" + str(total) + " videos downloaded[/bold green]",
        border_style="green", title="[bold green]  Playlist Complete[/bold green]", padding=(0,2)
    ))

    if skipped:
        console.print()
        warn(str(len(skipped)) + " video(s) failed.")
        for idx, vtitle, reason in skipped:
            info(str(idx) + ". " + vtitle[:55] + " \u2014 " + reason[:50])
