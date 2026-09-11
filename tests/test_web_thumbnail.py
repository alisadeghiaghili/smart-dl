"""Tests for Web UI thumbnail selection handling None dimensions."""

from smart_dl.web import _best_thumbnail


def test_best_thumbnail_handles_none_dimensions():
    """Test that _best_thumbnail handles None values for width and height."""
    thumbs = [
        {"url": "http://example.com/thumb1.jpg", "width": None, "height": 100},
        {"url": "http://example.com/thumb2.jpg", "width": 640, "height": 480},
        {"url": "http://example.com/thumb3.jpg", "width": 1280, "height": None},
    ]

    best = _best_thumbnail(thumbs)
    assert best is not None
    assert best["url"] == "http://example.com/thumb2.jpg"


def test_best_thumbnail_empty_list():
    """Test that _best_thumbnail returns None for empty list."""
    assert _best_thumbnail([]) is None
