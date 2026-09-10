"""Unit tests for platform detection cleanup."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.extractors.general import PERSIAN_PLATFORMS, detect_platform  # noqa: E402


class TestDetectPlatform:
    def test_aparat(self) -> None:
        assert detect_platform("https://www.aparat.com/v/abc") == "Aparat"

    def test_udemy_subdomain(self) -> None:
        assert detect_platform("https://www.udemy.com/course/foo/") == "Udemy"

    def test_rejects_junk_hosts(self) -> None:
        assert detect_platform("https://trello.com/b/xyz") is None
        assert detect_platform("https://www.vidio.com/live/1") is None

    def test_rejects_lookalike(self) -> None:
        assert detect_platform("https://evil-aparat.com.attacker.net/v") is None

    def test_mapping_has_no_trello(self) -> None:
        assert "trello.com" not in PERSIAN_PLATFORMS
        assert "vidio.com" not in PERSIAN_PLATFORMS
        assert "aion.iran" not in PERSIAN_PLATFORMS
