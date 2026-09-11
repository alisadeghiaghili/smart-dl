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
    item = {"id": 1, "url": "https://maktabkhooneh.org/course/learn-python", "format_str": "best", "is_audio": False}

    with patch("smart_dl.extractors.education.is_education_url", return_value=True), \
         patch("smart_dl.extractors.education.download_education_course", return_value=True) as mock_edu:

        from smart_dl.cli import queue_download_item

        res = queue_download_item(item, "/tmp/out")
        assert res is True
        mock_edu.assert_called_once()


def test_queue_download_item_routes_podcast_url():
    """Test that queue_download_item routes podcast RSS URLs to podcast extractor."""
    item = {"id": 2, "url": "https://castbox.fm/channel/id12345", "format_str": "best", "is_audio": False}

    with patch("smart_dl.extractors.education.is_education_url", return_value=False), \
         patch("smart_dl.utils.is_podcast_url", return_value=True), \
         patch("smart_dl.extractors.podcast.download_podcast_url", return_value=True) as mock_pod:

        from smart_dl.cli import queue_download_item

        res = queue_download_item(item, "/tmp/out")
        assert res is True
        mock_pod.assert_called_once()


def test_cli_version_flag(capsys) -> None:
    """Verify that --version outputs the correct version and exits."""
    import pytest

    from smart_dl import VERSION
    from smart_dl.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"SmartDL v{VERSION}" in (captured.out + captured.err)


def test_cli_help_flag(capsys) -> None:
    """Verify that --help outputs usage information and exits 0."""
    import pytest

    from smart_dl.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "SmartDL" in captured.out
    assert "--quality" in captured.out
    assert "--queue" in captured.out


def test_cli_unknown_flag(capsys) -> None:
    """Verify that unknown flag raises SystemExit with non-zero code."""
    import pytest

    from smart_dl.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--completely-unknown-flag"])
    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_cli_diagnose_flag() -> None:
    """Verify that --diagnose flag sets diagnose attribute."""
    from smart_dl.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["--diagnose"])
    assert args.diagnose is True
