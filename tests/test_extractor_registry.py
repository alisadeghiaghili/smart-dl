"""Tests for extractor registry routing."""

from __future__ import annotations

from smart_dl.extractors.registry import (
    ExtractorKind,
    describe_routes,
    resolve_extractor_kind,
    resolve_route,
)


def test_youtube_and_aparat_routes():
    assert resolve_extractor_kind("https://www.youtube.com/watch?v=abc") == ExtractorKind.YOUTUBE
    assert resolve_extractor_kind("https://aparat.com/v/xyz") == ExtractorKind.APARAT


def test_playlist_routes_prefer_platform():
    assert (
        resolve_extractor_kind("https://www.youtube.com/playlist?list=PL1")
        == ExtractorKind.PLAYLIST_YOUTUBE
    )
    assert (
        resolve_extractor_kind("https://aparat.com/playlist/abc")
        == ExtractorKind.PLAYLIST_APARAT
    )


def test_podcast_education_course_routes():
    assert resolve_extractor_kind("https://example.com/feed.mp3") == ExtractorKind.PODCAST
    assert (
        resolve_extractor_kind("https://maktabkhooneh.org/course/demo/")
        == ExtractorKind.EDUCATION
    )
    assert resolve_extractor_kind("https://www.udemy.com/course/demo") == ExtractorKind.COURSE


def test_force_gallery_and_general_fallback():
    assert (
        resolve_extractor_kind("https://example.com/x", force_gallery=True)
        == ExtractorKind.GALLERY
    )
    # Unknown host falls through to general (yt-dlp) path.
    assert resolve_extractor_kind("https://example.com/page") == ExtractorKind.GENERAL
    route = resolve_route("https://example.com/page")
    assert route.kind == ExtractorKind.GENERAL
    assert route.name


def test_describe_routes_in_match_order():
    labels = describe_routes()
    assert labels[0].startswith(ExtractorKind.TORRENT)
    assert any(ExtractorKind.YOUTUBE in item for item in labels)
    assert labels[-1].startswith(ExtractorKind.GENERAL)
