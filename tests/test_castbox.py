"""Unit tests for Castbox page parsing."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.castbox import (  # noqa: E402
    castbox_episode_lessons,
    extract_castbox_audio_urls,
    extract_castbox_episode_paths,
    extract_castbox_rss_url,
    is_castbox_url,
)

SAMPLE = """
<html><head><title>Madarane | Castbox</title></head><body>
<a href="/episode/%D8%A7%D9%BE%DB%8C%D8%B2%D9%88%D8%AF-11-id2386830-id967731521">Ep</a>
<script>
window.__DATA__ = {"rss_url":"https%3A%2F%2Freggioiran.com%2Ffeed%2Fmp3%2F",
"audio":"https%3A%2F%2Fcdn.example.com%2FEpisod%2B11.mp3"};
</script>
<script type="application/ld+json">{"rss_url":"https://direct.example.com/feed.xml"}</script>
</body></html>
"""


class TestCastboxDetection:
    def test_hosts(self) -> None:
        assert is_castbox_url("https://castbox.fm/channel/id2386830") is True
        assert is_castbox_url("https://www.castbox.fm/episode/x-id1-id2") is True
        assert is_castbox_url("https://castbox.fm.evil.com/x") is False


class TestCastboxExtractors:
    def test_rss_url_decoded(self) -> None:
        rss = extract_castbox_rss_url(SAMPLE)
        assert rss is not None
        assert rss.startswith("http")
        assert "reggioiran.com" in rss or "direct.example.com" in rss

    def test_episode_paths(self) -> None:
        paths = extract_castbox_episode_paths(SAMPLE)
        assert len(paths) == 1
        assert paths[0].startswith("/episode/")
        assert "id967731521" in paths[0]

    def test_audio_urls(self) -> None:
        urls = extract_castbox_audio_urls(SAMPLE)
        assert any(u.endswith(".mp3") for u in urls)

    def test_episode_lessons(self) -> None:
        eps = castbox_episode_lessons(SAMPLE)
        assert len(eps) == 1
        assert eps[0].url.startswith("https://castbox.fm/episode/")
        assert eps[0].title
