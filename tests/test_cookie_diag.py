"""Unit tests for cookie diagnostic report."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"


class TestCookieDiagnose:
    def test_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import cookie_diag

        monkeypatch.setattr(
            "smart_dl.core.cookies.get_cookie_browser", lambda: ""
        )
        report = cookie_diag.cookie_diagnose_report()
        assert report["configured"] is False
        assert "no cookie browser" in str(report["error"])

    def test_counts_by_domain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from http.cookiejar import Cookie

        from smart_dl.core import cookie_diag

        monkeypatch.setattr(
            "smart_dl.core.cookies.get_cookie_browser", lambda: "firefox"
        )

        def _c(domain: str) -> Cookie:
            return Cookie(
                0, "n", "1", None, False, domain, True, domain.startswith("."),
                "/", True, False, None, True, None, None, {},
            )

        jar = [
            _c(".youtube.com"),
            _c(".maktabkhooneh.org"),
            _c(".example.com"),
        ]
        with patch(
            "yt_dlp.cookies.extract_cookies_from_browser", return_value=jar
        ):
            report = cookie_diag.cookie_diagnose_report()
        assert report["configured"] is True
        assert report["extract_ok"] is True
        assert report["total_cookies"] == 3
        assert report["by_domain"]["youtube.com"] == 1
        assert report["by_domain"]["maktabkhooneh.org"] == 1
        assert report["by_domain"]["coursera.org"] == 0

    def test_extract_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import cookie_diag

        monkeypatch.setattr(
            "smart_dl.core.cookies.get_cookie_browser", lambda: "chrome"
        )
        with patch(
            "yt_dlp.cookies.extract_cookies_from_browser",
            side_effect=RuntimeError("locked"),
        ):
            report = cookie_diag.cookie_diagnose_report()
        assert report["extract_ok"] is False
        assert "locked" in str(report["error"])
