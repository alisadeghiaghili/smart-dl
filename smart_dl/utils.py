"""Utility functions: formatting, filenames, URL detection."""
from __future__ import annotations

import re
from typing import Optional, Union
from urllib.parse import urlparse


def fmt_size(b: Optional[Union[int, float, str]]) -> str:
    """Format byte count as human-readable string."""
    if b is None or b == "?": return "?"
    if b == 0: return "0 B"
    for unit in ["B","KB","MB","GB"]:
        if b < 1024: return str(round(b,1)) + " " + unit
        b /= 1024  # type: ignore
    return str(round(b,1)) + " TB"


def fmt_dur(s: Optional[Union[int, float]]) -> str:
    """Format seconds as HH:MM:SS."""
    if not s: return "?"
    return str(int(s//3600)).zfill(2) + ":" + str(int((s%3600)//60)).zfill(2) + ":" + str(int(s%60)).zfill(2)


def safe_filename(s: str, maxlen: int = 80) -> str:
    """Sanitize a string for use as a filename."""
    return ("".join(c for c in s if c.isalnum() or c in " ._-()[]").strip() or "file")[:maxlen]


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link."""
    return any(h in urlparse(url).netloc for h in ["youtube.com","youtu.be","www.youtube.com"])


def is_podcast_url(url: str, ct: str = "", text: str = "") -> bool:
    """Check if URL points to a podcast or direct audio file."""
    u = url.lower()
    ct = ct.lower()
    return (
        u.endswith((".mp3", ".m4a", ".ogg", ".opus", ".flac", ".wav")) or
        "audio" in ct or
        "rss" in ct or
        "xml" in ct or
        "feed" in ct
    )


def is_aparat_url(url: str) -> bool:
    """Check if URL is an Aparat link."""
    return any(h in urlparse(url).netloc for h in ["aparat.com", "www.aparat.com"])


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist link."""
    parsed = urlparse(url)
    qs = parsed.query.lower()
    path = parsed.path.lower()
    netloc = parsed.netloc.lower()

    # YouTube playlist
    if "youtube.com" in netloc and "list=" in qs:
        return True
    # Aparat playlist
    if "aparat.com" in netloc and "/playlist/" in path:
        return True
    # Generic /playlist/... pattern
    if re.search(r'/playlist[s]?(/|$|\?|\d)', path):
        return True

    return False
