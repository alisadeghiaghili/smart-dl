"""CLI interface — argparse for non-interactive mode."""
import argparse
import os
import sys
from pathlib import Path

from smart_dl import VERSION
from smart_dl.extractors.torrent import is_magnet_link, is_torrent_file


def build_parser():
    """Build the argument parser with all features."""
    parser = argparse.ArgumentParser(
        prog="smart-dl",
        description="SmartDL — Resilient media downloader for unstable networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  smart-dl https://youtube.com/watch?v=abc123\n"
            "  smart-dl URL -q best -o ~/Downloads\n"
            "  smart-dl URL --clip 00:01:30-00:05:00\n"
            "  smart-dl URL --audio-only --audio-format flac\n"
            "  smart-dl URL --sponsorblock --embed-metadata\n"
            "  smart-dl URL --subtitles en,fa --embed-subs\n"
            "  smart-dl URL --thumbnail --embed-thumbnail\n"
            "  smart-dl URL --format mkv\n"
            "  smart-dl --batch urls.txt -o ~/Downloads\n"
            "  smart-dl --queue add URL1 URL2 && smart-dl --queue start\n"
            "  smart-dl --subscribe https://youtube.com/@channel\n"
            "  smart-dl --check-updates\n"
            "  smart-dl --history list --sort date\n"
            "  smart-dl --smart-mode on\n"
            "  smart-dl --theme catppuccin\n"
            "  smart-dl https://pixiv.net/artworks/123\n"
            "  smart-dl --torrent magnet:?xt=...\n"
        )
    )

    # Positional
    parser.add_argument("urls", nargs="*", help="URL(s) to download")

    # Output
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output directory (default: ~/Downloads/SmartDL)")
    parser.add_argument("--output-template", type=str, default=None,
                        help="Output filename template (yt-dlp format)")

    # Quality & Format
    parser.add_argument("-q", "--quality", type=str, default="best",
                        help="Quality: best, worst, 720, 1080, 4k, 8k (default: best)")
    parser.add_argument("--format", type=str, default=None,
                        choices=["mp4", "mkv", "webm", "avi", "mov"],
                        help="Output container format")
    parser.add_argument("--clip", type=str, default=None,
                        help="Download segment: START-END (e.g., 00:01:30-00:05:00)")

    # Audio
    parser.add_argument("--audio-only", action="store_true",
                        help="Extract audio only")
    parser.add_argument("--audio-format", type=str, default="mp3",
                        choices=["mp3", "m4a", "opus", "flac", "wav", "vorbis"],
                        help="Audio format (default: mp3)")
    parser.add_argument("--audio-quality", type=str, default="192",
                        help="Audio bitrate in kbps (default: 192)")
    parser.add_argument("--dubbed-langs", type=str, default=None,
                        help="Download dubbed audio tracks (e.g., en,fa,ar)")

    # Subtitles
    parser.add_argument("--subtitles", type=str, default=None,
                        help="Download subtitles (e.g., en,fa or all)")
    parser.add_argument("--list-subs", action="store_true",
                        help="List available subtitles")
    parser.add_argument("--embed-subs", action="store_true",
                        help="Embed subtitles in video")

    # Thumbnails & Metadata
    parser.add_argument("--thumbnail", action="store_true",
                        help="Download thumbnail")
    parser.add_argument("--embed-thumbnail", action="store_true",
                        help="Embed thumbnail in video")
    parser.add_argument("--embed-metadata", action="store_true",
                        help="Embed metadata (title, artist, etc.)")

    # Features
    parser.add_argument("--sponsorblock", action="store_true",
                        help="Skip sponsor segments (SponsorBlock)")
    parser.add_argument("--geo-bypass", type=str, default=None,
                        help="Bypass geo-restriction (country code, e.g., US)")
    parser.add_argument("--impersonate", type=str, default=None,
                        help="Impersonate browser (chrome, firefox, safari)")
    parser.add_argument("--proxy", type=str, default=None,
                        help="Proxy URL (http://host:port or socks5://host:port)")

    # Batches & Queue
    parser.add_argument("--batch", type=str, default=None,
                        help="File containing URLs (one per line)")
    parser.add_argument("--concurrent", type=int, default=1,
                        help="Number of concurrent downloads (default: 1)")

    # Queue management
    parser.add_argument("--queue", nargs="+", metavar="CMD",
                        help="Queue commands: add URL..., start, pause, resume, list, clear")

    # History
    parser.add_argument("--history", nargs="+", metavar="CMD",
                        help="History commands: list, search QUERY, stats, re-download ID")
    parser.add_argument("--list", action="store_true",
                        help="List download history")
    parser.add_argument("--sort", type=str, default="date",
                        choices=["date", "name", "size"],
                        help="Sort order for --list")
    parser.add_argument("--filter", type=str, default=None,
                        help="Filter by platform (youtube, aparat, etc.)")
    parser.add_argument("--export", type=str, default=None,
                        help="Export history to JSON file")
    parser.add_argument("--cleanup", action="store_true",
                        help="Remove failed/incomplete downloads")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done (with --cleanup)")

    # Subscriptions
    parser.add_argument("--subscribe", type=str, default=None,
                        help="Subscribe to channel/playlist URL")
    parser.add_argument("--unsubscribe", type=int, default=None,
                        help="Unsubscribe by ID")
    parser.add_argument("--my-subs", action="store_true",
                        help="List your subscriptions")
    parser.add_argument("--check-updates", action="store_true",
                        help="Check for new uploads from subscriptions")

    # Smart Mode
    parser.add_argument("--smart-mode", type=str, default=None,
                        choices=["on", "off", "config"],
                        help="Smart Mode: on/off/config (interactive settings)")
    parser.add_argument("--default-quality", type=str, default=None,
                        help="Set default quality for Smart Mode")
    parser.add_argument("--default-format", type=str, default=None,
                        help="Set default format for Smart Mode")

    # Gallery
    parser.add_argument("--gallery", action="store_true",
                        help="Force gallery mode (image download)")

    # Torrent
    parser.add_argument("--torrent", type=str, default=None,
                        help="Download torrent/magnet link")

    # Settings
    parser.add_argument("--lang", type=str, choices=["en", "fa"], default=None,
                        help="Interface language")
    parser.add_argument("--theme", type=str, default=None,
                        help="CLI theme (dracula, catppuccin, one-dark, etc.)")
    parser.add_argument("--list-themes", action="store_true",
                        help="List available themes")
    parser.add_argument("--portable", action="store_true",
                        help="Enable portable mode")
    parser.add_argument("--quiet", action="store_true",
                        help="Quiet mode (no UI output)")
    parser.add_argument("--log", type=str, default=None,
                        help="Log to file")

    parser.add_argument("--version", action="version", version=f"SmartDL v{VERSION}")

    parser.add_argument("--diagnose", action="store_true",
                        help="Print environment diagnostics (versions, proxy, paths) and exit")

    # Fix conflicting --list-subs
    parser.set_defaults(list_subs=False)

    return parser


def run_cli():
    """Run SmartDL in CLI mode."""
    parser = build_parser()
    args = parser.parse_args()

    # ─── Theme ────────────────────────────────────────────────────────────────
    if args.theme:
        from smart_dl.ui.themes import set_theme
        set_theme(args.theme)

    if args.list_themes:
        from smart_dl.ui.themes import list_themes
        for key, name in list_themes():
            print(f"  {key:20s} {name}")
        return

    if args.diagnose:
        _print_diagnostics()
        return

    # ─── Language ─────────────────────────────────────────────────────────────
    if args.lang:
        from smart_dl.lang import set_lang
        set_lang(args.lang)

    # ─── Proxy ────────────────────────────────────────────────────────────────
    if args.proxy:
        from smart_dl.core.proxy import apply_proxy
        apply_proxy(args.proxy)

    # ─── Portable mode ────────────────────────────────────────────────────────
    if args.portable:
        from smart_dl.core.portable import enable_portable_mode
        enable_portable_mode()
        print("Portable mode enabled.")

    # ─── Smart Mode ───────────────────────────────────────────────────────────
    if args.smart_mode:
        from smart_dl.core.downloader import get_smart_mode, interactive_smart_mode, save_smart_mode
        if args.smart_mode == "config":
            interactive_smart_mode()
            return
        prefs = get_smart_mode()
        prefs["enabled"] = args.smart_mode == "on"
        save_smart_mode(prefs)
        print(f"Smart Mode {'enabled' if prefs['enabled'] else 'disabled'}.")
        if args.default_quality:
            prefs["quality"] = args.default_quality
            save_smart_mode(prefs)
        if args.default_format:
            prefs["format"] = args.default_format
            save_smart_mode(prefs)
        if not args.urls:
            return

    # ─── Subscriptions ────────────────────────────────────────────────────────
    if args.subscribe:
        from smart_dl.core.subscriptions import add_subscription, init_db
        init_db()
        sub_id = add_subscription(args.subscribe)
        print(f"Subscribed! (ID: {sub_id})")
        return

    if args.unsubscribe:
        from smart_dl.core.subscriptions import init_db, remove_subscription
        init_db()
        remove_subscription(args.unsubscribe)
        print(f"Unsubscribed from ID {args.unsubscribe}.")
        return

    if args.check_updates:
        from smart_dl.core.subscriptions import get_subscriptions, init_db
        init_db()
        subs = get_subscriptions()
        if not subs:
            print("No subscriptions.")
            return
        for sub in subs:
            print(f"Checking: {sub['name'] or sub['url']}...")
            # TODO: implement actual new upload detection
        return

    if args.my_subs:
        from smart_dl.core.subscriptions import get_subscription_stats, get_subscriptions, init_db
        init_db()
        subs = get_subscriptions()
        stats = get_subscription_stats()
        if not subs:
            print("No subscriptions.")
            return
        from rich import box
        from rich.table import Table
        t = Table(box=box.ROUNDED, show_header=True, border_style="cyan")
        t.add_column("#", width=5)
        t.add_column("Name", max_width=30)
        t.add_column("URL", max_width=50)
        t.add_column("Platform", width=10)
        t.add_column("Auto-DL", width=8)
        for sub in subs:
            t.add_row(str(sub["id"]), sub["name"] or "?", sub["url"][:50], sub["platform"], "yes" if sub["auto_download"] else "no")
        from smart_dl.ui import console
        console.print(t)
        print(f"\n{stats['active']} active subscriptions, {stats['videos_downloaded']} videos downloaded")
        return

    # ─── Queue ────────────────────────────────────────────────────────────────
    if args.queue:
        _handle_queue(args.queue)
        return

    # ─── History ──────────────────────────────────────────────────────────────
    if args.history:
        _handle_history(args.history)
        return

    if args.list:
        from smart_dl.core.manager import list_downloads
        list_downloads(sort_by=args.sort, filter_by=args.filter)
        return

    if args.export:
        from smart_dl.core.manager import export_downloads
        export_downloads(args.export)
        return

    if args.cleanup:
        from smart_dl.core.manager import cleanup_downloads
        cleanup_downloads(dry_run=args.dry_run)
        return

    # ─── Collect URLs ─────────────────────────────────────────────────────────
    urls = list(args.urls)
    if args.batch:
        try:
            with open(args.batch, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
        except FileNotFoundError:
            print(f"Error: Batch file not found: {args.batch}")
            sys.exit(1)

    if args.torrent:
        urls.append(args.torrent)

    if not urls:
        parser.print_help()
        sys.exit(0)

    # ─── Output directory ─────────────────────────────────────────────────────
    out_folder = Path(args.output) if args.output else Path.home() / "Downloads" / "SmartDL"
    out_folder.mkdir(parents=True, exist_ok=True)

    # ─── Process URLs ─────────────────────────────────────────────────────────
    from smart_dl.ui import error, info, success, warn
    from smart_dl.utils import is_aparat_url, is_playlist_url, is_podcast_url, is_youtube_url

    for url in urls:
        try:
            # ── List subtitles ────────────────────────────────────────────────
            if args.list_subs:
                from smart_dl.extractors.subtitles import list_subtitles
                title, subs, auto_subs = list_subtitles(url)
                if title:
                    print(f"\nSubtitles for: {title}")
                    if subs:
                        print("Manual subtitles:")
                        for lang in sorted(subs.keys()):
                            print(f"  - {lang}")
                    if auto_subs:
                        print("Auto-generated subtitles:")
                        for lang in sorted(auto_subs.keys()):
                            print(f"  - {lang}")
                continue

            # ── Subtitles download ────────────────────────────────────────────
            if args.subtitles:
                from smart_dl.extractors.subtitles import download_subtitles_for_video
                if args.subtitles.lower() == "all":
                    download_subtitles_for_video(url, out_folder, langs=None, embed=args.embed_subs)
                else:
                    langs = [l.strip() for l in args.subtitles.split(",")]
                    download_subtitles_for_video(url, out_folder, langs=langs, embed=args.embed_subs)
                continue

            # ── Thumbnail only ────────────────────────────────────────────────
            if args.thumbnail and not args.urls:
                from smart_dl.extractors.youtube import download_thumbnail
                download_thumbnail(url, out_folder)
                continue

            # ── Torrent ───────────────────────────────────────────────────────
            if is_magnet_link(url) or is_torrent_file(url):
                from smart_dl.extractors.torrent import download_torrent
                download_torrent(url, out_folder)
                continue

            # ── Gallery ───────────────────────────────────────────────────────
            from smart_dl.extractors.gallery import is_gallery_url
            if args.gallery or is_gallery_url(url):
                from smart_dl.extractors.gallery import download_gallery
                download_gallery(url, out_folder)
                continue

            # ── Playlists ─────────────────────────────────────────────────────
            if is_playlist_url(url):
                if is_aparat_url(url):
                    from smart_dl.extractors.aparat import handle_aparat_playlist
                    handle_aparat_playlist(url, out_folder)
                else:
                    from smart_dl.extractors.youtube import handle_playlist
                    handle_playlist(url, out_folder)

            # ── Aparat ────────────────────────────────────────────────────────
            elif is_aparat_url(url):
                from smart_dl.extractors.aparat import download_aparat
                download_aparat(url, out_folder)

            # ── YouTube ───────────────────────────────────────────────────────
            elif is_youtube_url(url):
                from smart_dl.core.downloader import download_with_features
                fmt = "bestvideo+bestaudio/best"
                is_audio = args.audio_only
                if args.quality != "best" and args.quality.isdigit():
                    h = int(args.quality)
                    fmt = f"bestvideo[height<={h}]+bestaudio/best"
                download_with_features(
                    url, out_folder, fmt=fmt, is_audio=is_audio,
                    clip=args.clip, sponsorblock=args.sponsorblock,
                    audio_format=args.audio_format, audio_quality=args.audio_quality,
                    output_format=args.format, embed_metadata=args.embed_metadata,
                    embed_thumbnail=args.embed_thumbnail, embed_subs=args.embed_subs,
                    geo_bypass=args.geo_bypass, impersonate=args.impersonate,
                    output_template=args.output_template, quiet=args.quiet,
                )

            # ── Podcasts ──────────────────────────────────────────────────────
            elif is_podcast_url(url):
                from smart_dl.extractors.podcast import handle_podcast
                handle_podcast(url, out_folder)

            # ── General (any yt-dlp site) ─────────────────────────────────────
            else:
                from smart_dl.extractors.general import detect_platform
                platform = detect_platform(url)
                if platform:
                    info(f"Detected: {platform}")
                from smart_dl.core.downloader import download_with_features
                fmt = "bestvideo+bestaudio/best"
                is_audio = args.audio_only
                download_with_features(
                    url, out_folder, fmt=fmt, is_audio=is_audio,
                    clip=args.clip, sponsorblock=args.sponsorblock,
                    audio_format=args.audio_format, audio_quality=args.audio_quality,
                    output_format=args.format, embed_metadata=args.embed_metadata,
                    embed_thumbnail=args.embed_thumbnail, embed_subs=args.embed_subs,
                    quiet=args.quiet,
                )

        except KeyboardInterrupt:
            warn("Interrupted.")
            break
        except Exception as e:
            error(f"Error: {str(e)[:200]}")

    success("All done!")


def _tool_version(tool: str) -> str:
    """Return the version string of `tool` if it's on PATH, else "not found"."""
    import shutil
    import subprocess
    path = shutil.which(tool)
    if not path:
        return "not found"
    try:
        out = subprocess.run(
            [tool, "--version"], capture_output=True, text=True, timeout=5
        )
        first = (out.stdout or out.stderr).strip().splitlines()
        # Take only the first non-empty line to keep output compact
        for line in first:
            line = line.strip()
            if line:
                return line[:120]
        return "?"
    except Exception as e:
        return f"error: {e!r}"


def _pip_show(pkg: str) -> str:
    """Return `pip show pkg` Version line, or "not installed"."""
    import subprocess
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True, text=True, timeout=10
        )
    except Exception as e:
        return f"error: {e!r}"
    if out.returncode != 0:
        return "not installed"
    for line in out.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    return "installed (no Version line)"


def _print_diagnostics() -> None:
    """Print a single diagnostic block: versions, proxy state, paths.

    Lets the user self-diagnose download issues in seconds without
    digging through toolchain versions manually.
    """
    from smart_dl.core.portable import get_data_dir, is_portable
    from smart_dl.core.proxy import peek_current_proxy

    lines: list[str] = []
    lines.append(f"  [bold cyan]SmartDL v{VERSION}[/bold cyan]  —  diagnostics")
    lines.append("")
    lines.append(f"  Python      : {sys.version.split()[0]}")
    lines.append(f"  Python exe  : {sys.executable}")
    lines.append(f"  Platform    : {sys.platform}")
    lines.append("")
    lines.append("  --- Python packages ---")
    lines.append(f"  yt-dlp      : {_pip_show('yt-dlp')}")
    lines.append(f"  rich        : {_pip_show('rich')}")
    lines.append(f"  requests    : {_pip_show('requests')}")
    lines.append("")
    lines.append("  --- External tools ---")
    lines.append(f"  ffmpeg      : {_tool_version('ffmpeg')}")
    lines.append(f"  node        : {_tool_version('node')}")
    lines.append(f"  aria2c      : {_tool_version('aria2c')}")
    lines.append(f"  winget      : {_tool_version('winget')}")
    lines.append("")
    lines.append("  --- Proxy state ---")
    proxy = peek_current_proxy()
    lines.append(f"  Active      : {proxy if proxy else '[dim]none[/dim]'}")
    # Show each proxy env var that is set
    env_proxies = [
        (k, os.environ.get(k, "")) for k in (
            "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
            "ALL_PROXY", "all_proxy",
            "SOCKS5_PROXY", "socks5_proxy", "SOCKS_PROXY", "socks_proxy",
        ) if os.environ.get(k)
    ]
    if env_proxies:
        lines.append("  Env vars    :")
        for k, v in env_proxies:
            lines.append(f"    {k} = {v}")
    else:
        lines.append("  Env vars    : [dim]none[/dim]")
    lines.append("")
    lines.append("  --- Paths ---")
    lines.append(f"  Portable    : {is_portable()}")
    lines.append(f"  Data dir    : {get_data_dir()}")
    lines.append(f"  Config      : {get_data_dir() / 'config.json'}")
    lines.append("")
    lines.append("  --- Network test ---")
    try:
        import requests
        r = requests.head("https://www.youtube.com", timeout=5, allow_redirects=True)
        lines.append(f"  youtube.com : HTTP {r.status_code} (OK)")
    except Exception as e:
        lines.append(f"  youtube.com : FAILED ({type(e).__name__}: {str(e)[:80]})")

    from rich.console import Console
    from rich.panel import Panel
    c = Console()
    c.print()
    c.print(Panel("\n".join(lines), title="[bold cyan]SmartDL Diagnostics[/bold cyan]",
                   border_style="cyan", padding=(0, 2)))


def _handle_queue(cmds):
    """Handle queue commands."""
    from smart_dl.core.queue import add_to_queue, clear_queue, get_queue, get_queue_stats, init_db
    init_db()

    if not cmds:
        print("Usage: --queue add URL... | start | pause | list | clear")
        return

    action = cmds[0].lower()

    if action == "add":
        urls = cmds[1:]
        if not urls:
            print("Usage: --queue add URL1 URL2 ...")
            return
        count = add_to_queue(urls)
        print(f"Added {count} URL(s) to queue.")

    elif action == "list":
        items = get_queue()
        if not items:
            print("Queue is empty.")
            return
        from rich import box
        from rich.table import Table
        t = Table(box=box.ROUNDED, show_header=True, border_style="cyan")
        t.add_column("#", width=5)
        t.add_column("URL", max_width=50)
        t.add_column("Status", width=10)
        t.add_column("Priority", width=8)
        for item in items:
            status_style = {"pending": "[yellow]", "active": "[cyan]", "completed": "[green]", "failed": "[red]"}.get(item["status"], "")
            t.add_row(str(item["id"]), item["url"][:50], status_style + item["status"] + "[/]", str(item["priority"]))
        from smart_dl.ui import console
        console.print(t)

    elif action == "clear":
        clear_queue()
        print("Queue cleared.")

    elif action == "stats":
        stats = get_queue_stats()
        print(f"Queue: {stats['total']} total, {stats['pending']} pending, {stats['active']} active, {stats['completed']} completed, {stats['failed']} failed")


def _handle_history(cmds):
    """Handle history commands."""
    from smart_dl.core.history import init_db
    init_db()

    if not cmds:
        print("Usage: --history list | search QUERY | stats | re-download ID")
        return

    action = cmds[0].lower()

    if action == "list":
        from smart_dl.core.manager import list_downloads
        list_downloads()

    elif action == "search":
        query = " ".join(cmds[1:])
        if not query:
            print("Usage: --history search KEYWORD")
            return
        from smart_dl.core.manager import list_downloads
        list_downloads(search=query)

    elif action == "stats":
        from smart_dl.core.manager import show_stats
        show_stats()

    elif action == "re-download":
        if len(cmds) < 2:
            print("Usage: --history re-download ID")
            return
        try:
            hist_id = int(cmds[1])
        except ValueError:
            print("Invalid ID.")
            return
        from smart_dl.core.history import get_history_by_id
        entry = get_history_by_id(hist_id)
        if not entry:
            print(f"History entry {hist_id} not found.")
            return
        from smart_dl.extractors.youtube import download_yt
        from smart_dl.ui import info as ui_info
        ui_info(f"Re-downloading: {entry['title']}")
        download_yt(entry["url"], Path.home() / "Downloads" / "SmartDL", "bestvideo+bestaudio/best")


if __name__ == "__main__":
    run_cli()
