"""Wiring tests: browser cookies / cookies.txt must reach yt-dlp options."""

from __future__ import annotations

from pathlib import Path

from smart_dl.core.config import set_config_path_for_tests
from smart_dl.core.cookies import clear_cookie_browser, set_cookie_browser
from smart_dl.core.cookies_file import set_cookies_file
from smart_dl.core.downloader import build_download_opts
from smart_dl.core.engine import build_yt_opts, create_ydl_instance


def test_browser_cookie_injected_into_ydl_opts(tmp_path: Path) -> None:
    set_config_path_for_tests(tmp_path / "cfg.json")
    try:
        set_cookie_browser("firefox")
        opts = build_download_opts(fmt="best")
        assert opts.get("cookiesfrombrowser") == ("firefox", None, None, None)

        engine_opts = build_yt_opts(tmp_path, fmt="best")
        assert engine_opts.get("cookiesfrombrowser") == ("firefox", None, None, None)

        ydl = create_ydl_instance()
        assert ydl.params.get("cookiesfrombrowser") == ("firefox", None, None, None)
    finally:
        clear_cookie_browser()
        set_config_path_for_tests(None)


def test_cookies_file_used_when_no_browser(tmp_path: Path) -> None:
    set_config_path_for_tests(tmp_path / "cfg.json")
    cookies_txt = tmp_path / "cookies.txt"
    cookies_txt.write_text(
        "# Netscape HTTP Cookie File\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1893456000\tGPS\t1\n",
        encoding="utf-8",
    )
    try:
        clear_cookie_browser()
        assert set_cookies_file(str(cookies_txt)) is True
        opts = build_download_opts(fmt="best")
        assert opts.get("cookiefile") == str(cookies_txt)
        assert "cookiesfrombrowser" not in opts
    finally:
        set_cookies_file("")
        set_config_path_for_tests(None)


def test_browser_wins_over_cookies_file(tmp_path: Path) -> None:
    set_config_path_for_tests(tmp_path / "cfg.json")
    cookies_txt = tmp_path / "cookies.txt"
    cookies_txt.write_text(
        "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1893456000\tGPS\t1\n",
        encoding="utf-8",
    )
    try:
        set_cookies_file(str(cookies_txt))
        set_cookie_browser("edge")
        opts = build_download_opts(fmt="best")
        assert opts.get("cookiesfrombrowser") == ("edge", None, None, None)
        # Documented priority: configured browser first, cookies.txt only as fallback.
        assert opts.get("cookiefile") is None
    finally:
        clear_cookie_browser()
        set_cookies_file("")
        set_config_path_for_tests(None)
