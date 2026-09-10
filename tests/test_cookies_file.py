"""Unit tests for Netscape cookies.txt helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

NETSCAPE = (
    "# Netscape HTTP Cookie File\n"
    ".youtube.com\tTRUE\t/\tFALSE\t1893456000\tSID\tabc123\n"
    ".youtube.com\tTRUE\t/\tFALSE\t1893456000\tHSID\tdef456\n"
    "example.com\tFALSE\t/\tFALSE\t1893456000\tx\ty\n"
)


class TestNetscapeCookies:
    def test_load_and_count(self, tmp_path: Path) -> None:
        from smart_dl.core.cookies_file import (
            count_cookies_for_domain,
            load_netscape_cookies,
        )

        path = tmp_path / "cookies.txt"
        path.write_text(NETSCAPE, encoding="utf-8")
        ok, msg = load_netscape_cookies(str(path))
        assert ok is True
        assert "3" in msg or "2" in msg
        assert count_cookies_for_domain(str(path), "youtube.com") == 2

    def test_missing_file(self, tmp_path: Path) -> None:
        from smart_dl.core.cookies_file import load_netscape_cookies

        ok, msg = load_netscape_cookies(str(tmp_path / "nope.txt"))
        assert ok is False
        assert "not found" in msg

    def test_no_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import cookies_file as cf

        monkeypatch.setattr(cf, "get_cookies_file", lambda: "")
        ok, msg = cf.load_netscape_cookies()
        assert ok is False
        assert "cookies-file" in msg
