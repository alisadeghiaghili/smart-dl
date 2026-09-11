"""Utility functions: formatting, filenames, URL detection."""

from __future__ import annotations

import re
from typing import Optional, Union
from urllib.parse import urlparse

from smart_dl.core.net_utils import host_matches, url_host

__all__ = [
    "fmt_dur",
    "fmt_size",
    "is_aparat_url",
    "is_http_url",
    "is_playlist_url",
    "is_podcast_url",
    "is_youtube_url",
    "quality_to_format",
    "safe_filename",
]

_YOUTUBE_HOSTS = ("youtube.com", "youtu.be", "m.youtube.com", "youtube-nocookie.com")
_APARAT_HOSTS = ("aparat.com",)

_QUALITY_PRESETS = {
    "best": "bestvideo+bestaudio/best",
    "worst": "worstvideo+worstaudio/worst",
    "4k": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "8k": "bestvideo[height<=4320]+bestaudio/best[height<=4320]",
    "2160": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
}


def fmt_size(b: Optional[Union[int, float, str]]) -> str:
    """Format a byte count as a human-readable string.

    Parameters
    ----------
    b : int or float or str or None
        Size in bytes, or ``None`` / ``"?"`` for unknown.

    Returns
    -------
    str
        e.g. ``"1.0 MB"`` or ``"?"``.

    Examples
    --------
    >>> fmt_size(0)
    '0 B'
    >>> fmt_size(1024)
    '1.0 KB'
    >>> fmt_size(None)
    '?'
    """
    if b is None or b == "?":
        return "?"
    if b == 0:
        return "0 B"
    size = float(b)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B" and float(size).is_integer():
                return str(int(size)) + " B"
            return str(round(size, 1)) + " " + unit
        size /= 1024
    return str(round(size, 1)) + " TB"


def fmt_dur(s: Optional[Union[int, float]]) -> str:
    """Format seconds as ``HH:MM:SS``.

    Parameters
    ----------
    s : int or float or None
        Duration in seconds.

    Returns
    -------
    str
        Zero-padded duration, or ``"?"`` when unknown.

    Examples
    --------
    >>> fmt_dur(3661)
    '01:01:01'
    """
    if not s:
        return "?"
    total = int(s)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def safe_filename(s: str, maxlen: int = 80) -> str:
    """Sanitize *s* for use as a cross-platform filename.

    Parameters
    ----------
    s : str
        Raw title or path fragment.
    maxlen : int, optional
        Maximum length (default ``80``).

    Returns
    -------
    str
        Safe name; ``"file"`` if the result would be empty.
    """
    cleaned = "".join(c for c in (s or "") if c.isalnum() or c in " ._-()[]").strip()
    cleaned = cleaned.rstrip(". ")
    # Windows reserved device names
    reserved = {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
    if cleaned.lower() in reserved:
        cleaned = "_" + cleaned
    return (cleaned or "file")[:maxlen]


def is_http_url(url: str) -> bool:
    """Check whether *url* uses http(s) or ftp.

    Parameters
    ----------
    url : str
        Candidate URL.

    Returns
    -------
    bool
        ``True`` for supported schemes.
    """
    try:
        scheme = urlparse(url or "").scheme.lower()
    except ValueError:
        return False
    return scheme in ("http", "https", "ftp")


def is_youtube_url(url: str) -> bool:
    """Check whether *url* is a YouTube link (host-aware).

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` if the host is YouTube or a YouTube subdomain.
    """
    return host_matches(url_host(url), _YOUTUBE_HOSTS)


def is_aparat_url(url: str) -> bool:
    """Check whether *url* is an Aparat link (host-aware).

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` if the host is Aparat or a subdomain.
    """
    return host_matches(url_host(url), _APARAT_HOSTS)


def is_podcast_url(url: str, ct: str = "", text: str = "") -> bool:
    """Check whether *url* points at a podcast feed or direct audio file.

    Parameters
    ----------
    url : str
        Absolute URL.
    ct : str, optional
        HTTP Content-Type header value.
    text : str, optional
        Optional body prefix for RSS sniffing (unused reserved).

    Returns
    -------
    bool
        ``True`` if the URL or content type looks like audio/RSS.
    """
    del text  # reserved for future body sniffing
    u = (url or "").lower()
    ctype = (ct or "").lower()
    path = urlparse(u).path if u else ""
    return (
        path.endswith((".mp3", ".m4a", ".ogg", ".opus", ".flac", ".wav"))
        or "audio" in ctype
        or "rss" in ctype
        or "xml" in ctype
        or "feed" in ctype
    )


def is_playlist_url(url: str) -> bool:
    """Check whether *url* looks like a playlist.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for YouTube ``list=`` queries, Aparat playlists, or
        generic ``/playlist/`` paths.
    """
    parsed = urlparse(url or "")
    qs = parsed.query.lower()
    path = parsed.path.lower()
    host = url_host(url)

    if host_matches(host, _YOUTUBE_HOSTS) and "list=" in qs:
        return True
    if host_matches(host, _APARAT_HOSTS) and "/playlist/" in path:
        return True
    if re.search(r"/playlist[s]?(/|$|\?|\d)", path):
        return True
    return False


def quality_to_format(quality: str) -> str:
    """Map a CLI quality token to a yt-dlp format selector.

    Parameters
    ----------
    quality : str
        ``best``, ``worst``, ``4k``, ``8k``, or a height such as ``720``.

    Returns
    -------
    str
        yt-dlp format string.

    Examples
    --------
    >>> quality_to_format("720")
    'bestvideo[height<=720]+bestaudio/best'
    >>> quality_to_format("4k")
    'bestvideo[height<=2160]+bestaudio/best'
    """
    token = (quality or "best").strip().lower()
    if token in _QUALITY_PRESETS:
        return _QUALITY_PRESETS[token]
    if token.isdigit():
        return f"bestvideo[height<={int(token)}]+bestaudio/best"
    return _QUALITY_PRESETS["best"]
