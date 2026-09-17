"""Route URL downloads through the extractor registry (CLI/queue shared path)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from smart_dl.extractors.registry import ExtractorKind, resolve_route

__all__ = ["dispatch_url_download"]


def _quality_fmt(args: Any) -> str:
    from smart_dl.utils import quality_to_format

    quality = getattr(args, "quality", None) or "best"
    return quality_to_format(str(quality))


def dispatch_url_download(url: str, args: Any, out_folder: Path) -> bool:
    """Download *url* using registry routing and CLI feature flags.

    Parameters
    ----------
    url : str
        Absolute media URL.
    args : argparse.Namespace
        Parsed CLI arguments (feature flags).
    out_folder : pathlib.Path
        Destination directory.

    Returns
    -------
    bool
        ``True`` when the selected handler reports success.
    """
    from smart_dl.ui import info
    from smart_dl.utils import quality_to_format

    kind = resolve_route(url, force_gallery=bool(getattr(args, "gallery", False))).kind
    fmt = _quality_fmt(args)
    is_audio = bool(getattr(args, "audio_only", False))

    if kind == ExtractorKind.TORRENT:
        from smart_dl.extractors.torrent import download_torrent

        download_torrent(url, out_folder)
        return True

    if kind == ExtractorKind.GALLERY:
        from smart_dl.extractors.gallery import download_gallery

        download_gallery(url, out_folder)
        return True

    if kind == ExtractorKind.PLAYLIST_APARAT:
        from smart_dl.extractors.aparat import handle_aparat_playlist

        return bool(handle_aparat_playlist(url, out_folder))

    if kind == ExtractorKind.PLAYLIST_YOUTUBE:
        from smart_dl.extractors.youtube import handle_playlist

        return bool(
            handle_playlist(
                url,
                out_folder,
                audio_only=is_audio,
                quality=str(getattr(args, "quality", "best") or "best"),
                audio_format=str(getattr(args, "audio_format", "mp3") or "mp3"),
            )
        )

    if kind == ExtractorKind.APARAT:
        from smart_dl.extractors.aparat import download_aparat

        return bool(download_aparat(url, out_folder))

    if kind == ExtractorKind.YOUTUBE:
        from smart_dl.core.downloader import download_with_features

        return bool(
            _download_with_cli_flags(
                download_with_features,
                url,
                out_folder,
                args,
                fmt=fmt,
                is_audio=is_audio,
            )
        )

    if kind == ExtractorKind.PODCAST:
        from smart_dl.extractors.podcast import handle_podcast

        return bool(
            handle_podcast(
                url,
                out_folder,
                max_episodes=getattr(args, "max_episodes", None),
                download_all=bool(getattr(args, "all_episodes", False)),
            )
        )

    if kind == ExtractorKind.EDUCATION:
        from smart_dl.extractors.education import download_education_course

        if bool(getattr(args, "all", False)):
            max_lessons: Optional[int] = None
        elif getattr(args, "max_lessons", None) is not None:
            max_lessons = max(0, int(args.max_lessons))
        else:
            max_lessons = 20
        return bool(download_education_course(url, out_folder, max_lessons=max_lessons))

    if kind == ExtractorKind.PERSIAN:
        from smart_dl.extractors.persian import download_persian_platform

        return bool(download_persian_platform(url, out_folder))

    if kind == ExtractorKind.COURSE:
        from smart_dl.extractors.courses import download_course

        return bool(download_course(url, out_folder))

    from smart_dl.core.downloader import download_with_features
    from smart_dl.extractors.general import detect_platform

    platform = detect_platform(url)
    if platform:
        info(f"Detected: {platform}")
    return bool(
        _download_with_cli_flags(
            download_with_features,
            url,
            out_folder,
            args,
            fmt=fmt or quality_to_format("best"),
            is_audio=is_audio,
        )
    )


def _download_with_cli_flags(
    download_fn,
    url: str,
    out_folder: Path,
    args: Any,
    *,
    fmt: str,
    is_audio: bool,
) -> bool:
    """Call the shared download engine with CLI feature flags."""
    from smart_dl.core.rate_limit import parse_limit_rate

    rate_limit = parse_limit_rate(getattr(args, "limit_rate", None))
    return bool(
        download_fn(
            url,
            out_folder,
            fmt=fmt,
            is_audio=is_audio,
            clip=getattr(args, "clip", None),
            sponsorblock=bool(getattr(args, "sponsorblock", False)),
            audio_format=getattr(args, "audio_format", "mp3"),
            audio_quality=getattr(args, "audio_quality", "192"),
            output_format=getattr(args, "format", None),
            embed_metadata=bool(getattr(args, "embed_metadata", False)),
            embed_thumbnail=bool(getattr(args, "embed_thumbnail", False)),
            embed_subs=bool(getattr(args, "embed_subs", False)),
            geo_bypass=getattr(args, "geo_bypass", None),
            impersonate=getattr(args, "impersonate", None),
            output_template=getattr(args, "output_template", None),
            quiet=bool(getattr(args, "quiet", False)),
            rate_limit=rate_limit,
        )
    )
