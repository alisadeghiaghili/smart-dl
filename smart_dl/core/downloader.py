"""Download engine — Smart Mode, clipping, SponsorBlock, format selection."""
import yt_dlp
from pathlib import Path

from smart_dl.ui import console, success, warn, error, info, print_section
from smart_dl.ui.progress import stop_event, _progress_ctx, make_progress, yt_hook
from smart_dl.core.proxy import get_current_proxy
from smart_dl.core.cookies import get_cookie_browser
from smart_dl.core.retry import retry_with_backoff
from smart_dl.settings import DL_SETTINGS
from smart_dl.core.config import load_config, save_config

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


# ─── Smart Mode ──────────────────────────────────────────────────────────────
def get_smart_mode() -> dict:
    """Load smart mode preferences from config."""
    cfg = load_config()
    return cfg.get("smart_mode", {
        "enabled": False,
        "quality": "best",
        "format": "mp4",
        "audio_format": "mp3",
        "audio_quality": "192",
        "embed_metadata": False,
        "embed_thumbnail": False,
        "embed_subs": False,
        "sponsorblock": False,
    })


def save_smart_mode(prefs: dict):
    """Save smart mode preferences to config."""
    cfg = load_config()
    cfg["smart_mode"] = prefs
    save_config(cfg)


def apply_smart_mode(ydl_opts: dict):
    """Apply smart mode preferences to yt-dlp options."""
    prefs = get_smart_mode()
    if not prefs.get("enabled"):
        return ydl_opts

    # Quality
    q = prefs.get("quality", "best")
    if q == "best":
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    elif q == "worst":
        ydl_opts["format"] = "worstvideo+worstaudio/worst"
    elif q.isdigit():
        h = int(q)
        ydl_opts["format"] = f"bestvideo[height<={h}]+bestaudio/best"

    # Format
    fmt = prefs.get("format", "mp4")
    if fmt in ("mp4", "mkv", "webm", "avi", "mov"):
        ydl_opts["merge_output_format"] = fmt

    # Audio
    if prefs.get("audio_only"):
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": prefs.get("audio_format", "mp3"),
            "preferredquality": prefs.get("audio_quality", "192"),
        }]

    # Embedding
    if prefs.get("embed_metadata"):
        ydl_opts.setdefault("postprocessors", []).append({
            "key": "FFmpegMetadata"
        })
    if prefs.get("embed_thumbnail"):
        ydl_opts.setdefault("postprocessors", []).append({
            "key": "EmbedThumbnail"
        })
    if prefs.get("embed_subs"):
        ydl_opts["writesubtitles"] = True
        ydl_opts["subtitlesformat"] = "srt/best"

    # SponsorBlock
    if prefs.get("sponsorblock"):
        ydl_opts["sponsorblock_mark"] = ["all"]
        ydl_opts["remove_sponsorblock"] = True

    return ydl_opts


def interactive_smart_mode():
    """Interactive menu to configure Smart Mode."""
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich import box

    prefs = get_smart_mode()

    while True:
        console.print()
        status = "[green]ON[/green]" if prefs.get("enabled") else "[red]OFF[/red]"
        t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
        t.add_column(style="bold cyan", width=4, justify="right")
        t.add_column(style="white")
        t.add_column(style="dim")
        t.add_row("1", "Smart Mode: " + status, "Toggle on/off")
        t.add_row("2", "Default quality: " + prefs.get("quality", "best"), "best, worst, 720, 1080, etc.")
        t.add_row("3", "Default format: " + prefs.get("format", "mp4"), "mp4, mkv, webm, avi, mov")
        t.add_row("4", "Audio format: " + prefs.get("audio_format", "mp3"), "mp3, m4a, opus, flac, wav")
        t.add_row("5", "Audio quality: " + prefs.get("audio_quality", "192") + " kbps", "128, 192, 256, 320")
        t.add_row("6", "SponsorBlock: " + ("ON" if prefs.get("sponsorblock") else "OFF"), "Skip sponsor segments")
        t.add_row("7", "Embed metadata: " + ("ON" if prefs.get("embed_metadata") else "OFF"), "Add title, artist, etc.")
        t.add_row("8", "Embed thumbnail: " + ("ON" if prefs.get("embed_thumbnail") else "OFF"), "Add thumbnail to file")
        t.add_row("0", "Back", "")
        console.print(Panel(t, title="[bold cyan]  Smart Mode Settings[/bold cyan]",
                            border_style="cyan", padding=(0,1)))
        ch = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="0").strip()

        if ch == "0":
            break
        elif ch == "1":
            prefs["enabled"] = not prefs.get("enabled", False)
            state = "ON" if prefs["enabled"] else "OFF"
            success(f"Smart Mode {state}")
        elif ch == "2":
            val = Prompt.ask("  [bold yellow]Quality[/bold yellow]", default=prefs.get("quality", "best")).strip()
            prefs["quality"] = val
        elif ch == "3":
            val = Prompt.ask("  [bold yellow]Format[/bold yellow]", default=prefs.get("format", "mp4")).strip()
            prefs["format"] = val
        elif ch == "4":
            val = Prompt.ask("  [bold yellow]Audio format[/bold yellow]", default=prefs.get("audio_format", "mp3")).strip()
            prefs["audio_format"] = val
        elif ch == "5":
            val = Prompt.ask("  [bold yellow]Audio quality (kbps)[/bold yellow]", default=prefs.get("audio_quality", "192")).strip()
            prefs["audio_quality"] = val
        elif ch == "6":
            prefs["sponsorblock"] = not prefs.get("sponsorblock", False)
        elif ch == "7":
            prefs["embed_metadata"] = not prefs.get("embed_metadata", False)
        elif ch == "8":
            prefs["embed_thumbnail"] = not prefs.get("embed_thumbnail", False)

    save_smart_mode(prefs)


# ─── Enhanced Download ──────────────────────────────────────────────────────
def build_download_opts(
    fmt="bestvideo+bestaudio/best",
    is_audio=False,
    clip=None,
    sponsorblock=False,
    audio_format="mp3",
    audio_quality="192",
    output_format=None,
    embed_metadata=False,
    embed_thumbnail=False,
    embed_subs=False,
    geo_bypass=None,
    impersonate=None,
    output_template=None,
    quiet=False,
):
    """Build yt-dlp options dict with all features."""
    prx = get_current_proxy()
    maxr = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]

    opts = {
        "format": fmt,
        "outtmpl": str(Path.home() / "Downloads" / "SmartDL" / "%(title)s [%(format_id)s].%(ext)s"),
        "continuedl": True,
        "retries": maxr,
        "fragment_retries": maxr,
        "skip_unavailable_fragments": False,
        "concurrent_fragment_downloads": frags,
        "socket_timeout": 30,
        "http_chunk_size": 10 * 1024 * 1024,
        "logger": _QuietLogger() if quiet else None,
        "progress_hooks": [yt_hook] if not quiet else [],
        "quiet": quiet,
        "no_progress": quiet,
        "file_access_retries": 10,
        "extractor_retries": 10,
    }

    # Output format
    if output_format:
        opts["merge_output_format"] = output_format
    elif not is_audio:
        opts["merge_output_format"] = "mp4"

    # Audio extraction
    if is_audio:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": audio_quality,
        }]

    # Video clipping
    if clip:
        opts["download_sections"] = {"*": clip}

    # SponsorBlock
    if sponsorblock:
        opts["sponsorblock_mark"] = ["all"]
        opts["remove_sponsorblock"] = True

    # Embedding
    if embed_metadata:
        opts.setdefault("postprocessors", []).append({"key": "FFmpegMetadata"})
    if embed_thumbnail:
        opts.setdefault("postprocessors", []).append({"key": "EmbedThumbnail"})
    if embed_subs:
        opts["writesubtitles"] = True
        opts["subtitlesformat"] = "srt/best"

    # Geo-bypass
    if geo_bypass:
        opts["geo_verification_proxy"] = geo_bypass

    # Impersonate
    if impersonate:
        opts["impersonate"] = impersonate

    # Output template
    if output_template:
        opts["outtmpl"] = output_template

    # Proxy
    if prx:
        opts["proxy"] = prx

    # Browser cookies
    saved_b = get_cookie_browser()
    if saved_b:
        opts["cookiesfrombrowser"] = (saved_b, None, None, None)

    return opts


def download_with_features(url, out_folder, fmt="bestvideo+bestaudio/best",
                           is_audio=False, **kwargs):
    """Download with all features enabled."""
    from smart_dl.extractors.youtube import _YTLogger

    stop_event.clear()
    maxr = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]

    opts = build_download_opts(fmt=fmt, is_audio=is_audio, **kwargs)
    opts["outtmpl"] = str(out_folder / "%(title)s [%(format_id)s].%(ext)s")
    opts["logger"] = _YTLogger()
    opts["progress_hooks"] = [yt_hook]
    opts["quiet"] = True
    opts["no_progress"] = True

    def _do_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    with make_progress() as prog:
        _progress_ctx["last"] = 0
        _progress_ctx["task"] = prog.add_task("[cyan]Downloading...[/cyan]", total=None)
        _progress_ctx["obj"] = prog
        try:
            retry_with_backoff(_do_download, max_retries=maxr)
        except KeyboardInterrupt:
            warn("Stopped by user.")
            return
        except Exception as e:
            if stop_event.is_set(): return
            error(str(e)[:200])
            return
        finally:
            _progress_ctx["task"] = None
            _progress_ctx["obj"] = None

    success("Download complete!  \u2192  " + str(out_folder))


class _QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
