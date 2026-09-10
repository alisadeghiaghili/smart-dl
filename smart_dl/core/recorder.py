"""Record download outcomes into history."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from smart_dl.core import history as history_store
from smart_dl.core.net_utils import url_host
from smart_dl.utils import is_aparat_url, is_youtube_url

__all__ = ["detect_platform_slug", "record_download"]


def detect_platform_slug(url: str) -> str:
    """Best-effort platform slug for history rows.

    Parameters
    ----------
    url : str
        Source URL.

    Returns
    -------
    str
        ``youtube``, ``aparat``, or the bare host (may be empty).
    """
    if is_youtube_url(url):
        return "youtube"
    if is_aparat_url(url):
        return "aparat"
    return url_host(url)


def record_download(
    url: str,
    *,
    success: bool,
    title: str = "",
    file_path: Optional[Path] = None,
    format_str: str = "",
    is_audio: bool = False,
    error: str = "",
) -> int:
    """Persist a download result.

    Parameters
    ----------
    url : str
        Source URL.
    success : bool
        Whether the download completed.
    title : str, optional
        Media title when known.
    file_path : pathlib.Path or str, optional
        Local output path when known.
    format_str : str, optional
        yt-dlp format selector.
    is_audio : bool, optional
        Audio-only download flag.
    error : str, optional
        Failure reason when ``success`` is ``False``.

    Returns
    -------
    int
        History row id.
    """
    history_store.init_db()
    path_str = str(file_path) if file_path else ""
    size = 0
    if path_str:
        try:
            size = Path(path_str).stat().st_size
        except OSError:
            size = 0
    return history_store.add_to_history(
        url=url,
        title=title,
        platform=detect_platform_slug(url),
        file_path=path_str,
        file_size=size,
        format_str=format_str,
        is_audio=is_audio,
        status="completed" if success else "failed",
        error="" if success else (error or "unknown error"),
    )
