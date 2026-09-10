"""Unit tests for browser cookie session helpers."""

from __future__ import annotations

import os
import sys
from http.cookiejar import Cookie
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"


class TestBrowserCookieSession:
    def test_no_browser_returns_empty_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import browser_cookies as bc

        monkeypatch.setattr(bc, "get_cookie_browser", lambda: "")
        session = bc.session_with_browser_cookies()
        assert len(session.cookies) == 0

    def test_import_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import browser_cookies as bc

        monkeypatch.setattr(bc, "get_cookie_browser", lambda: "firefox")

        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "yt_dlp.cookies":
                raise ImportError("no cookies module")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        session = bc.session_with_browser_cookies()
        assert len(session.cookies) == 0

    def test_filters_domains(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from smart_dl.core import browser_cookies as bc

        monkeypatch.setattr(bc, "get_cookie_browser", lambda: "chrome")

        def _cookie(domain: str, name: str) -> Cookie:
            return Cookie(
                version=0,
                name=name,
                value="1",
                port=None,
                port_specified=False,
                domain=domain,
                domain_specified=bool(domain),
                domain_initial_dot=domain.startswith("."),
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=True,
                comment=None,
                comment_url=None,
                rest={},
                rfc2109=False,
            )

        jar = MagicMock()
        jar.__iter__ = lambda self: iter(
            [
                _cookie(".coursera.org", "CAUTH"),
                _cookie(".example.com", "other"),
            ]
        )
        with patch(
            "smart_dl.core.browser_cookies.extract_cookies_from_browser",
            create=True,
        ):
            # Patch inside function via module path used in import
            with patch("yt_dlp.cookies.extract_cookies_from_browser", return_value=jar):
                session = bc.session_with_browser_cookies(
                    "chrome", domains=["coursera.org"]
                )
        names = {c.name for c in session.cookies}
        assert "CAUTH" in names
        assert "other" not in names
