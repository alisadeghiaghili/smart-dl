"""Podcast extractor — RSS parser, direct audio, podcast handler."""
import re
import subprocess
import xml.etree.ElementTree as ET

import requests
import yt_dlp
from rich import box
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from smart_dl.core.installer import has_ffmpeg
from smart_dl.core.proxy import get_current_proxy
from smart_dl.core.retry import diagnose_error, retry_with_backoff
from smart_dl.settings import DL_SETTINGS
from smart_dl.ui import console, error, info, print_section, success, warn
from smart_dl.ui.progress import stop_event
from smart_dl.utils import fmt_size

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


def _is_rss(text):
    """Check if text is an RSS/Atom feed."""
    return "<rss" in text[:2000] or "<feed" in text[:2000]


def _parse_rss(text):
    """Parse RSS feed and return list of (title, url) tuples."""
    items = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        # Fallback to regex if XML is malformed
        return _parse_rss_regex(text)

    # Handle RSS 2.0
    for item in root.iter("item"):
        title = _get_text(item, "title", "Episode")
        url = _get_enclosure_url(item)
        if url:
            items.append((title, url))

    # Handle Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = _get_text(entry, "{http://www.w3.org/2005/Atom}title", "Episode", ns)
        url = _get_atom_link(entry)
        if url:
            items.append((title, url))

    return items


def _get_text(element, tag, default="", ns=None):
    """Get text content of an XML element."""
    child = element.find(tag, ns) if ns else element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def _get_enclosure_url(item):
    """Get URL from RSS enclosure element."""
    enc = item.find("enclosure")
    if enc is not None:
        url = enc.get("url", "")
        if url:
            return url.strip()
    return None


def _get_atom_link(entry):
    """Get URL from Atom link element."""
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        href = link.get("href", "")
        if href:
            return href.strip()
    return None


def _parse_rss_regex(text):
    """Fallback RSS parser using regex (for malformed XML)."""
    items = []
    for block in re.findall(r'<item[^>]*>(.*?)</item>', text, re.DOTALL):
        title_m = re.search(r'<title[^>]*><!\[CDATA\[(.+?)\]\]>|<title[^>]*>([^<]+)<', block)
        enc_m   = re.search(r'<enclosure[^>]+url=["\'"]([^"\']+)["\'"][^>]*/?>|<enclosure[^>]+url=([^\s>]+)', block)
        title   = (title_m.group(1) or title_m.group(2)).strip() if title_m else "Episode"
        url     = (enc_m.group(1) or enc_m.group(2)).strip() if enc_m else None
        if url: items.append((title, url))
    return items


def podcast_quality_menu(raw_sz=None):
    """Show quality selection menu for podcast downloads."""
    print_section("Quality \u2014 podcast", "\u2699")
    rows = [
        ("Original (no conversion)", "original", "Direct \u2014 fastest"),
        ("MP3  192 kbps",            "mp3",      "Good quality \u2014 requires ffmpeg"),
        ("MP3  128 kbps",            "mp3_128",  "Smaller file"),
        ("MP3  320 kbps",            "mp3_320",  "Highest MP3 quality"),
        ("M4A (AAC) 128k",           "m4a",      "Best for Apple"),
        ("OGG  192 kbps",            "ogg",      "Open format"),
    ]
    t = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
    t.add_column("#",       style="bold cyan", width=5,  justify="right")
    t.add_column("Quality", style="white",     width=23)
    t.add_column("Format",  style="dim",       width=9)
    t.add_column("Size",    style="dim",       width=14)
    t.add_column("Note",    style="dim",       width=31)
    for i, (label, fmt, note) in enumerate(rows, 1):
        if fmt == "original":
            sz = fmt_size(raw_sz) if raw_sz else "?"
        else:
            sz = ("~" + fmt_size(raw_sz)) if raw_sz else "?"
        t.add_row(str(i), label, fmt.split()[0], sz, note)
    console.print(t)
    if not has_ffmpeg():
        warn("Conversion options require ffmpeg")
        info("Type [bold]i[/bold] at the URL prompt to install ffmpeg from within SmartDL.")
    while True:
        try:
            sel = Prompt.ask("  [bold yellow]Select quality #[/bold yellow]", default="1").strip()
        except (KeyboardInterrupt, EOFError):
            return None
        if sel.isdigit() and 1 <= int(sel) <= len(rows):
            return rows[int(sel)-1]
        warn("Enter a number between 1 and " + str(len(rows)) + ".")


def _convert_audio(raw_path, out_path, fmt_key):
    """Convert audio file using ffmpeg."""
    bitrate_map = {"mp3":"192k","mp3_128":"128k","mp3_320":"320k","m4a":"128k","ogg":"192k"}
    ext_map     = {"mp3":"mp3","mp3_128":"mp3","mp3_320":"mp3","m4a":"m4a","ogg":"ogg"}
    bitrate = bitrate_map.get(fmt_key,"192k")
    ext     = ext_map.get(fmt_key,"mp3")
    final   = out_path.with_suffix("." + ext)
    with Progress(SpinnerColumn(spinner_name="dots"), TextColumn("{task.description}"), BarColumn(complete_style="cyan bold", pulse_style="cyan"),
                  transient=True, console=console) as prog:
        prog.add_task("Converting to " + ext.upper() + "...", total=None)
        subprocess.check_call(
            ["ffmpeg","-y","-i",str(raw_path),"-b:a",bitrate,str(final)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    return final


def download_podcast_url(url, out_folder, fmt_tuple):
    """Download a podcast audio file. Returns True on success, False otherwise."""
    stop_event.clear()
    label, fmt_key, _ = fmt_tuple
    prx = get_current_proxy()
    max_r = DL_SETTINGS["max_retries"]
    frags = DL_SETTINGS["fragments"]
    retry_label = "infinite" if max_r >= 999 else str(max_r)

    print_section("Downloading", "\u2193")
    info("Resume enabled  \u00b7  " + retry_label + " retr" + ("y" if max_r==1 else "ies") +
         "  \u00b7  " + str(frags) + "-thread fragments")

    ydl_opts = {
        "outtmpl":         str(out_folder / "podcast_raw"),
        "quiet":           True,
        "no_warnings":     True,
        "continuedl":      True,
        # yt-dlp's internal retries stay low; the outer retry_with_backoff is
        # the single retry authority (avoids 999 x 999 double-retry hangs).
        "retries":         3,
        "fragment_retries":3,
        "concurrent_fragment_downloads": frags,
        "noprogress":      True,
    }
    if prx: ydl_opts["proxy"] = prx

    def _do_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    try:
        retry_with_backoff(_do_download, max_retries=max_r)
    except KeyboardInterrupt:
        warn("Stopped by user.")
        return False
    except Exception as e:
        if stop_event.is_set():
            return False
        error(str(e)[:200])
        hint = diagnose_error(e)
        if hint:
            info(hint)
        return False

    candidates = list(out_folder.glob("podcast_raw*"))
    raw = candidates[0] if candidates else out_folder / "podcast_raw"
    if not raw.exists():
        error("Download finished but no file was produced.")
        return False

    if fmt_key == "original":
        ext = raw.suffix.lstrip(".") or "mp3"
        out = out_folder / ("podcast." + ext)
        if out.exists():
            out.unlink()
        raw.rename(out)
        success("Downloaded: " + out.name)
        return True

    if not has_ffmpeg():
        error("ffmpeg not found. Install it first (type i at URL prompt).")
        warn("Raw file saved: " + str(raw))
        return False
    try:
        final = _convert_audio(raw, out_folder / "podcast", fmt_key)
        raw.unlink(missing_ok=True)
        success("Downloaded: " + final.name)
        return True
    except Exception as e:
        _estr = str(e)
        if "3199971767" in _estr or "BEF00007" in _estr.upper():
            error("ffmpeg could not convert \u2014 file may be DRM-protected or corrupted.")
            info("Spotify tracks are DRM-protected and cannot be converted.")
            info("Try a different source, or use option 1 (Original) to keep the raw file.")
        else:
            error("ffmpeg error: " + _estr)
        warn("Raw file saved: " + str(raw))
        return False


def handle_podcast(url, out_folder):
    """Handle podcast URL — detect type and download."""
    print_section("Analyzing podcast link", "\U0001f3a4")
    prx = get_current_proxy()
    try:
        s = requests.Session()
        if prx:
            s.proxies = {"http": prx, "https": prx}
        resp = s.get(url, timeout=15, allow_redirects=True,
                     headers={"User-Agent":"Mozilla/5.0"})
        raw_sz = None
        cl = resp.headers.get("Content-Length", "")
        if cl.isdigit():
            raw_sz = int(cl)
        ct   = resp.headers.get("Content-Type","")
        text = resp.text

        # RSS feed
        if "xml" in ct or "rss" in ct or _is_rss(text):
            items = _parse_rss(text)
            if not items:
                error("RSS feed found but no episodes.")
                return
            t = Table(box=box.ROUNDED, show_header=True, border_style="cyan", padding=(0,1))
            t.add_column("#",     style="bold cyan", width=5, justify="right")
            t.add_column("Title", style="white")
            for i,(title,_) in enumerate(items[:20],1):
                t.add_row(str(i), title[:70])
            console.print(t)
            while True:
                sel = Prompt.ask("  [bold yellow]Episode #[/bold yellow]", default="1").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(items[:20]):
                    _, ep_url = items[int(sel)-1]
                    break
                warn("Invalid selection.")
            fmt = podcast_quality_menu(raw_sz=raw_sz)
            if fmt is not None:
                download_podcast_url(ep_url, out_folder, fmt)
            return

        # direct audio
        if "audio" in ct or url.lower().endswith((".mp3",".m4a",".ogg",".opus",".flac",".wav")):
            fmt = podcast_quality_menu(raw_sz=raw_sz)
            if fmt is not None:
                download_podcast_url(url, out_folder, fmt)
            return

    except Exception:
        pass

    # fallback: yt-dlp
    from smart_dl.extractors.youtube import download_yt, yt_quality_menu
    try:
        ydl_opts = {"quiet":True,"no_warnings":True}
        if prx: ydl_opts["proxy"] = prx
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            media_info = ydl.extract_info(url, download=False)

        fmts = media_info.get("formats", []) if media_info else []
        has_video = any(
            f.get("vcodec", "none") not in (None, "none") for f in fmts
        )

        if has_video and media_info:
            fmt, is_audio = yt_quality_menu(media_info)
            if fmt is not None:
                download_yt(url, out_folder, fmt, is_audio)
        else:
            fmt = podcast_quality_menu()
            if fmt is not None:
                download_podcast_url(url, out_folder, fmt)
    except Exception as e:
        error("Cannot handle this URL: " + str(e)[:120])
