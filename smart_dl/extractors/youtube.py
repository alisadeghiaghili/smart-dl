"""YouTube extractor — format fetch, quality menu, download, playlists."""
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from rich import box
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table

from smart_dl.core.cookies import get_cookie_browser
from smart_dl.core.installer import has_ffmpeg
from smart_dl.core.network import show_no_internet_panel
from smart_dl.core.proxy import get_current_proxy
from smart_dl.ui import console, error, info, print_section, success, warn
from smart_dl.ui.progress import stop_event
from smart_dl.utils import fmt_dur, fmt_size

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


from smart_dl.core.engine import (
    YTLogger as _YTLogger,
)
from smart_dl.core.engine import (
    download_single as download_yt,
)
from smart_dl.core.engine import (
    get_media_formats as get_yt_formats,
)


def show_yt_info(info_dict):
    """Display video info panel."""
    title   = info_dict.get("title", "?")
    channel = info_dict.get("uploader") or info_dict.get("channel") or "?"
    dur     = fmt_dur(info_dict.get("duration"))
    views   = info_dict.get("view_count")
    views_s = "{:,}".format(views) if views else "?"
    body = (
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Channel:[/dim] [cyan]" + channel + "[/cyan]   "
        "[dim]Duration:[/dim] [green]" + dur + "[/green]   "
        "[dim]Views:[/dim] [yellow]" + views_s + "[/yellow]"
    )
    console.print(Panel(body, border_style="cyan", title="[bold]Video Info[/bold]", padding=(0,2)))


def yt_quality_menu(info_dict) -> tuple:
    """Show quality selection menu and return (format_string, is_audio)."""
    show_yt_info(info_dict)
    fmts = info_dict.get("formats", [])
    if not fmts and info_dict.get("url"):
        fmts = [info_dict]
    ff = has_ffmpeg()

    combos     = sorted(
        [f for f in fmts if f.get("vcodec","none") != "none" and f.get("acodec","none") != "none" and f.get("ext") != "mhtml"],
        key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
    video_only = sorted(
        [f for f in fmts if f.get("vcodec","none") != "none" and f.get("acodec","none") == "none"],
        key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)
    audio_only = sorted(
        [f for f in fmts if f.get("vcodec","none") == "none" and f.get("acodec","none") != "none"],
        key=lambda x: x.get("abr") or 0, reverse=True)

    _bv_sz = (video_only[0].get("filesize") or video_only[0].get("filesize_approx") or 0) if video_only else 0
    _ba_sz = (audio_only[0].get("filesize") or audio_only[0].get("filesize_approx") or 0) if audio_only else 0
    _bq_sz  = fmt_size(_bv_sz + _ba_sz) if (_bv_sz + _ba_sz) else "?"
    _mp3_sz = fmt_size(_ba_sz) if _ba_sz else "?"

    options = []
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta",
                  border_style="dim", padding=(0,1))
    table.add_column("#",       style="bold cyan",  width=4, justify="right")
    table.add_column("Type",    width=16)
    table.add_column("Quality", style="bold green", width=13)
    table.add_column("Format",  style="yellow",     width=7)
    table.add_column("Size",    style="blue",        width=12)
    table.add_column("Codec",   style="dim",         width=22)

    unknown_codec = [f for f in fmts if f not in combos and f not in video_only and f not in audio_only and f.get("ext") != "mhtml"]
    seen_heights = set()
    deduped = []
    for f in unknown_codec:
        h = f.get("height")
        if h not in seen_heights:
            seen_heights.add(h)
            deduped.append(f)
    unknown_codec = deduped

    for f in unknown_codec[:10]:
        h  = f.get("height","?"); fps = f.get("fps","")
        q  = str(h) + "p" + ("@" + str(fps) + "fps" if fps else "") if h and h != "?" else (f.get("format_note") or f.get("quality") or "?")
        sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        ext = f.get("ext") or "?"
        vc = (f.get("vcodec") or "")[:10]; ac = (f.get("acodec") or "")[:8]
        codec_str = (vc + "+" + ac).strip("+") or (ext + " / aac" if ext != "?" else "\u2014")
        idx = len(options)+1; options.append(("combined", f.get("format_id", "best")))
        table.add_row(str(idx), "\U0001f3ac Video+Audio", q, ext, sz, codec_str)

    for f in combos[:10]:
        h  = f.get("height","?"); fps = f.get("fps","")
        q  = str(h) + "p" + ("@" + str(fps) + "fps" if fps else "") if h != "?" else "?"
        sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        vc = (f.get("vcodec") or "")[:10]; ac = (f.get("acodec") or "")[:8]
        idx = len(options)+1; options.append(("combined", f.get("format_id", "best")))
        table.add_row(str(idx), "\U0001f3ac Video+Audio", q, f.get("ext","?"), sz, vc+"+"+ac)

    for h in [2160,1440,1080,720,480,360,240,144]:
        m = [f for f in video_only if f.get("height") == h]
        if not m: continue
        f = m[0]; fps = f.get("fps","")
        sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        vc = (f.get("vcodec") or "")[:10]
        idx = len(options)+1; options.append(("merge", h))
        needs = "" if ff else " [dim](needs ffmpeg)[/dim]"
        table.add_row(str(idx), "[bold]\U0001f4fa Video HD[/bold]",
                      str(h)+"p"+("@"+str(fps)+"fps" if fps else ""), "mp4",
                      (sz+"+" if sz != "?" else "?"), vc+"+bestaudio"+needs)

    for f in audio_only[:4]:
        abr = f.get("abr","?")
        q   = str(abr) + " kbps" if abr != "?" else f.get("format_note","?")
        sz  = fmt_size(f.get("filesize") or f.get("filesize_approx"))
        idx = len(options)+1; options.append(("audio", f["format_id"]))
        table.add_row(str(idx), "[green]\U0001f3b5 Audio Only[/green]", q,
                      (f.get("ext") or "?"), sz, (f.get("acodec") or "")[:20])

    for label, kind, fmt_id, _sz in [
        ("\U0001f3c6 Best Quality (auto)", "best_v", "bestvideo+bestaudio/best", _bq_sz),
        ("\U0001f399 Audio MP3 192k",      "best_a", "bestaudio/best",           _mp3_sz),
    ]:
        idx = len(options)+1; options.append((kind, fmt_id))
        table.add_row(str(idx), label, "auto", "auto", _sz, "yt-dlp auto")

    console.print(table)
    if not ff:
        warn("ffmpeg not found \u2014 Video HD rows need it for merging.  "
             "Type [bold]i[/bold] at URL prompt to install.")

    while True:
        try:
            choice = IntPrompt.ask("  [bold yellow]Select quality #[/bold yellow]",
                               default=len(options)-1)
        except (KeyboardInterrupt, EOFError):
            return None, False
        choice = max(1, min(choice, len(options)))
        kind, val = options[choice-1]
        if not ff and kind in ("merge", "best_v"):
            warn("This format requires ffmpeg. Type [bold]i[/bold] to install it.")
            continue
        if kind == "combined": return val, False
        if kind == "merge":    return "bestvideo[height<=" + str(val) + "]+bestaudio/best", False
        if kind == "audio":    return val, False
        if kind == "best_v":   return val, False
        if kind == "best_a":   return val, True
        return "bestvideo+bestaudio/best", False


def handle_playlist(
    url: str,
    out_folder: Path,
    audio_only: bool = False,
    quality: str = "best",
    audio_format: str = "mp3",
) -> bool:
    """Handle YouTube playlist download.

    Parameters
    ----------
    url : str
        Playlist URL.
    out_folder : pathlib.Path
        Output directory.
    audio_only : bool, optional
        Whether to extract audio only for all videos.
    quality : str, optional
        Quality selector.
    audio_format : str, optional
        Audio codec format.

    Returns
    -------
    bool
        ``True`` when at least one video downloaded and none remain failed.
    """
    from smart_dl.utils import quality_to_format

    print_section("Analyzing playlist", "\U0001f4cb")
    prx = get_current_proxy()
    fmt = quality_to_format(quality)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "noplaylist": False,
        "logger": _YTLogger(),
    }
    if prx:
        ydl_opts["proxy"] = prx
    saved_browser = get_cookie_browser()
    if saved_browser:
        ydl_opts["cookiesfrombrowser"] = (saved_browser, None, None, None)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(url, download=False)
    except Exception as e:
        _em = str(e).lower()
        _net_kws = ["read timed out", "timeout", "connection", "transporterror",
                    "getaddrinfo", "failed to resolve", "network is unreachable"]
        if any(x in _em for x in _net_kws):
            _host = urlparse(url).netloc or url
            show_no_internet_panel(host=_host)
        else:
            error("Could not fetch playlist: " + str(e)[:120])
        return False

    entries = playlist_info.get("entries") or []
    total = len(entries)
    if total == 0:
        error("Playlist is empty or unavailable.")
        return False

    title = playlist_info.get("title") or "Playlist"
    console.print(Panel(
        "[bold white]" + title + "[/bold white]\n"
        "[dim]Videos:[/dim] [cyan]" + str(total) + "[/cyan]",
        border_style="cyan", title="[bold cyan] Playlist: " + urlparse(url).netloc + "[/bold cyan]", padding=(0,2)
    ))

    t = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0,2))
    t.add_column(style="bold cyan", width=4, justify="right")
    t.add_column(style="white")
    t.add_column(style="dim")
    t.add_row("1", "Same quality for all",   "Choose once \u2014 download all")
    t.add_row("2", "Ask per video",          "Choose quality for each video individually")
    t.add_row("0", "Cancel", "")
    console.print(Panel(t, title="[bold cyan]  Download Mode[/bold cyan]",
                        border_style="cyan", padding=(0,1)))
    mode = Prompt.ask("  [bold yellow]Select[/bold yellow]", default="1").strip()
    if mode == "0":
        return False

    shared_fmt, shared_is_audio = None, False
    if mode == "1":
        info_msg = "Fetching format list from first video..."
        console.print("[dim]  \u00b7 " + info_msg + "[/dim]")
        first_url = entries[0].get("url") or entries[0].get("webpage_url") or (
            "https://www.youtube.com/watch?v=" + entries[0].get("id",""))
        first_info = get_yt_formats(first_url)
        if not first_info:
            error("Could not fetch formats.")
            return False
        shared_fmt, shared_is_audio = yt_quality_menu(first_info)
        if shared_fmt is None:
            return False

    skipped = []
    for i, entry in enumerate(entries, 1):
        if stop_event.is_set():
            break
        vid_url = entry.get("url") or entry.get("webpage_url") or (
            "https://www.youtube.com/watch?v=" + entry.get("id",""))
        vid_title = entry.get("title") or ("Video " + str(i))

        console.print()
        console.print(Rule(
            "[dim cyan]" + str(i) + "/" + str(total) + "  \u2014  " + vid_title[:60] + "[/dim cyan]",
            style="dim"
        ))

        if mode == "2":
            vid_info = get_yt_formats(vid_url)
            if not vid_info:
                warn("Skipping: could not fetch info.")
                skipped.append((i, vid_title, "Could not fetch info"))
                continue
            fmt, is_audio = yt_quality_menu(vid_info)
            if fmt is None:
                skipped.append((i, vid_title, "Skipped by user"))
                continue
        else:
            fmt, is_audio = (fmt if not audio_only else quality_to_format(quality)), (is_audio or audio_only)

        try:
            if not download_yt(vid_url, out_folder, fmt, is_audio):
                skipped.append((i, vid_title, "download failed"))
        except Exception as e:
            warn("Skipped: " + str(e)[:80])
            skipped.append((i, vid_title, str(e)[:80]))

    console.print()
    done = total - len(skipped)
    console.print(Panel(
        "[bold green]\u2713  " + str(done) + "/" + str(total) + " videos downloaded[/bold green]"
        + ("\n[dim]  Folder: " + str(out_folder) + "[/dim]" if done > 0 else ""),
        border_style="green", title="[bold green]  Playlist Complete[/bold green]", padding=(0,2)
    ))

    if not skipped:
        return done == total and total > 0

    console.print()
    st = Table(box=box.ROUNDED, show_header=True, border_style="yellow", padding=(0,1))
    st.add_column("#",     style="bold cyan", width=5, justify="right")
    st.add_column("Title", style="white")
    st.add_column("Reason", style="dim")
    for idx, vtitle, reason in skipped:
        st.add_row(str(idx), vtitle[:55], reason[:40])
    console.print(Panel(st, title="[bold yellow]  Skipped Videos[/bold yellow]",
                        border_style="yellow", padding=(0,1)))

    retry = Prompt.ask(
        "  [bold yellow]Retry skipped videos?[/bold yellow] [dim](y / n)[/dim]",
        default="n"
    ).strip().lower()
    if retry != "y":
        return False

    still_skipped = []
    for idx, vtitle, _ in skipped:
        entry = entries[idx - 1]
        vid_url = entry.get("url") or entry.get("webpage_url") or (
            "https://www.youtube.com/watch?v=" + entry.get("id",""))
        console.print()
        console.print(Rule(
            "[dim cyan]Retry " + str(idx) + "/" + str(total) + "  \u2014  " + vtitle[:60] + "[/dim cyan]",
            style="dim"
        ))
        if mode == "2":
            vid_info = get_yt_formats(vid_url)
            if not vid_info:
                still_skipped.append((idx, vtitle, "Could not fetch info"))
                continue
            fmt, is_audio = yt_quality_menu(vid_info)
            if fmt is None:
                still_skipped.append((idx, vtitle, "Skipped by user"))
                continue
        else:
            fmt, is_audio = shared_fmt, shared_is_audio
        try:
            download_yt(vid_url, out_folder, fmt, is_audio)
        except Exception as e:
            still_skipped.append((idx, vtitle, str(e)[:80]))

    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " \u2014 " + reason[:50])
    else:
        success("All retried videos downloaded successfully.")
        return True




def download_thumbnail(url, out_folder, info_dict=None):
    """Download video thumbnail as a separate file."""
    if info_dict is None:
        info_dict = get_yt_formats(url)
    if not info_dict:
        error("Could not fetch video info for thumbnail.")
        return

    title = info_dict.get("title", "video")
    # Try to get best thumbnail URL
    thumbnails = info_dict.get("thumbnails", [])
    if not thumbnails:
        # Fallback: construct thumbnail URL from video ID
        vid_id = info_dict.get("id", "")
        if vid_id:
            thumb_url = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
        else:
            error("No thumbnail available for this video.")
            return
    else:
        # Pick highest resolution thumbnail
        best = max(thumbnails, key=lambda t: (t.get("width", 0) * t.get("height", 0)))
        thumb_url = best.get("url", "")

    if not thumb_url:
        error("No thumbnail URL found.")
        return

    from smart_dl.utils import safe_filename
    fname = safe_filename(title) + ".jpg"
    fpath = out_folder / fname
    try:
        import requests

        prx = get_current_proxy()
        proxies = {"http": prx, "https": prx} if prx else None
        session = requests.Session()
        if proxies:
            session.proxies = proxies
        resp = session.get(thumb_url, timeout=15, stream=True)
        resp.raise_for_status()
        fpath.parent.mkdir(parents=True, exist_ok=True)
        # Direct copyfileobj — bypasses Python per-chunk overhead
        import shutil as _shutil
        with open(fpath, "wb") as f:
            _shutil.copyfileobj(resp.raw, f, length=64 * 1024)
        success("Thumbnail saved: " + str(fpath))
    except Exception as e:
        error("Failed to download thumbnail: " + str(e)[:100])
