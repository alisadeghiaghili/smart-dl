"""Tests for core module logic fixes: config safety, utils, retry, sub_updates, and queue."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from smart_dl.core.config import load_config, save_config
from smart_dl.core.retry import retry_with_backoff
from smart_dl.utils import fmt_dur, safe_filename


def test_load_config_handles_corrupted_json(tmp_path: Path):
    """Test that load_config returns empty dict without crashing on malformed JSON."""
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("{corrupted: json...", encoding="utf-8")

    with patch("smart_dl.core.config._config_path_override", cfg_file):
        cfg = load_config()
        assert cfg == {}


def test_save_config_preserves_persian_characters(tmp_path: Path):
    """Test that save_config writes Persian Unicode characters without escaping."""
    cfg_file = tmp_path / "config.json"
    data = {"download_dir": "C:/دانلودهای من/ویدیو"}

    with patch("smart_dl.core.config._config_path_override", cfg_file):
        save_config(data)
        raw_text = cfg_file.read_text(encoding="utf-8")
        assert "دانلودهای من" in raw_text


def test_fmt_dur_zero():
    """Test that fmt_dur(0) returns '00:00:00' instead of '?'."""
    assert fmt_dur(0) == "00:00:00"
    assert fmt_dur(0.0) == "00:00:00"
    assert fmt_dur(None) == "?"


def test_safe_filename_windows_reserved():
    """Test sanitizing Windows reserved filenames and trailing dots."""
    assert safe_filename("CON") == "_CON"
    assert safe_filename("nul.txt") == "_nul.txt"
    assert safe_filename("my_file....") == "my_file"


def test_retry_skips_non_retryable_errors():
    """Test that retry_with_backoff immediately propagates non-retryable errors."""
    mock_fn = MagicMock(side_effect=PermissionError("Access denied"))

    with pytest.raises(PermissionError):
        retry_with_backoff(mock_fn, max_retries=5)

    assert mock_fn.call_count == 1
