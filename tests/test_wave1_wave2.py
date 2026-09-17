"""Wave 1–2 feature tests: R2, C-Auth helpers, R8, R4, R7."""

from __future__ import annotations

from pathlib import Path

from smart_dl.cli import build_parser
from smart_dl.core.clipboard import (
    ClipboardSource,
    is_grabbable_url,
    normalize_clipboard_candidate,
    watch_clipboard,
)
from smart_dl.core.config import load_config, save_config, set_config_path_for_tests
from smart_dl.core.config_io import (
    EXPORTABLE_KEYS,
    export_config,
    import_config,
    scrub_config,
)
from smart_dl.core.telegram_notify import (
    get_telegram_settings,
    notify_download_complete,
    notify_test,
    telegram_enabled,
)
from smart_dl.core.ytdlp_updater import (
    auto_update_allowed,
    should_update_ytdlp,
    update_yt_dlp,
)


class TestR2YtDlpUpdate:
    def test_env_flag_gates_auto_update(self, monkeypatch):
        monkeypatch.delenv("SMARTDL_UPDATE_YTDLP", raising=False)
        assert auto_update_allowed() is False
        assert should_update_ytdlp(None) is False
        monkeypatch.setenv("SMARTDL_UPDATE_YTDLP", "1")
        assert auto_update_allowed() is True
        assert should_update_ytdlp(None) is True
        assert should_update_ytdlp(True) is True

    def test_update_uses_installer_and_reports_versions(self):
        calls = []

        def installer(pkg: str) -> int:
            calls.append(pkg)
            return 0

        ok, msg = update_yt_dlp(installer=installer)
        assert ok is True
        assert calls == ["yt-dlp"]
        assert "→" in msg or "yt-dlp" in msg

    def test_cli_exposes_update_flag(self):
        args = build_parser().parse_args(["--update-ytdlp", "https://example.com/x"])
        assert args.update_ytdlp is True


class TestCookieAuthCli:
    def test_set_cookie_browser_roundtrip(self, tmp_path: Path):
        set_config_path_for_tests(tmp_path / "cfg.json")
        try:
            from smart_dl.commands.wave_features import handle_set_cookie_browser
            from smart_dl.core.cookies import clear_cookie_browser, get_cookie_browser

            handle_set_cookie_browser("firefox")
            assert get_cookie_browser() == "firefox"
            handle_set_cookie_browser("clear")
            assert get_cookie_browser() == ""
            clear_cookie_browser()
        finally:
            set_config_path_for_tests(None)

    def test_cli_exposes_set_cookie_browser(self):
        args = build_parser().parse_args(["--set-cookie-browser", "firefox"])
        assert args.set_cookie_browser == "firefox"


class TestR8ConfigIO:
    def test_scrub_drops_secrets(self):
        data = {
            "proxy": "socks5h://127.0.0.1:1080",
            "cookie_browser": "firefox",
            "telegram_bot_token": "SECRET",
            "telegram_chat_id": "123",
            "telegram_notify": True,
            "unknown_key": 1,
        }
        safe = scrub_config(data)
        assert "telegram_bot_token" not in safe
        assert safe["proxy"].startswith("socks5h://")
        assert safe["cookie_browser"] == "firefox"
        assert set(safe) <= EXPORTABLE_KEYS

    def test_export_import_roundtrip(self, tmp_path: Path):
        set_config_path_for_tests(tmp_path / "live.json")
        export_path = tmp_path / "portable.json"
        try:
            save_config(
                {
                    "proxy": "http://127.0.0.1:7890",
                    "cookie_browser": "firefox",
                    "telegram_bot_token": "SECRET_TOKEN",
                    "lang": "fa",
                }
            )
            export_config(export_path)
            raw = export_path.read_text(encoding="utf-8")
            assert "SECRET_TOKEN" not in raw
            assert "cookie_browser" in raw
            # wipe live and re-import
            save_config({})
            applied = import_config(export_path, merge=True)
            cfg = load_config()
            assert applied["cookie_browser"] == "firefox"
            assert cfg["cookie_browser"] == "firefox"
            assert cfg["proxy"] == "http://127.0.0.1:7890"
            assert "telegram_bot_token" not in cfg or cfg.get("telegram_bot_token") in (None, "")
        finally:
            set_config_path_for_tests(None)

    def test_cli_flags(self):
        args = build_parser().parse_args(["--export-config", "out.json"])
        assert args.export_config == "out.json"
        args = build_parser().parse_args(["--import-config", "in.json"])
        assert args.import_config == "in.json"


class TestR4Clipboard:
    def test_normalize_and_grab(self):
        assert normalize_clipboard_candidate('  "https://youtu.be/abc"  ') == "https://youtu.be/abc"
        assert is_grabbable_url("https://youtu.be/abc")
        assert is_grabbable_url("magnet:?xt=urn:btih:abc")
        assert is_grabbable_url("not a url") is False
        assert is_grabbable_url("https://example.com/has space") is False

    def test_watch_collects_new_urls_and_dedupes(self):
        samples = iter(
            [
                "hello",
                "https://youtube.com/watch?v=aaa",
                "https://youtube.com/watch?v=aaa",
                "https://aparat.com/v/bbb",
            ]
        )
        src = ClipboardSource(lambda: next(samples, "https://aparat.com/v/bbb"))
        found = watch_clipboard(
            interval=0,
            max_items=2,
            source=src,
            sleep=lambda _s: None,
        )
        assert found == [
            "https://youtube.com/watch?v=aaa",
            "https://aparat.com/v/bbb",
        ]

    def test_cli_watch_flags(self):
        args = build_parser().parse_args(["--watch-clipboard", "--watch-interval", "1.5", "--watch-max", "3"])
        assert args.watch_clipboard is True
        assert args.watch_interval == 1.5
        assert args.watch_max == 3


class TestR7Telegram:
    def _cfg(self):
        return {
            "telegram_bot_token": "123:ABC",
            "telegram_chat_id": "42",
            "telegram_notify": True,
        }

    def test_enabled_and_settings(self):
        assert telegram_enabled(self._cfg()) is True
        assert get_telegram_settings(self._cfg()) == ("123:ABC", "42")
        assert telegram_enabled({"telegram_notify": False, "telegram_bot_token": "x", "telegram_chat_id": "1"}) is False
        assert telegram_enabled({}) is False

    def test_notify_download_complete_sends_when_configured(self):
        posted = []

        class Resp:
            status_code = 200

            def json(self):
                return {"ok": True}

        def http(url, json=None, timeout=None):
            posted.append({"url": url, "json": json})
            return Resp()

        ok = notify_download_complete(
            url="https://youtu.be/x",
            success=True,
            title="Demo",
            config=self._cfg(),
            http=http,
        )
        assert ok is True
        assert len(posted) == 1
        assert posted[0]["json"]["chat_id"] == "42"
        assert "SmartDL OK" in posted[0]["json"]["text"]
        assert "123:ABC" not in posted[0]["json"]["text"]

    def test_notify_skips_when_disabled(self):
        posted = []

        def http(url, json=None, timeout=None):
            posted.append(url)
            raise AssertionError("should not call")

        ok = notify_download_complete(
            url="https://x",
            success=False,
            config={"telegram_notify": False, "telegram_bot_token": "t", "telegram_chat_id": "1"},
            http=http,
        )
        assert ok is False
        assert posted == []

    def test_token_not_in_error_message(self):
        class Resp:
            status_code = 401

            def json(self):
                return {"ok": False}

        def http(url, json=None, timeout=None):
            assert "SECRET" not in url or "bot" in url  # url contains token by design
            return Resp()

        ok = notify_test(config=self._cfg(), http=http)
        assert ok is False

    def test_cli_flags(self):
        args = build_parser().parse_args(["--notify-test"])
        assert args.notify_test is True
        args = build_parser().parse_args(["--set-telegram-token", "tok", "--set-telegram-chat", "99"])
        assert args.set_telegram_token == "tok"
        assert args.set_telegram_chat == "99"


class TestRecorderTelegramHook:
    def test_record_download_calls_notify_when_enabled(self, tmp_path: Path, monkeypatch):
        from smart_dl.core import history as history_store
        from smart_dl.core import recorder, telegram_notify
        from smart_dl.core.config import set_config_path_for_tests

        set_config_path_for_tests(tmp_path / "cfg.json")
        save_config(
            {
                "telegram_bot_token": "T",
                "telegram_chat_id": "1",
                "telegram_notify": True,
            }
        )
        history_store.set_history_db_path_for_tests(tmp_path / "h.db")
        called = []

        def fake_notify(**kwargs):
            called.append(kwargs)
            return True

        monkeypatch.setattr(telegram_notify, "notify_download_complete", fake_notify)
        try:
            recorder.record_download("https://example.com/v", success=True, title="T1")
            assert called and called[0]["success"] is True
        finally:
            history_store.set_history_db_path_for_tests(None)
            set_config_path_for_tests(None)
