"""Extractor routing registry — single place to map URL → extractor kind.

Keeps CLI/queue/main from growing another if/elif chain every time a
platform is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from smart_dl.utils import (
    is_aparat_url,
    is_playlist_url,
    is_podcast_url,
    is_youtube_url,
)

__all__ = [
    "ExtractorKind",
    "ExtractorRoute",
    "ROUTES",
    "describe_routes",
    "resolve_extractor_kind",
    "resolve_route",
]


class ExtractorKind:
    """Canonical extractor kind identifiers."""

    SUBTITLE_LIST = "subtitle_list"
    SUBTITLE_DOWNLOAD = "subtitle_download"
    THUMBNAIL = "thumbnail"
    TORRENT = "torrent"
    GALLERY = "gallery"
    PLAYLIST_APARAT = "playlist_aparat"
    PLAYLIST_YOUTUBE = "playlist_youtube"
    APARAT = "aparat"
    YOUTUBE = "youtube"
    PODCAST = "podcast"
    EDUCATION = "education"
    PERSIAN = "persian"
    COURSE = "course"
    GENERAL = "general"


@dataclass(frozen=True)
class ExtractorRoute:
    """One routing rule.

    Attributes
    ----------
    kind : str
        :class:`ExtractorKind` value.
    name : str
        Human-readable label for diagnostics.
    matches : Callable[[str], bool]
        Predicate over the URL (may inspect path/host only).
    """

    kind: str
    name: str
    matches: Callable[[str], bool]


def _is_torrent(url: str) -> bool:
    from smart_dl.extractors.torrent import is_magnet_link, is_torrent_file

    return is_magnet_link(url) or is_torrent_file(url)


def _is_gallery(url: str) -> bool:
    from smart_dl.extractors.gallery import is_gallery_url

    return is_gallery_url(url)


def _is_podcast_any(url: str) -> bool:
    from smart_dl.extractors.podcast_meta import is_podcast_platform_url

    return is_podcast_url(url) or is_podcast_platform_url(url)


def _is_education(url: str) -> bool:
    from smart_dl.extractors.education import is_education_url

    return is_education_url(url)


def _is_persian(url: str) -> bool:
    from smart_dl.extractors.persian import is_persian_platform

    return is_persian_platform(url)


def _is_course(url: str) -> bool:
    from smart_dl.extractors.courses import is_course_url

    return is_course_url(url)


# Order matters: first match wins.
ROUTES: Sequence[ExtractorRoute] = (
    ExtractorRoute(ExtractorKind.TORRENT, "torrent/magnet", _is_torrent),
    ExtractorRoute(ExtractorKind.GALLERY, "image gallery", _is_gallery),
    ExtractorRoute(
        ExtractorKind.PLAYLIST_APARAT,
        "aparat playlist",
        lambda u: is_playlist_url(u) and is_aparat_url(u),
    ),
    ExtractorRoute(
        ExtractorKind.PLAYLIST_YOUTUBE,
        "playlist",
        is_playlist_url,
    ),
    ExtractorRoute(ExtractorKind.APARAT, "aparat", is_aparat_url),
    ExtractorRoute(ExtractorKind.YOUTUBE, "youtube", is_youtube_url),
    ExtractorRoute(ExtractorKind.PODCAST, "podcast", _is_podcast_any),
    ExtractorRoute(ExtractorKind.EDUCATION, "education course", _is_education),
    ExtractorRoute(ExtractorKind.PERSIAN, "persian platform", _is_persian),
    ExtractorRoute(ExtractorKind.COURSE, "online course host", _is_course),
    ExtractorRoute(ExtractorKind.GENERAL, "general/yt-dlp fallback", lambda _u: True),
)


def resolve_route(
    url: str,
    *,
    force_gallery: bool = False,
) -> ExtractorRoute:
    """Return the first matching :class:`ExtractorRoute` for *url*.

    Parameters
    ----------
    url : str
        Absolute media URL.
    force_gallery : bool, optional
        Treat the URL as a gallery even if host detection fails.

    Returns
    -------
    ExtractorRoute
        Matching route; ``GENERAL`` is the terminal fallback.

    Examples
    --------
    >>> resolve_route("https://www.youtube.com/watch?v=abc").kind
    'youtube'
    """
    if force_gallery:
        for route in ROUTES:
            if route.kind == ExtractorKind.GALLERY:
                return route
    for route in ROUTES:
        try:
            if route.matches(url):
                return route
        except Exception:
            continue
    for route in ROUTES:
        if route.kind == ExtractorKind.GENERAL:
            return route
    return ExtractorRoute(ExtractorKind.GENERAL, "general/yt-dlp fallback", lambda _u: True)


def resolve_extractor_kind(url: str, *, force_gallery: bool = False) -> str:
    """Return only the extractor kind string for *url*.

    Parameters
    ----------
    url : str
        Absolute media URL.
    force_gallery : bool, optional
        Force gallery routing.

    Returns
    -------
    str
        One of :class:`ExtractorKind` values.
    """
    return resolve_route(url, force_gallery=force_gallery).kind


def describe_routes() -> List[str]:
    """Return human-readable route labels in match order.

    Returns
    -------
    list of str
        ``"kind — name"`` entries.
    """
    return [f"{r.kind} — {r.name}" for r in ROUTES]


def optional_route(kind: str) -> Optional[ExtractorRoute]:
    """Look up a route by kind.

    Parameters
    ----------
    kind : str
        :class:`ExtractorKind` value.

    Returns
    -------
    ExtractorRoute or None
    """
    for route in ROUTES:
        if route.kind == kind:
            return route
    return None
