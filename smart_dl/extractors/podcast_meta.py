"""Podcast platform detection and RSS episode listing."""

from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from smart_dl.core.net_utils import host_matches, url_host

__all__ = [
    "PodcastEpisode",
    "detect_podcast_platform",
    "is_podcast_feed_url",
    "is_podcast_platform_url",
    "parse_rss_episodes",
    "rss_from_platform_url",
]

_PODCAST_HOSTS = (
    "anchor.fm",
    "spotify.com",
    "open.spotify.com",
    "soundcloud.com",
    "castbox.fm",
    "podcasters.spotify.com",
    "buzzsprout.com",
    "libsyn.com",
    "podbean.com",
    "simplecast.com",
    "transistor.fm",
    "megaphone.fm",
    "fireside.fm",
    "feed.podbean.com",
    "feeds.simplecast.com",
)


class PodcastEpisode(dict):
    """One podcast episode (dict with convenience properties)."""

    @property
    def title(self) -> str:
        return str(self.get("title") or "")

    @property
    def url(self) -> str:
        return str(self.get("url") or "")


def is_podcast_platform_url(url: str) -> bool:
    """Check whether *url* is a known podcast hosting platform page.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    bool
        ``True`` for SoundCloud / Anchor / Castbox / Spotify pages, etc.
    """
    return host_matches(url_host(url), _PODCAST_HOSTS)


def is_podcast_feed_url(url: str, ct: str = "") -> bool:
    """Check whether *url* looks like an RSS/podcast feed or direct audio.

    Parameters
    ----------
    url : str
        Absolute URL.
    ct : str, optional
        HTTP Content-Type header.

    Returns
    -------
    bool
        ``True`` for RSS XML or audio file URLs.
    """
    from smart_dl.utils import is_podcast_url

    path = urlparse(url or "").path.lower()
    if path.endswith((".xml", ".rss", "/feed", "/rss")):
        return True
    return is_podcast_url(url, ct=ct)


def detect_podcast_platform(url: str) -> str:
    """Return a short platform label for a podcast URL.

    Parameters
    ----------
    url : str
        Absolute URL.

    Returns
    -------
    str
        e.g. ``SoundCloud``, ``Anchor``, ``Spotify``, ``Podcast feed``,
        or ``Unknown``.
    """
    host = url_host(url)
    if host_matches(host, ("soundcloud.com",)):
        return "SoundCloud"
    if host_matches(host, ("anchor.fm", "podcasters.spotify.com")):
        return "Anchor"
    if host_matches(host, ("open.spotify.com", "spotify.com")):
        return "Spotify"
    if host_matches(host, ("castbox.fm",)):
        return "Castbox"
    if host_matches(host, ("buzzsprout.com",)):
        return "Buzzsprout"
    if host_matches(host, ("podbean.com", "feed.podbean.com")):
        return "Podbean"
    if is_podcast_feed_url(url):
        return "Podcast feed"
    return "Unknown"


def parse_rss_episodes(text: str, limit: Optional[int] = None) -> List[PodcastEpisode]:
    """Parse RSS/Atom episodes into a list.

    Parameters
    ----------
    text : str
        Raw RSS/Atom XML.
    limit : int, optional
        Maximum episodes to return.

    Returns
    -------
    list of PodcastEpisode
        Episodes with ``title`` and enclosure ``url`` when present.
    """
    import xml.etree.ElementTree as ET

    from smart_dl.extractors.podcast import (
        _get_atom_link,
        _get_enclosure_url,
        _get_text,
        _parse_rss_regex,
    )

    items: List[PodcastEpisode] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        for title, url in _parse_rss_regex(text):
            items.append(PodcastEpisode(title=title, url=url))
        return items[:limit] if limit else items

    for item in root.iter("item"):
        title = _get_text(item, "title", "Episode")
        url = _get_enclosure_url(item)
        if url:
            items.append(PodcastEpisode(title=title, url=url))

    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = _get_text(entry, "{http://www.w3.org/2005/Atom}title", "Episode")
        url = _get_atom_link(entry)
        if url:
            items.append(PodcastEpisode(title=title, url=url))

    return items[:limit] if limit else items


def rss_from_platform_url(url: str, html: str = "") -> Optional[str]:
    """Best-effort: find a direct RSS feed URL from a platform page.

    Parameters
    ----------
    url : str
        Platform page URL.
    html : str, optional
        Already-fetched HTML.

    Returns
    -------
    str or None
        Absolute RSS URL when discoverable.
    """
    import re

    if is_podcast_feed_url(url) and url.lower().endswith((".xml", ".rss")):
        return url

    if not html:
        return None

    # <link rel="alternate" type="application/rss+xml" href="...">
    match = re.search(
        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if not match:
        match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
            html,
            re.I,
        )
    if match:
        from urllib.parse import urljoin

        return urljoin(url, match.group(1))
    return None
