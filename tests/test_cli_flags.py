"""Tests for CLI argument handling, quality mapping, and extractor routing correctness."""

from unittest.mock import patch

from smart_dl.utils import quality_to_format


def test_quality_to_format_presets():
    """Test mapping of standard and high-res quality presets."""
    assert quality_to_format("best") == "bestvideo+bestaudio/best"
    assert quality_to_format("worst") == "worstvideo+worstaudio/worst"
    assert quality_to_format("4k") == "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
    assert quality_to_format("8k") == "bestvideo[height<=4320]+bestaudio/best[height<=4320]"
    assert quality_to_format("1080") == "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    assert quality_to_format("720") == "bestvideo[height<=720]+bestaudio/best[height<=720]"


def test_queue_download_item_routes_education_url():
    """Test that queue_download_item routes Maktabkhooneh URLs to education extractor."""
    url = "https://maktabkhooneh.org/course/learn-python"

    with patch("smart_dl.utils.is_education_url", return_value=True), \
         patch("smart_dl.extractors.education.download_education_course", return_value=True) as mock_edu:

        from smart_dl.cli import queue_download_item

        res = queue_download_item(url, "/tmp/out")
        assert res is True
        mock_edu.assert_called_once()


def test_queue_download_item_routes_podcast_url():
    """Test that queue_download_item routes podcast RSS URLs to podcast extractor."""
    url = "https://castbox.fm/channel/id12345"

    with patch("smart_dl.utils.is_education_url", return_value=False), \
         patch("smart_dl.utils.is_podcast_url", return_value=True), \
         patch("smart_dl.extractors.podcast.download_podcast_url", return_value=True) as mock_pod:

        from smart_dl.cli import queue_download_item

        res = queue_download_item(url, "/tmp/out")
        assert res is True
        mock_pod.assert_called_once()
