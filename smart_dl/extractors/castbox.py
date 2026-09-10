"""Castbox-specific page parsing (RSS + episode links)."""

from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import unquote, urljoin

__all__ = [
    "CastboxEpisode",
    "extract_castbox_audio_urls",
    "extract_castbox_episode_paths",
    "extract_castbox_rss_url",
    "is_castbox_url",
]


class CastboxEpisode(dict):
    """Episode entry parsed from a Castbox page."""

    @property
    def url(self) -> str:
        return str(self.get("url") or "")

    @property
    def title(self) -> str:
        return str(self.get("title") or "")


def is_castbox_url(url: str) -> bool:
    """Check whether *url* is a Castbox.fm link.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for castbox.fm hosts.
    """
    from smart_dl.core.net_utils import host_matches, url_host

    return host_matches(url_host(url), ("castbox.fm", "www.castbox.fm"))


def extract_castbox_rss_url(html: str) -> Optional[str]:
    """Extract the show's original RSS URL from Castbox HTML.

    Castbox embeds URL-encoded JSON containing ``rss_url``.

    Parameters
    ----------
    html : str
        Channel page HTML.

    Returns
    -------
    str or None
        Absolute RSS URL when present.
    """
    # Direct JSON key (sometimes not encoded)
    match = re.search(r'"rss_url"\s*:\s*"([^"]+)"', html or "")
    if match:
        value = unquote(match.group(1))
        if value.startswith("http"):
            return value

    # URL-encoded inside escaped JSON
    match = re.search(r"rss_url(?:%22)?(?:%3A|:)(?:%22)?(https?[^%\"']+)", html or "", re.I)
    if match:
        value = unquote(match.group(0).split(":", 1)[-1].strip("%22%22"))
        if value.startswith("http"):
            return value

    decoded = unquote(html or "")
    match = re.search(r'"rss_url"\s*:\s*"(https?://[^"]+)"', decoded)
    if match:
        return match.group(1)
    return None


def extract_castbox_episode_paths(html: str) -> List[str]:
    """Extract Castbox episode paths from channel HTML.

    Parameters
    ----------
    html : str
        Channel page HTML.

    Returns
    -------
    list of str
        Paths like ``/episode/slug-id2386830-id967731521``.
    """
    found: List[str] = []
    for match in re.finditer(r"/episode/([^\"'\\?\s]+)", html or ""):
        path = "/episode/" + unquote(match.group(1))
        if path not in found:
            found.append(path)
    return found


def extract_castbox_audio_urls(html: str) -> List[str]:
    """Extract direct mp3 URLs from Castbox HTML (decoded).

    Parameters
    ----------
    html : str
        Channel or episode page HTML.

    Returns
    -------
    list of str
        Unique http(s) mp3 URLs.
    """
    decoded = unquote(html or "")
    found: List[str] = []
    for match in re.finditer(r"https?://[^\"'\s\\]+\.mp3[^\"'\s\\]*", decoded, re.I):
        url = match.group(0)
        if url not in found:
            found.append(url)
    return found


def castbox_episode_lessons(
    html: str,
    base_url: str = "https://castbox.fm",
    *,
    limit: int = 50,
) -> List[CastboxEpisode]:
    """Build Castbox episode list from channel HTML.

    Parameters
    ----------
    html : str
        Channel page HTML.
    base_url : str, optional
        Origin for absolute URLs.
    limit : int, optional
        Maximum episodes.

    Returns
    -------
    list of CastboxEpisode
        Episodes with absolute URLs and crude titles from slugs.
    """
    episodes: List[CastboxEpisode] = []
    for path in extract_castbox_episode_paths(html)[:limit]:
        slug = path.rsplit("/", 1)[-1]
        # strip trailing -idNNN-idMMM
        title = re.sub(r"-id\d+(-id\d+)?$", "", slug)
        title = unquote(title).replace("-", " ").strip()[:80] or slug
        episodes.append(
            CastboxEpisode(title=title, url=urljoin(base_url, path))
        )
    return episodes
