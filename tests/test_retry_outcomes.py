"""Unit tests for smart_dl.core.retry — terminal outcomes must raise."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SMARTDL_NO_DEPS"] = "1"

from smart_dl.core import retry  # noqa: E402
from smart_dl.ui.progress import stop_event  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_stop():
    stop_event.clear()
    yield
    stop_event.clear()


class TestRetryGaveUp:
    def test_success_passthrough(self) -> None:
        assert retry.retry_with_backoff(lambda: "ok", base_delay=0, max_retries=1) == "ok"

    def test_fatal_raises_original(self) -> None:
        def boom():
            raise RuntimeError("Private video")

        with pytest.raises(RuntimeError, match="Private video"):
            retry.retry_with_backoff(boom, base_delay=0, max_retries=3)

    def test_dns_raises_retry_gave_up(self) -> None:
        def boom():
            raise OSError("getaddrinfo failed youtube.com")

        with pytest.raises(retry.RetryGaveUp) as exc_info:
            retry.retry_with_backoff(boom, base_delay=0, max_retries=5, sleep=lambda _s: None)
        assert exc_info.value.reason == "dns"

    def test_duration_cap_raises(self) -> None:
        calls = {"n": 0}

        def boom():
            calls["n"] += 1
            raise ConnectionError("connection reset by peer")

        with pytest.raises(retry.RetryGaveUp) as exc_info:
            retry.retry_with_backoff(
                boom,
                base_delay=0,
                max_retries=999,
                max_duration=0,
                sleep=lambda _s: None,
            )
        assert exc_info.value.reason == "duration"
        assert calls["n"] >= 1

    def test_stop_event_raises_stopped(self) -> None:
        stop_event.set()
        with pytest.raises(retry.RetryGaveUp) as exc_info:
            retry.retry_with_backoff(lambda: 1, base_delay=0)
        assert exc_info.value.reason == "stopped"


class TestClassifiers:
    def test_is_network_error(self) -> None:
        assert retry.is_network_error("Connection reset by peer") is True
        assert retry.is_network_error("Video unavailable") is False

    def test_diagnose_error(self) -> None:
        assert retry.diagnose_error(Exception("ffmpeg is not installed"))
        assert retry.diagnose_error(Exception("totally unknown xyz")) == ""


class TestUtilsQualityAndHosts:
    def test_is_youtube_rejects_spoof(self) -> None:
        from smart_dl.utils import is_youtube_url

        assert is_youtube_url("https://www.youtube.com/watch?v=a") is True
        assert is_youtube_url("https://evil-youtube.com.attacker.net/x") is False
        assert is_youtube_url("https://youtube.com.evil.com/x") is False

    def test_is_aparat_rejects_spoof(self) -> None:
        from smart_dl.utils import is_aparat_url

        assert is_aparat_url("https://www.aparat.com/v/abc") is True
        assert is_aparat_url("https://notaparat.com.evil.net/v") is False

    def test_quality_presets(self) -> None:
        from smart_dl.utils import quality_to_format

        assert quality_to_format("4k") == "bestvideo[height<=2160]+bestaudio/best"
        assert quality_to_format("8k") == "bestvideo[height<=4320]+bestaudio/best"
        assert quality_to_format("worst") == "worstvideo+worstaudio/worst"
        assert quality_to_format("1080") == "bestvideo[height<=1080]+bestaudio/best"
        assert quality_to_format("nope") == "bestvideo+bestaudio/best"

    def test_safe_filename_reserved(self) -> None:
        from smart_dl.utils import safe_filename

        assert safe_filename("CON") == "_CON"
        assert safe_filename("Hello World") == "Hello World"
