"""Unit tests for installer relaunch argv and queue integration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"


class TestRelaunchArgv:
    def test_uses_module_not_installer_path(self) -> None:
        from smart_dl.core.installer import build_relaunch_argv

        argv = build_relaunch_argv()
        assert argv[1] == "-m"
        assert argv[2] == "smart_dl"
        assert "installer" not in " ".join(argv)


class TestQueueStartIntegration:
    def test_process_queue_calls_download_fn(self, tmp_path: Path) -> None:
        from smart_dl.core import queue as queue_mod

        queue_mod.set_queue_db_path_for_tests(tmp_path / "queue.db")
        try:
            queue_mod.init_db()
            queue_mod.add_to_queue(["https://example.com/a", "https://example.com/b"])
            seen: list[str] = []

            def fake_download(item: dict) -> bool:
                seen.append(item["url"])
                return item["url"].endswith("/a")

            result = queue_mod.process_queue(fake_download)
            assert result["processed"] == 2
            assert result["completed"] == 1
            assert result["failed"] == 1
            assert seen == [
                "https://example.com/a",
                "https://example.com/b",
            ]
        finally:
            queue_mod.set_queue_db_path_for_tests(None)


class TestLangFallback:
    def test_fa_folder_keys_exist(self) -> None:
        from smart_dl.lang import _FA, set_lang, t

        set_lang("fa")
        try:
            assert t("output_folder") == _FA["output_folder"]
            assert "default_folder" in _FA
            assert t("default_folder") == _FA["default_folder"]
            # guide_* falls back to English when missing from FA
            assert t("guide_title") == "Quick Guide"
        finally:
            set_lang("en")
