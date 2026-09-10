"""Subscription update detection — find new uploads on followed channels."""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Sequence

from smart_dl.core import subscriptions as store
from smart_dl.utils import is_youtube_url

__all__ = [
    "NewUpload",
    "check_subscription",
    "check_all_subscriptions",
    "default_upload_lister",
    "normalize_channel_feed_url",
]

# Cap how many entries we inspect per channel so checks stay fast.
_DEFAULT_MAX_ENTRIES = 15


class NewUpload(dict):
    """A newly detected upload (dict subclass for easy JSON/CLI use)."""

    @property
    def url(self) -> str:
        return str(self.get("url") or "")

    @property
    def video_id(self) -> str:
        return str(self.get("video_id") or "")

    @property
    def title(self) -> str:
        return str(self.get("title") or "")


def normalize_channel_feed_url(url: str) -> str:
    """Return a URL yt-dlp can list for uploads.

    For YouTube channel/home URLs this appends ``/videos`` so flat
    extraction targets uploads rather than the channel landing page.

    Parameters
    ----------
    url : str
        Channel, playlist, or feed URL.

    Returns
    -------
    str
        Feed URL to list.
    """
    cleaned = (url or "").rstrip("/")
    if not cleaned:
        return cleaned
    if is_youtube_url(cleaned):
        path = cleaned.split("?", 1)[0]
        if path.endswith("/videos") or path.endswith("/shorts") or path.endswith("/streams"):
            return cleaned
        if "/playlist?" in cleaned or "list=" in cleaned:
            return cleaned
        if "/@" in path or "/channel/" in path or "/c/" in path or "/user/" in path:
            return path + "/videos"
    return cleaned


def default_upload_lister(url: str, *, limit: int = _DEFAULT_MAX_ENTRIES) -> List[dict]:
    """List recent uploads for *url* using yt-dlp flat extraction.

    Parameters
    ----------
    url : str
        Channel or playlist URL.
    limit : int, optional
        Maximum entries to return.

    Returns
    -------
    list of dict
        Items with keys ``id``, ``url``, ``title``. Empty list on failure.
    """
    try:
        import yt_dlp
    except ImportError:
        return []

    from smart_dl.core.proxy import get_current_proxy

    feed = normalize_channel_feed_url(url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "playlistend": max(1, int(limit)),
        "skip_download": True,
    }
    proxy = get_current_proxy()
    if proxy:
        opts["proxy"] = proxy
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(feed, download=False)
    except Exception:
        return []

    if not info:
        return []
    entries = info.get("entries") or []
    results: List[dict] = []
    for entry in entries:
        if not entry:
            continue
        vid = entry.get("id") or ""
        page = entry.get("url") or entry.get("webpage_url") or ""
        if not page and vid:
            page = "https://www.youtube.com/watch?v=" + vid
        results.append(
            {
                "id": vid,
                "url": page,
                "title": entry.get("title") or vid or "video",
            }
        )
    return results[:limit]


def _entry_ids(entries: Sequence[dict]) -> List[str]:
    return [str(e.get("id") or "") for e in entries if e.get("id")]


def check_subscription(
    sub_id: int,
    *,
    lister: Optional[Callable[[str], Iterable[dict]]] = None,
    max_entries: int = _DEFAULT_MAX_ENTRIES,
    mark_checked: bool = True,
) -> List[NewUpload]:
    """Return uploads for one subscription that have not been recorded yet.

    Parameters
    ----------
    sub_id : int
        Subscription row id.
    lister : Callable[[str], Iterable[dict]], optional
        Upload lister; defaults to :func:`default_upload_lister`.
    max_entries : int, optional
        How many recent entries to inspect.
    mark_checked : bool, optional
        Update ``last_checked`` / ``last_video_id`` when True.

    Returns
    -------
    list of NewUpload
        Newest-first uploads not present in subscription history.
    """
    lister = lister or (lambda u: default_upload_lister(u, limit=max_entries))
    store.init_db()
    sub = store.get_subscription_by_id(sub_id)
    if not sub or not sub.get("enabled", 1):
        return []

    url = sub["url"]
    entries = list(lister(url))
    known = set(store.get_subscription_video_ids(sub_id))
    known.add(sub.get("last_video_id") or "")

    new_uploads: List[NewUpload] = []
    for entry in entries:
        vid = str(entry.get("id") or "")
        if not vid or vid in known:
            continue
        page = entry.get("url") or (
            "https://www.youtube.com/watch?v=" + vid if vid else ""
        )
        if not page:
            continue
        new_uploads.append(
            NewUpload(
                url=page,
                video_id=vid,
                title=entry.get("title") or vid,
                sub_id=sub_id,
                subscription_url=url,
            )
        )

    if mark_checked and entries:
        newest = _entry_ids(entries)
        store.update_last_checked(sub_id, video_id=newest[0] if newest else "")
    elif mark_checked:
        store.update_last_checked(sub_id, video_id=sub.get("last_video_id") or "")

    return new_uploads


def check_all_subscriptions(
    *,
    lister: Optional[Callable[[str], Iterable[dict]]] = None,
    max_entries: int = _DEFAULT_MAX_ENTRIES,
) -> dict:
    """Check every enabled subscription for new uploads.

    Parameters
    ----------
    lister : Callable[[str], Iterable[dict]], optional
        Upload lister used for each subscription.
    max_entries : int, optional
        Entries inspected per subscription.

    Returns
    -------
    dict
        ``new_uploads`` (list of NewUpload), ``checked`` (int),
        ``by_subscription`` (dict sub_id → list of NewUpload).
    """
    store.init_db()
    subs = store.get_subscriptions(enabled_only=True)
    by_subscription: dict[int, List[NewUpload]] = {}
    new_uploads: List[NewUpload] = []
    for sub in subs:
        found = check_subscription(
            int(sub["id"]),
            lister=lister,
            max_entries=max_entries,
        )
        by_subscription[int(sub["id"])] = found
        new_uploads.extend(found)
    return {
        "checked": len(subs),
        "new_uploads": new_uploads,
        "by_subscription": by_subscription,
        "total_new": len(new_uploads),
    }


def record_subscription_download(
    sub_id: int,
    video_url: str,
    *,
    title: str = "",
    video_id: str = "",
) -> None:
    """Record that a subscription video was downloaded.

    Parameters
    ----------
    sub_id : int
        Subscription id.
    video_url : str
        Downloaded video URL.
    title : str, optional
        Video title.
    video_id : str, optional
        Platform video id (parsed from URL when omitted for YouTube).
    """
    if not video_id and is_youtube_url(video_url):
        from urllib.parse import parse_qs, urlparse

        video_id = parse_qs(urlparse(video_url).query).get("v", [""])[0]
    store.add_subscription_video(sub_id, video_url, title=title, video_id=video_id)
