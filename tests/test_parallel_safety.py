"""Tests for parallel download safety — decode_content and thread isolation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from smart_dl.core.parallel import _copy_one, parallel_downloads


def test_copy_one_sets_decode_content(tmp_path: Path):
    """Test that _copy_one sets decode_content=True on the raw response stream."""
    mock_raw = MagicMock()
    mock_raw.read.side_effect = [b"content data", b""]
    mock_raw.decode_content = False

    mock_resp = MagicMock()
    mock_resp.raw = mock_raw
    mock_resp.status_code = 200

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    dest = tmp_path / "test.file"
    res = _copy_one("http://example.com/file", dest, session=mock_session)

    assert res == dest
    assert mock_raw.decode_content is True


def test_parallel_downloads_creates_per_thread_sessions(tmp_path: Path):
    """Test that parallel_downloads creates thread-isolated requests sessions."""
    urls = [f"http://example.com/file{i}" for i in range(5)]

    with patch("smart_dl.core.parallel.requests.Session") as mock_session_cls, \
         patch("smart_dl.core.parallel._copy_one") as mock_copy:
        mock_copy.return_value = tmp_path / "file"
        parallel_downloads(urls, tmp_path, workers=3)

        # Should create dedicated Session per thread
        assert mock_session_cls.call_count >= 3
