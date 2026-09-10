"""Unit tests for podcast platform detection and RSS episodes."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.podcast_meta import (  # noqa: E402
    detect_podcast_platform,
    is_podcast_feed_url,
    is_podcast_platform_url,
    parse_rss_episodes,
    rss_from_platform_url,
)

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Show</title>
<item><title>Ep 1</title>
  <enclosure url="https://cdn.example.com/ep1.mp3" type="audio/mpeg"/>
</item>
<item><title>Ep 2</title>
  <enclosure url="https://cdn.example.com/ep2.mp3" type="audio/mpeg"/>
</item>
<item><title>No enclosure</title></item>
</channel></rss>
"""


class TestPlatformDetection:
    def test_soundcloud(self) -> None:
        assert is_podcast_platform_url("https://soundcloud.com/user/track") is True
        assert detect_podcast_platform("https://soundcloud.com/user/track") == "SoundCloud"

    def test_anchor_spotify(self) -> None:
        assert detect_podcast_platform("https://anchor.fm/s/show") == "Anchor"
        assert detect_podcast_platform("https://open.spotify.com/show/abc") == "Spotify"

    def test_rejects_lookalike(self) -> None:
        assert is_podcast_platform_url("https://soundcloud.com.evil.com/x") is False

    def test_feed_url(self) -> None:
        assert is_podcast_feed_url("https://example.com/feed.xml") is True
        assert is_podcast_feed_url("https://example.com/x.mp3") is True
        assert is_podcast_feed_url("https://example.com/page", ct="application/rss+xml") is True


class TestParseRss:
    def test_enclosures(self) -> None:
        eps = parse_rss_episodes(RSS)
        assert len(eps) == 2
        assert eps[0].title == "Ep 1"
        assert eps[0].url.endswith("ep1.mp3")

    def test_limit(self) -> None:
        assert len(parse_rss_episodes(RSS, limit=1)) == 1

    def test_malformed_falls_back(self) -> None:
        broken = "<item><title>Hi</title><enclosure url='http://x/a.mp3'/></item>"
        eps = parse_rss_episodes(broken)
        assert len(eps) == 1


class TestRssFromPlatform:
    def test_link_alternate(self) -> None:
        html = (
            '<html><head><link rel="alternate" type="application/rss+xml" '
            'href="/feeds/show.xml"/></head></html>'
        )
        assert rss_from_platform_url("https://castbox.fm/show/1", html) == (
            "https://castbox.fm/feeds/show.xml"
        )

    def test_none_without_feed(self) -> None:
        assert rss_from_platform_url("https://castbox.fm/show/1", "<html></html>") is None
