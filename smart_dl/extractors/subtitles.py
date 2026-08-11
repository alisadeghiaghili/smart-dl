"""Subtitle support — download, search, and embed subtitles."""

import yt_dlp
from rich import box
from rich.prompt import Prompt
from rich.table import Table

from smart_dl.core.cookies import get_cookie_browser
from smart_dl.core.proxy import get_current_proxy
from smart_dl.ui import console, error, info, print_section, success, warn

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


def list_subtitles(url):
    """List available subtitles for a video."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    prx = get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx
    saved = get_cookie_browser()
    if saved:
        ydl_opts["cookiesfrombrowser"] = (saved, None, None, None)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            if not info_dict:
                return None, None, None

            title = info_dict.get("title", "video")
            subs = info_dict.get("subtitles", {})
            auto_subs = info_dict.get("automatic_captions", {})

            return title, subs, auto_subs
    except Exception as e:
        error("Could not fetch subtitle info: " + str(e)[:100])
        return None, None, None


def show_subtitle_menu(url):
    """Show subtitle selection menu."""
    print_section("Subtitles", "\U0001f4dd")

    title, subs, auto_subs = list_subtitles(url)
    if title is None:
        return

    if not subs and not auto_subs:
        warn("No subtitles available for this video.")
        return

    # Build options list
    options = []

    # Manual subtitles first
    if subs:
        info("Manual subtitles available:")
        for lang in sorted(subs.keys()):
            options.append(("manual", lang, lang))
    else:
        info("No manual subtitles found.")

    # Auto-generated subtitles
    if auto_subs:
        info("Auto-generated subtitles available:")
        for lang in sorted(auto_subs.keys()):
            if lang not in subs:  # Don't show duplicates
                options.append(("auto", lang, lang + " (auto)"))

    if not options:
        warn("No subtitles available.")
        return

    # Show table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta",
                  border_style="dim", padding=(0,1))
    table.add_column("#", style="bold cyan", width=4, justify="right")
    table.add_column("Language", style="white", width=20)
    table.add_column("Type", style="dim", width=15)

    for i, (stype, lang, label) in enumerate(options, 1):
        type_str = "Manual" if stype == "manual" else "Auto-generated"
        table.add_row(str(i), label, type_str)

    table.add_row("A", "All subtitles", "Download all")
    table.add_row("0", "Cancel", "")

    console.print(table)

    while True:
        try:
            choice = Prompt.ask("  [bold yellow]Select subtitle #[/bold yellow]", default="0").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if choice == "0":
            return

        if choice.upper() == "A":
            # Download all
            selected = options
            break

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            selected = [options[int(choice) - 1]]
            break

        warn("Invalid selection.")

    return selected


def download_subtitles(url, out_folder, selected=None, embed=False):
    """Download subtitles for a video."""
    if selected is None:
        selected = show_subtitle_menu(url)
    if not selected:
        return

    out_dir = str(out_folder)

    for stype, lang, label in selected:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": stype == "manual",
            "writeautomaticsub": stype == "auto",
            "subtitleslangs": [lang],
            "subtitlesformat": "srt/best",
            "outtmpl": out_dir + "/%(title)s.%(ext)s",
        }

        if embed:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegSubtitlesConvertor",
                "format": "srt",
            }]

        prx = get_current_proxy()
        if prx:
            ydl_opts["proxy"] = prx
        saved = get_cookie_browser()
        if saved:
            ydl_opts["cookiesfrombrowser"] = (saved, None, None, None)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            success(f"Subtitle downloaded: {label}")
        except Exception as e:
            error(f"Failed to download subtitle {label}: {str(e)[:100]}")


def download_subtitles_for_video(url, out_folder, langs=None, embed=False):
    """Download subtitles by language code list."""
    if langs is None:
        # Default: try English and Persian
        langs = ["en", "fa", "fa-IR"]

    title, subs, auto_subs = list_subtitles(url)
    if title is None:
        return

    # Find matching subtitles
    selected = []
    for lang in langs:
        if lang in subs:
            selected.append(("manual", lang, lang))
        elif lang in auto_subs:
            selected.append(("auto", lang, lang + " (auto)"))

    # Also try partial matches (e.g., "en" matches "en-US")
    if not selected:
        for lang in langs:
            for sub_lang in list(subs.keys()) + list(auto_subs.keys()):
                if sub_lang.startswith(lang):
                    stype = "manual" if sub_lang in subs else "auto"
                    selected.append((stype, sub_lang, sub_lang))
                    break

    if selected:
        download_subtitles(url, out_folder, selected, embed)
    else:
        info("No matching subtitles found for: " + ", ".join(langs))
