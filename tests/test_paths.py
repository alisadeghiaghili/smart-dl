"""Unit tests for smart_dl.core.paths — unified data directory."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.core import paths  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_app_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point app root at a temp dir so tests never touch the real repo."""
    monkeypatch.setattr(paths, "get_app_root", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    yield tmp_path


class TestPortableMode:
    def test_not_portable_by_default(self, tmp_path: Path) -> None:
        assert paths.is_portable() is False

    def test_enable_and_disable(self, tmp_path: Path) -> None:
        marker = paths.enable_portable_mode()
        assert marker.exists()
        assert paths.is_portable() is True
        paths.disable_portable_mode()
        assert paths.is_portable() is False


class TestDataDir:
    def test_posix_uses_home_dot_smartdl(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "name", "posix")
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home"))
        (tmp_path / "home").mkdir()
        data = paths.get_data_dir()
        assert data == tmp_path / "home" / ".smartdl"
        assert data.is_dir()

    def test_portable_uses_app_root_data(self, tmp_path: Path) -> None:
        paths.enable_portable_mode()
        data = paths.get_data_dir()
        assert data == tmp_path / "data"
        assert data.is_dir()

    def test_windows_uses_appdata(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(os, "name", "nt")
        monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
        data = paths.get_data_dir()
        assert data == tmp_path / "AppData" / "SmartDL"
        assert data.is_dir()


class TestDbAndConfigPaths:
    def test_config_path_under_data(self, tmp_path: Path) -> None:
        paths.enable_portable_mode()
        assert paths.get_config_path() == tmp_path / "data" / "config.json"

    def test_db_path_appends_suffix(self, tmp_path: Path) -> None:
        paths.enable_portable_mode()
        assert paths.get_db_path("history") == tmp_path / "data" / "history.db"
        assert paths.get_db_path("queue.db") == tmp_path / "data" / "queue.db"
