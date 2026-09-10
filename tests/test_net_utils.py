"""Unit tests for smart_dl.core.net_utils — host matching."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.core.net_utils import host_matches, normalize_host, url_host  # noqa: E402

YOUTUBE = ("youtube.com", "youtu.be", "m.youtube.com")


class TestNormalizeHost:
    def test_strips_www(self) -> None:
        assert normalize_host("www.YouTube.com") == "youtube.com"

    def test_strips_port(self) -> None:
        assert normalize_host("youtube.com:443") == "youtube.com"

    def test_strips_credentials(self) -> None:
        assert normalize_host("user:pass@youtube.com") == "youtube.com"

    def test_empty(self) -> None:
        assert normalize_host("") == ""


class TestUrlHost:
    def test_basic(self) -> None:
        assert url_host("https://www.youtube.com/watch?v=abc") == "youtube.com"

    def test_youtu_be(self) -> None:
        assert url_host("https://youtu.be/abc") == "youtu.be"


class TestHostMatches:
    def test_exact(self) -> None:
        assert host_matches("youtube.com", YOUTUBE) is True

    def test_subdomain(self) -> None:
        assert host_matches("music.youtube.com", YOUTUBE) is True

    def test_www_prefix(self) -> None:
        assert host_matches("www.youtube.com", YOUTUBE) is True

    def test_rejects_substring_lookalike(self) -> None:
        assert host_matches("evil-youtube.com.attacker.net", YOUTUBE) is False

    def test_rejects_suffix_spoof(self) -> None:
        assert host_matches("youtube.com.evil.com", YOUTUBE) is False

    def test_rejects_notyoutube(self) -> None:
        assert host_matches("notyoutube.com", YOUTUBE) is False

    def test_aparat(self) -> None:
        assert host_matches("www.aparat.com", ("aparat.com",)) is True
        assert host_matches("evil-aparat.com.br", ("aparat.com",)) is False
