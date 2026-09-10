"""Unit tests for subscription update detection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.core import sub_updates  # noqa: E402
from smart_dl.core import subscriptions as store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path):
    store.set_subscriptions_db_path_for_tests(tmp_path / "subs.db")
    store.init_db()
    yield
    store.set_subscriptions_db_path_for_tests(None)


FAKE_UPLOADS = [
    {"id": "aaa", "url": "https://www.youtube.com/watch?v=aaa", "title": "New A"},
    {"id": "bbb", "url": "https://www.youtube.com/watch?v=bbb", "title": "Old B"},
]


class TestNormalizeChannelFeedUrl:
    def test_handle_appends_videos(self) -> None:
        url = "https://www.youtube.com/@somechannel"
        assert sub_updates.normalize_channel_feed_url(url).endswith("/videos")

    def test_keeps_playlist(self) -> None:
        url = "https://www.youtube.com/playlist?list=PL123"
        assert sub_updates.normalize_channel_feed_url(url) == url

    def test_keeps_already_videos(self) -> None:
        url = "https://www.youtube.com/@ch/videos"
        assert sub_updates.normalize_channel_feed_url(url) == url


class TestCheckSubscription:
    def test_detects_new_uploads(self) -> None:
        sub_id = store.add_subscription("https://www.youtube.com/@demo", name="Demo")
        found = sub_updates.check_subscription(sub_id, lister=lambda _u: FAKE_UPLOADS)
        assert len(found) == 2
        assert found[0].video_id == "aaa"

    def test_marks_known_after_download(self) -> None:
        sub_id = store.add_subscription("https://www.youtube.com/@demo")
        store.add_subscription_video(
            sub_id,
            "https://www.youtube.com/watch?v=bbb",
            video_title="Old B",
            video_id="bbb",
        )
        found = sub_updates.check_subscription(sub_id, lister=lambda _u: FAKE_UPLOADS)
        assert [u.video_id for u in found] == ["aaa"]

    def test_skips_disabled(self) -> None:
        sub_id = store.add_subscription("https://www.youtube.com/@off")
        store.toggle_subscription(sub_id, enabled=False)
        found = sub_updates.check_subscription(sub_id, lister=lambda _u: FAKE_UPLOADS)
        assert found == []

    def test_all_subscriptions(self) -> None:
        store.add_subscription("https://www.youtube.com/@one")
        store.add_subscription("https://www.youtube.com/@two")
        result = sub_updates.check_all_subscriptions(lister=lambda _u: FAKE_UPLOADS)
        assert result["checked"] == 2
        assert result["total_new"] == 4  # 2 each
