"""CLI interface — argparse for non-interactive mode.

Command handlers live in :mod:`smart_dl.commands`; this module owns the
parser surface and thin orchestration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from smart_dl import VERSION
from smart_dl.commands.diagnose import print_diagnostics as _print_diagnostics
from smart_dl.commands.downloads import (
    count_failure,
    queue_download_item,
    resolve_education_max_lessons,
)
from smart_dl.commands.history_cmds import handle_history as _handle_history
from smart_dl.commands.queue_cmds import handle_queue as _handle_queue
from smart_dl.commands.smart_mode import handle_smart_mode_flag
from smart_dl.commands.subscriptions import (
    handle_check_updates,
    handle_my_subs,
    handle_subscribe,
    handle_unsubscribe,
)
from smart_dl.extractors.dispatch import dispatch_url_download

__all__ = [
    "build_parser",
    "count_failure",
    "queue_download_item",
    "resolve_education_max_lessons",
    "run_cli",
]


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all features.

    Returns
    -------
    argparse.ArgumentParser
        Configured CLI parser.
    """
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
            "  smart-dl URL --limit-rate 2M\n"
            "  smart-dl --batch urls.txt -o ~/Downloads\n"
            "  smart-dl --queue add URL1 URL2 && smart-dl --queue start\n"
            "  smart-dl --subscribe https://youtube.com/@channel\n"
            "  smart-dl --check-updates\n"
            "  smart-dl --history list --sort date\n"
            "  smart-dl --smart-mode on\n"
            "  smart-dl --theme catppuccin\n"
            "  smart-dl https://pixiv.net/artworks/123\n"
            "  smart-dl --torrent magnet:?xt=...\n"
        ),
    )

    parser.add_argument("urls", nargs="*", help="URL(s) to download")

    # Output
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output directory (default: ~/Downloads/SmartDL)",
    )
    parser.add_argument(
        "--output-template",
        type=str,
        default=None,
        help="Output filename template (yt-dlp format)",
    )

    # Quality & Format
    parser.add_argument(
        "-q",
        "--quality",
        type=str,
        default="best",
        help="Quality: best, worst, 720, 1080, 4k, 8k (default: best)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=None,
        choices=["mp4", "mkv", "webm", "avi", "mov"],
        help="Output container format",
    )
    parser.add_argument(
        "--clip",
        type=str,
        default=None,
        help="Download segment: START-END (e.g., 00:01:30-00:05:00)",
    )

    # Audio
    parser.add_argument("--audio-only", action="store_true", help="Extract audio only")
    parser.add_argument(
        "--audio-format",
        type=str,
        default="mp3",
        choices=["mp3", "m4a", "opus", "flac", "wav", "vorbis"],
        help="Audio format (default: mp3)",
    )
    parser.add_argument(
        "--audio-quality",
        type=str,
        default="192",
        help="Audio bitrate in kbps (default: 192)",
    )

    # Subtitles
    parser.add_argument(
        "--subtitles",
        type=str,
        default=None,
        help="Download subtitles (e.g., en,fa or all)",
    )
    parser.add_argument("--list-subs", action="store_true", help="List available subtitles")
    parser.add_argument(
        "--embed-subs",
        action="store_true",
        help="Embed subtitles in video",
    )

    # Thumbnails & Metadata
    parser.add_argument("--thumbnail", action="store_true", help="Download thumbnail")
    parser.add_argument(
        "--embed-thumbnail",
        action="store_true",
        help="Embed thumbnail in video",
    )
    parser.add_argument(
        "--embed-metadata",
        action="store_true",
        help="Embed metadata (title, artist, etc.)",
    )

    # Features
    parser.add_argument(
        "--sponsorblock",
        action="store_true",
        help="Skip sponsor segments (SponsorBlock)",
    )
    parser.add_argument(
        "--geo-bypass",
        type=str,
        default=None,
        help="Bypass geo-restriction (country code, e.g., US)",
    )
    parser.add_argument(
        "--impersonate",
        type=str,
        default=None,
        help="Impersonate browser (chrome, firefox, safari)",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy URL (http://host:port or socks5://host:port)",
    )
    parser.add_argument(
        "--limit-rate",
        type=str,
        default=None,
        help="Max download rate (e.g. 500K, 2M) — fair use on shared links",
    )

    # Batches & Queue
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        help="File containing URLs (one per line)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Number of concurrent downloads (default: 1)",
    )

    parser.add_argument(
        "--queue",
        nargs="+",
        metavar="CMD",
        help="Queue commands: add URL..., start, pause, resume, list, clear",
    )
    parser.add_argument(
        "--history",
        nargs="+",
        metavar="CMD",
        help="History commands: list, search QUERY, stats, re-download ID",
    )
    parser.add_argument("--list", action="store_true", help="List download history")
    parser.add_argument(
        "--sort",
        type=str,
        default="date",
        choices=["date", "name", "size"],
        help="Sort order for --list",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Filter by platform (youtube, aparat, etc.)",
    )
    parser.add_argument("--export", type=str, default=None, help="Export history to JSON file")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove failed/incomplete downloads",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done (with --cleanup)",
    )

    # Subscriptions
    parser.add_argument("--subscribe", type=str, default=None, help="Subscribe to channel/playlist URL")
    parser.add_argument("--unsubscribe", type=int, default=None, help="Unsubscribe by ID")
    parser.add_argument("--my-subs", action="store_true", help="List your subscriptions")
    parser.add_argument(
        "--check-updates",
        action="store_true",
        help="Check for new uploads from subscriptions",
    )

    # Smart Mode
    parser.add_argument(
        "--smart-mode",
        type=str,
        default=None,
        choices=["on", "off", "config"],
        help="Smart Mode: on/off/config (interactive settings)",
    )
    parser.add_argument(
        "--default-quality",
        type=str,
        default=None,
        help="Set default quality for Smart Mode",
    )
    parser.add_argument(
        "--default-format",
        type=str,
        default=None,
        help="Set default format for Smart Mode",
    )

    parser.add_argument("--gallery", action="store_true", help="Force gallery mode (image download)")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download every education lesson (no cap; default is capped)",
    )
    parser.add_argument(
        "--max-lessons",
        type=int,
        default=None,
        help="Cap number of education course lessons (default: 20)",
    )
    parser.add_argument(
        "--all-episodes",
        action="store_true",
        help="Download every episode from a podcast RSS feed",
    )
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=None,
        help="Cap number of podcast episodes to download",
    )
    parser.add_argument("--torrent", type=str, default=None, help="Download torrent/magnet link")

    parser.add_argument("--lang", type=str, choices=["en", "fa"], default=None, help="Interface language")
    parser.add_argument(
        "--cookies-file",
        type=str,
        default=None,
        help="Netscape cookies.txt path (used when no browser cookie source)",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        help="CLI theme (dracula, catppuccin, one-dark, etc.)",
    )
    parser.add_argument("--list-themes", action="store_true", help="List available themes")
    parser.add_argument("--portable", action="store_true", help="Enable portable mode")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (no UI output)")
    parser.add_argument("--log", type=str, default=None, help="Log to file")

    parser.add_argument("--version", action="version", version=f"SmartDL v{VERSION}")
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Print environment diagnostics (versions, proxy, paths) and exit",
    )

    parser.set_defaults(list_subs=False)
    return parser


def _download_single_url(url: str, args, out_folder: Path) -> bool:
    """Dispatch one URL; CLI-only pre-steps (subtitles/thumbnail) first."""
    from smart_dl.extractors.subtitles import (
        download_subtitles_for_video,
        list_subtitles,
    )

    if args.list_subs:
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
        return True

    if args.subtitles:
        if args.subtitles.lower() == "all":
            download_subtitles_for_video(url, out_folder, langs=None, embed=args.embed_subs)
        else:
            langs = [part.strip() for part in args.subtitles.split(",")]
            download_subtitles_for_video(url, out_folder, langs=langs, embed=args.embed_subs)
        return True

    if args.thumbnail:
        from smart_dl.extractors.youtube import download_thumbnail

        download_thumbnail(url, out_folder)
        return True

    return dispatch_url_download(url, args, out_folder)


def run_cli() -> None:
    """Run SmartDL in CLI mode.

    Returns
    -------
    None
        Exits the process on fatal CLI errors.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.theme:
        from smart_dl.ui.themes import set_theme

        set_theme(args.theme)

    if args.list_themes:
        from smart_dl.ui import console
        from smart_dl.ui.themes import list_themes

        console.print("[bold cyan]Available Themes:[/bold cyan]")
        for key, name in list_themes():
            console.print(f"  [green]{key:20s}[/green] {name}")
        return

    if args.diagnose:
        print_diagnostics_safe()
        return

    if args.lang:
        from smart_dl.lang import set_lang

        set_lang(args.lang)

    if args.cookies_file:
        from smart_dl.core.cookies_file import load_netscape_cookies, set_cookies_file
        from smart_dl.ui import error, success

        set_cookies_file(args.cookies_file)
        ok, msg = load_netscape_cookies(args.cookies_file)
        if ok:
            success("Cookies: " + msg)
        else:
            error("Cookies file: " + msg)
            sys.exit(1)

    if args.log:
        from smart_dl.core.logging import setup_logging

        setup_logging(args.log, verbose=not args.quiet)

    if args.proxy:
        from smart_dl.core.proxy import apply_proxy

        apply_proxy(args.proxy)

    if args.portable:
        from smart_dl.core.portable import enable_portable_mode
        from smart_dl.ui import success

        enable_portable_mode()
        success("Portable mode enabled 🎒.")

    if not handle_smart_mode_flag(
        args.smart_mode,
        default_quality=args.default_quality,
        default_format=args.default_format,
    ):
        return
    if args.smart_mode and not args.urls:
        return

    if args.subscribe:
        handle_subscribe(args.subscribe)
        return
    if args.unsubscribe:
        handle_unsubscribe(args.unsubscribe)
        return
    if args.check_updates:
        handle_check_updates()
        return
    if args.my_subs:
        handle_my_subs()
        return

    if args.queue:
        _handle_queue(args.queue, queue_download_item)
        return
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

    urls = list(args.urls)
    if args.batch:
        try:
            with open(args.batch, "r", encoding="utf-8") as handle:
                for line in handle:
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

    from smart_dl.core.paths import get_default_download_dir

    out_folder = Path(args.output) if args.output else get_default_download_dir()
    try:
        out_folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"Error: cannot create output directory {out_folder}: {exc}", file=sys.stderr)
        sys.exit(1)

    failures = 0
    for url in urls:
        try:
            if not _download_single_url(url, args, out_folder):
                failures += 1
        except KeyboardInterrupt:
            from smart_dl.ui import warn

            warn("Interrupted.")
            break
        except Exception as exc:  # noqa: BLE001
            from smart_dl.ui import error

            error(f"Error: {str(exc)[:200]}")
            failures += 1

    if failures:
        from smart_dl.ui import error

        error(f"Finished with {failures} failed download(s).")
        sys.exit(1)
    from smart_dl.ui import success

    success("All done!")


def print_diagnostics_safe() -> None:
    """Print diagnostics without crashing the CLI."""
    _print_diagnostics()


if __name__ == "__main__":
    run_cli()
