"""Unit tests for SmartDL core modules."""
import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SMARTDL_NO_DEPS'] = '1'


class TestConfigPersistence:
    def test_load_empty(self):
        from smart_dl.core.config import load_config
        # Should not crash even if file doesn't exist
        cfg = load_config()
        assert isinstance(cfg, dict)

    def test_save_and_load(self):
        from smart_dl.core.config import save_config, load_config, _SMARTDL_CONFIG
        import shutil

        # Use temp dir for testing
        temp_dir = tempfile.mkdtemp()
        test_config = os.path.join(temp_dir, "config.json")

        # Patch the config path
        import smart_dl.core.config as config_mod
        original = config_mod._SMARTDL_CONFIG
        config_mod._SMARTDL_CONFIG = test_config

        try:
            save_config({"test": "value", "nested": {"key": 123}})
            loaded = load_config()
            assert loaded["test"] == "value"
            assert loaded["nested"]["key"] == 123
        finally:
            config_mod._SMARTDL_CONFIG = original
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_permission_error(self):
        from smart_dl.core.config import save_config
        # Should not crash on permission error
        save_config({"test": "value"})


class TestRetryLogic:
    def test_is_network_error(self):
        from smart_dl.core.retry import is_network_error
        assert is_network_error("Connection reset by peer") is True
        assert is_network_error("timeout error") is True
        assert is_network_error("ssl certificate error") is True
        assert is_network_error("Video unavailable") is False
        assert is_network_error("ffmpeg not found") is False

    def test_diagnose_error(self):
        from smart_dl.core.retry import diagnose_error
        assert diagnose_error(Exception("ffmpeg is not installed")) != ""
        assert diagnose_error(Exception("private video")) != ""
        assert diagnose_error(Exception("age-restricted")) != ""
        assert diagnose_error(Exception("random error")) == ""

    def test_fatal_errors_list(self):
        from smart_dl.core.retry import FATAL_ERRORS
        assert len(FATAL_ERRORS) > 0
        assert "private video" in [e.lower() for e in FATAL_ERRORS]

    def test_dns_keywords(self):
        from smart_dl.core.retry import DNS_KEYWORDS
        assert len(DNS_KEYWORDS) > 0
        assert "getaddrinfo" in DNS_KEYWORDS


class TestDownloader:
    def test_smart_mode_defaults(self):
        from smart_dl.core.downloader import get_smart_mode
        prefs = get_smart_mode()
        assert isinstance(prefs, dict)
        assert "quality" in prefs
        assert "format" in prefs

    def test_build_download_opts_basic(self):
        from smart_dl.core.downloader import build_download_opts
        opts = build_download_opts(fmt="bestvideo+bestaudio/best")
        assert opts["format"] == "bestvideo+bestaudio/best"
        assert opts["continuedl"] is True
        assert "retries" in opts

    def test_build_download_opts_audio(self):
        from smart_dl.core.downloader import build_download_opts
        opts = build_download_opts(is_audio=True, audio_format="flac", audio_quality="320")
        assert opts["postprocessors"]
        assert opts["postprocessors"][0]["preferredcodec"] == "flac"
        assert opts["postprocessors"][0]["preferredquality"] == "320"

    def test_build_download_opts_clip(self):
        from smart_dl.core.downloader import build_download_opts
        opts = build_download_opts(clip="00:01:30-00:05:00")
        assert opts["download_sections"] == {"*": "00:01:30-00:05:00"}

    def test_build_download_opts_sponsorblock(self):
        from smart_dl.core.downloader import build_download_opts
        opts = build_download_opts(sponsorblock=True)
        assert opts["sponsorblock_mark"] == ["all"]
        assert opts["remove_sponsorblock"] is True

    def test_build_download_opts_format(self):
        from smart_dl.core.downloader import build_download_opts
        opts = build_download_opts(output_format="mkv")
        assert opts["merge_output_format"] == "mkv"


class TestThemes:
    def test_themes_exist(self):
        from smart_dl.ui.themes import THEMES
        assert len(THEMES) >= 10

    def test_theme_structure(self):
        from smart_dl.ui.themes import THEMES
        for name, theme in THEMES.items():
            assert "border" in theme, f"Theme {name} missing border"
            assert "success" in theme, f"Theme {name} missing success"
            assert "error" in theme, f"Theme {name} missing error"

    def test_set_theme(self):
        from smart_dl.ui.themes import set_theme, get_theme, THEMES
        original = get_theme()
        set_theme("dracula")
        assert get_theme()["name"] == "Dracula"
        set_theme("default")
        assert get_theme()["name"] == "Default"


class TestI18n:
    def test_english(self):
        from smart_dl.lang import set_lang, t
        set_lang("en")
        assert t("download_complete") == "Download complete!"
        assert t("proxy_set") == "Proxy set:"

    def test_persian(self):
        from smart_dl.lang import set_lang, t
        set_lang("fa")
        assert t("download_complete") != "Download complete!"
        assert len(t("download_complete")) > 0

    def test_fallback(self):
        from smart_dl.lang import set_lang, t
        set_lang("en")
        result = t("nonexistent_key")
        assert result == "nonexistent_key"


class TestQueue:
    def test_init_db(self):
        from smart_dl.core.queue import init_db
        init_db()  # Should not crash

    def test_add_and_get(self):
        from smart_dl.core.queue import init_db, add_to_queue, get_queue, clear_queue
        init_db()
        clear_queue()
        count = add_to_queue(["https://example.com/test1", "https://example.com/test2"])
        assert count == 2
        items = get_queue()
        assert len(items) == 2
        clear_queue()

    def test_stats(self):
        from smart_dl.core.queue import init_db, add_to_queue, get_queue_stats, clear_queue
        init_db()
        clear_queue()
        add_to_queue(["https://example.com/test"])
        stats = get_queue_stats()
        assert stats["pending"] >= 1
        clear_queue()


class TestHistory:
    def test_init_db(self):
        from smart_dl.core.history import init_db
        init_db()

    def test_add_and_get(self):
        from smart_dl.core.history import init_db, add_to_history, get_history
        init_db()
        hist_id = add_to_history(
            url="https://example.com/test",
            title="Test Video",
            platform="youtube"
        )
        assert hist_id > 0
        rows = get_history()
        assert len(rows) >= 1

    def test_stats(self):
        from smart_dl.core.history import init_db, get_history_stats
        init_db()
        stats = get_history_stats()
        assert "total_downloads" in stats
        assert "total_size" in stats
