"""CLI download orchestration helpers shared by queue and flag paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

__all__ = [
    "count_failure",
    "process_urls",
    "queue_download_item",
    "resolve_education_max_lessons",
]


def count_failure(ok: Any) -> int:
    """Return 1 when a download handler reports failure, else 0.

    Parameters
    ----------
    ok : bool or None
        Handler return value. ``None`` is treated as failure.

    Returns
    -------
    int
        0 or 1.

    Examples
    --------
    >>> count_failure(True), count_failure(False), count_failure(None)
    (0, 1, 1)
    """
    return 0 if ok is True else 1


def resolve_education_max_lessons(
    *,
    all_lessons: bool,
    max_lessons: Optional[int],
) -> Optional[int]:
    """Resolve the education lesson cap from CLI flags.

    Parameters
    ----------
    all_lessons : bool
        ``--all`` was passed (remove the cap).
    max_lessons : int, optional
        Explicit ``--max-lessons`` value.

    Returns
    -------
    int or None
        ``None`` means unlimited; otherwise a non-negative cap.

    Examples
    --------
    >>> resolve_education_max_lessons(all_lessons=True, max_lessons=5) is None
    True
    >>> resolve_education_max_lessons(all_lessons=False, max_lessons=None)
    20
    """
    if all_lessons:
        return None
    if max_lessons is not None:
        return max(0, int(max_lessons))
    return 20


def queue_download_item(item: dict, out_folder: Path) -> bool:
    """Download one queue row without opening interactive menus.

    Parameters
    ----------
    item : dict
        Queue row with ``url``, ``format_str``, ``is_audio``.
    out_folder : pathlib.Path
        Destination directory.

    Returns
    -------
    bool
        ``True`` on success.
    """
    from smart_dl.extractors.registry import ExtractorKind, resolve_extractor_kind
    from smart_dl.ui import info
    from smart_dl.ui.progress import stop_event
    from smart_dl.utils import quality_to_format

    url = item["url"]
    info(f"Queue #{item.get('id')}: {url[:80]}")
    stop_event.clear()
    fmt = item.get("format_str") or "best"
    is_audio = bool(item.get("is_audio"))
    if fmt in ("best", "", None):
        fmt = quality_to_format("best")

    out = Path(out_folder)
    kind = resolve_extractor_kind(url)

    if kind == ExtractorKind.EDUCATION:
        from smart_dl.extractors.education import download_education_course

        return bool(download_education_course(url, out, max_lessons=None))
    if kind == ExtractorKind.PODCAST:
        from smart_dl.extractors.podcast import download_podcast_url

        return bool(download_podcast_url(url, out))
    if kind == ExtractorKind.APARAT:
        from smart_dl.extractors.aparat import download_aparat

        return bool(download_aparat(url, out))
    if kind == ExtractorKind.PERSIAN:
        from smart_dl.extractors.persian import download_persian_platform

        return bool(download_persian_platform(url, out))
    if kind == ExtractorKind.COURSE:
        from smart_dl.extractors.courses import download_course

        return bool(download_course(url, out))

    from smart_dl.extractors.youtube import download_yt

    return bool(download_yt(url, out, str(fmt), is_audio))


def process_urls(urls: List[str], args: Any, out_folder: Path) -> None:
    """Process all URLs passed to CLI; exit 1 when any download failed.

    Parameters
    ----------
    urls : list of str
        Absolute media URLs.
    args : argparse.Namespace
        Parsed CLI arguments.
    out_folder : pathlib.Path
        Destination directory.

    Returns
    -------
    None
    """
    import sys

    from smart_dl.extractors.dispatch import dispatch_url_download
    from smart_dl.ui import error, success, warn

    failures = 0
    for url in urls:
        try:
            ok = dispatch_url_download(url, args, out_folder)
            if not ok:
                failures += 1
        except KeyboardInterrupt:
            warn("Interrupted.")
            break
        except Exception as exc:  # noqa: BLE001 — isolate per-URL failures
            error(f"Error: {str(exc)[:200]}")
            failures += 1

    if failures:
        error(f"Finished with {failures} failed download(s).")
        sys.exit(1)
    success("All done!")
