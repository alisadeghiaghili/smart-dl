"""Central download engine — factory for yt-dlp instances and core download operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import yt_dlp

from smart_dl.core.cookies import get_cookie_browser, handle_bot_detection
from smart_dl.core.network import show_no_internet_panel
from smart_dl.core.proxy import get_current_proxy
from smart_dl.core.recorder import record_download
from smart_dl.core.retry import (
    DNS_KEYWORDS,
    RESET_KEYWORDS,
    SUPPRESS_WARNINGS,
    RetryGaveUp,
    diagnose_error,
    retry_with_backoff,
)
from smart_dl.settings import DL_SETTINGS
from smart_dl.ui import error, info, print_section, warn
from smart_dl.ui.progress import _progress_ctx, make_progress, stop_event, yt_hook


class YTLogger:
    """yt-dlp logger that filters noise and shows clean messages."""

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        import re

        if any(s in msg.lower() for s in SUPPRESS_WARNINGS):
            return
        _ml = msg.lower()
        if any(x in _ml for x in DNS_KEYWORDS):
            if "giving up" in _ml:
                show_no_internet_panel(host="www.youtube.com")
                return
            m = re.search(r"[Rr]etrying.*?\((\d+)/(\d+)\)", msg)
            if m:
                warn(
                    "DNS lookup failed — retrying ("
                    + m.group(1)
                    + "/"
                    + m.group(2)
                    + ")..."
                )
            else:
                warn("DNS lookup failed — retrying...")
            return
        if any(x in _ml for x in RESET_KEYWORDS):
            m = re.search(r"[Rr]etrying.*?\((\d+)/(\d+)\)", msg)
            if m:
                warn(
                    "Connection reset by server — retrying ("
                    + m.group(1)
                    + "/"
                    + m.group(2)
                    + ")..."
                )
                if m.group(1) == "3":
                    info(
                        "Server keeps dropping the connection — likely network filtering."
                    )
                    info(
                        "Consider setting a proxy: press [bold cyan]P[/bold cyan] at the URL prompt."
                    )
            else:
                warn("Connection reset by server — retrying...")
            return
        warn(msg)

    def error(self, msg: str) -> None:
        if not stop_event.is_set():
            _ml = msg.lower()
            if any(x in _ml for x in DNS_KEYWORDS):
                return
            error(msg)


def create_ydl_instance(custom_opts: Optional[Dict[str, Any]] = None) -> yt_dlp.YoutubeDL:
    """Factory to create a configured YoutubeDL instance with proxy, cookies, and logger."""
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "logger": YTLogger(),
    }
    prx = get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx

    saved_browser = get_cookie_browser()
    if saved_browser:
        ydl_opts["cookiesfrombrowser"] = (saved_browser, None, None, None)
    else:
        from smart_dl.core.cookies_file import get_cookies_file

        cookie_file = get_cookies_file()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

    if custom_opts:
        ydl_opts.update(custom_opts)

    return yt_dlp.YoutubeDL(ydl_opts)


def build_yt_opts(
    out_folder: Path,
    fmt: str = "bestvideo+bestaudio/best",
    is_audio: bool = False,
    maxr: Optional[int] = None,
    frags: Optional[int] = None,
) -> Dict[str, Any]:
    """Build standard yt-dlp download options."""
    if maxr is None:
        maxr = DL_SETTINGS.get("max_retries", 3)
    if frags is None:
        frags = DL_SETTINGS.get("fragments", 3)

    retries = min(maxr, 3) if maxr < 999 else 3
    opts: Dict[str, Any] = {
        "format": fmt,
        "outtmpl": str(out_folder / "%(title)s [%(format_id)s].%(ext)s"),
        "continuedl": True,
        "retries": retries,
        "fragment_retries": retries,
        "skip_unavailable_fragments": False,
        "concurrent_fragment_downloads": frags,
        "socket_timeout": 30,
        "http_chunk_size": 10 * 1024 * 1024,
        "logger": YTLogger(),
        "progress_hooks": [yt_hook],
        "merge_output_format": "mp4" if (not is_audio and "+" in fmt) else None,
        "quiet": True,
        "no_progress": True,
        "file_access_retries": 10,
        "extractor_retries": 10,
        "postprocessors": (
            [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            if is_audio
            else []
        ),
    }
    prx = get_current_proxy()
    if prx:
        opts["proxy"] = prx
    saved_browser = get_cookie_browser()
    if saved_browser:
        opts["cookiesfrombrowser"] = (saved_browser, None, None, None)
    else:
        from smart_dl.core.cookies_file import get_cookies_file

        cookie_file = get_cookies_file()
        if cookie_file:
            opts["cookiefile"] = cookie_file

    return opts


def get_media_formats(url: str) -> Optional[Dict[str, Any]]:
    """Extract format information for any media URL."""
    from rich.prompt import Prompt

    from smart_dl.ui.progress import reset_no_internet

    reset_no_internet(urlparse(url).netloc or url)
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "listformats": False,
        "noplaylist": True,
        "logger": YTLogger(),
    }
    prx = get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx
    saved_browser = get_cookie_browser()
    if saved_browser:
        ydl_opts["cookiesfrombrowser"] = (saved_browser, None, None, None)
    else:
        from smart_dl.core.cookies_file import get_cookies_file

        cookie_file = get_cookies_file()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        err_s = str(e)
        if "sign in to confirm" in err_s.lower() or "not a bot" in err_s.lower():
            if handle_bot_detection(url, ydl_opts):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(url, download=False)
                except Exception as e2:
                    error(str(e2)[:200])
                    return None
            return None
        if prx and ("Unable to connect to proxy" in err_s or "10061" in err_s or "ProxyError" in err_s):
            warn("Proxy unreachable: " + prx)
            ans = Prompt.ask(
                "  [bold yellow]Clear proxy and retry without it?[/bold yellow] [dim](y / n)[/dim]",
                default="y",
            ).strip().lower()
            if ans != "n":
                from smart_dl.core.proxy import clear_proxy

                clear_proxy()
                info("Retrying without proxy...")
                with yt_dlp.YoutubeDL({
                    "quiet": True,
                    "no_warnings": True,
                    "listformats": False,
                    "noplaylist": True,
                }) as ydl:
                    return ydl.extract_info(url, download=False)
        _net_kws = [
            "getaddrinfo failed", "name or service not known",
            "failed to resolve", "network is unreachable",
            "no route to host", "errno 11001", "transporterror",
        ]
        if any(x in err_s.lower() for x in _net_kws):
            _host = urlparse(url).netloc or url
            show_no_internet_panel(host=_host)
            return None
        if "unsupported url" in err_s.lower():
            error("Unsupported URL — yt-dlp has no extractor for: " + urlparse(url).netloc)
            return None
        raise


def download_single(
    url: str,
    out_folder: Path,
    fmt: str = "bestvideo+bestaudio/best",
    is_audio: bool = False,
) -> bool:
    """Download a single stream with retry and history recording."""
    from rich.prompt import Prompt

    stop_event.clear()
    maxr = DL_SETTINGS.get("max_retries", 3)
    frags = DL_SETTINGS.get("fragments", 3)
    retry_label = "infinite" if maxr >= 999 else str(maxr)
    print_section("Downloading", "⬇")
    info(
        "Resume enabled  ·  "
        + retry_label
        + " retr"
        + ("y" if maxr == 1 else "ies")
        + "  ·  "
        + str(frags)
        + "-thread fragments"
    )

    opts = build_yt_opts(out_folder, fmt=fmt, is_audio=is_audio, maxr=maxr, frags=frags)

    def _do_download() -> None:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _attempt_download() -> bool:
        try:
            retry_with_backoff(_do_download, max_retries=maxr)
            return True
        except KeyboardInterrupt:
            warn("Stopped by user.")
            return False
        except RetryGaveUp as give_up:
            if stop_event.is_set():
                return False
            error(str(give_up)[:200])
            if give_up.reason == "dns":
                show_no_internet_panel(host=urlparse(url).netloc or url)
            return False
        except Exception as exc:
            if stop_event.is_set():
                return False
            err_s = str(exc)
            prx2 = get_current_proxy()
            if prx2 and ("Unable to connect to proxy" in err_s or "10061" in err_s):
                warn("Proxy unreachable: " + prx2)
                ans = Prompt.ask(
                    "  [bold yellow]Clear proxy and retry?[/bold yellow] [dim](y / n)[/dim]",
                    default="y",
                ).strip().lower()
                if ans != "n":
                    from smart_dl.core.proxy import clear_proxy

                    clear_proxy()
                    opts.pop("proxy", None)
                    try:
                        retry_with_backoff(_do_download, max_retries=maxr)
                        return True
                    except Exception as exc2:
                        error(str(exc2)[:200])
                        hint = diagnose_error(exc2)
                        if hint:
                            info(hint)
                        return False
                return False
            error(err_s[:200])
            hint = diagnose_error(exc)
            if hint:
                info(hint)
            return False

    with make_progress() as prog:
        _progress_ctx["last"] = 0
        _progress_ctx["task"] = prog.add_task("[cyan]Downloading...[/cyan]", total=None)
        _progress_ctx["obj"] = prog
        try:
            ok = _attempt_download()
        finally:
            _progress_ctx["task"] = None
            _progress_ctx["obj"] = None

    out_path = _progress_ctx.pop("outfile", None)
    record_download(
        url,
        success=ok,
        title=Path(str(out_path)).name if out_path else "",
        file_path=Path(str(out_path)) if out_path else None,
        format_str=fmt,
        is_audio=is_audio,
        error="" if ok else "download failed",
    )
    return ok
