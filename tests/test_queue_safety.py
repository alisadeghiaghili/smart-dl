"""Tests for queue state handling during interruptions."""

from unittest.mock import patch

import pytest

from smart_dl.core.queue import process_queue


def test_queue_ctrl_c_resets_item_to_pending():
    """Test that KeyboardInterrupt during queue processing resets active item back to pending."""
    mock_item = {"id": 42, "url": "http://example.com", "output_dir": "/tmp", "quality": "best", "audio_only": False}

    with patch("smart_dl.core.queue.get_next_pending", side_effect=[mock_item, None]), \
         patch("smart_dl.core.queue.update_queue_status") as mock_update:

        def mock_download(*args, **kwargs):
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            process_queue(mock_download)

        mock_update.assert_any_call(42, "active")
        mock_update.assert_any_call(42, "pending")
