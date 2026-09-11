"""Tests for history cleanup safety — preventing deletion of re-downloaded files."""

from pathlib import Path
from unittest.mock import patch

from smart_dl.core.manager import cleanup_downloads


def test_cleanup_skips_redownloaded_file(tmp_path: Path):
    """Test that cleanup_downloads does not delete files that were successfully re-downloaded."""
    test_file = tmp_path / "video.mp4"
    test_file.write_text("dummy content")

    failed_records = [{"id": 1, "file_path": str(test_file), "status": "failed"}]
    success_records = [{"id": 2, "file_path": str(test_file), "status": "success"}]

    def mock_get_history(status=None, limit=10000):
        if status == "failed":
            return failed_records
        if status == "success":
            return success_records
        return []

    with patch("smart_dl.core.history.get_history", side_effect=mock_get_history):
        cleaned = cleanup_downloads()
        assert cleaned == 0
        assert test_file.exists()


def test_cleanup_deletes_pure_failures(tmp_path: Path):
    """Test that cleanup_downloads removes files for pure failures without successful re-downloads."""
    test_file = tmp_path / "failed_video.mp4"
    test_file.write_text("dummy content")

    failed_records = [{"id": 1, "file_path": str(test_file), "status": "failed"}]

    def mock_get_history(status=None, limit=10000):
        if status == "failed":
            return failed_records
        if status == "success":
            return []
        return []

    with patch("smart_dl.core.history.get_history", side_effect=mock_get_history):
        cleaned = cleanup_downloads()
        assert cleaned == 1
        assert not test_file.exists()
