"""Unit tests for SmartDL utility functions."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SMARTDL_NO_DEPS'] = '1'

from smart_dl.utils import (
    fmt_dur,
    fmt_size,
    is_aparat_url,
    is_playlist_url,
    is_podcast_url,
    is_youtube_url,
    safe_filename,
)


class TestFmtSize:
    def test_zero(self):
        assert fmt_size(0) == "0 B"

    def test_bytes(self):
        assert fmt_size(500) == "500 B"

    def test_kilobytes(self):
        assert fmt_size(1024) == "1.0 KB"
        assert fmt_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert fmt_size(1048576) == "1.0 MB"

    def test_gigabytes(self):
        assert fmt_size(1073741824) == "1.0 GB"

    def test_terabytes(self):
        assert fmt_size(1099511627776) == "1.0 TB"

    def test_none(self):
        assert fmt_size(None) == "?"

    def test_question_mark(self):
        assert fmt_size("?") == "?"


class TestFmtDur:
    def test_zero(self):
        assert fmt_dur(0) == "?"

    def test_none(self):
        assert fmt_dur(None) == "?"

    def test_seconds_only(self):
        assert fmt_dur(45) == "00:00:45"

    def test_minutes(self):
        assert fmt_dur(125) == "00:02:05"

    def test_hours(self):
        assert fmt_dur(3661) == "01:01:01"

    def test_long_duration(self):
        assert fmt_dur(36000) == "10:00:00"


class TestSafeFilename:
    def test_normal(self):
        assert safe_filename("Hello World") == "Hello World"

    def test_special_chars(self):
        result = safe_filename("Hello! @#$%^&* World")
        assert "!" not in result
        assert "@" not in result

    def test_empty(self):
        assert safe_filename("") == "file"

    def test_maxlen(self):
        result = safe_filename("A" * 100, maxlen=10)
        assert len(result) == 10

    def test_preserves_valid(self):
        assert safe_filename("test_file-123 (copy)") == "test_file-123 (copy)"


class TestIsYoutubeUrl:
    def test_standard(self):
        assert is_youtube_url("https://www.youtube.com/watch?v=abc") is True

    def test_short(self):
        assert is_youtube_url("https://youtu.be/abc") is True

    def test_mobile(self):
        assert is_youtube_url("https://m.youtube.com/watch?v=abc") is True

    def test_not_youtube(self):
        assert is_youtube_url("https://vimeo.com/123") is False

    def test_aparat(self):
        assert is_youtube_url("https://aparat.com/v/abc") is False


class TestIsAparatUrl:
    def test_standard(self):
        assert is_aparat_url("https://aparat.com/v/abc") is True

    def test_www(self):
        assert is_aparat_url("https://www.aparat.com/v/abc") is True

    def test_not_aparat(self):
        assert is_aparat_url("https://youtube.com/watch?v=abc") is False


class TestIsPlaylistUrl:
    def test_youtube_playlist(self):
        assert is_playlist_url("https://www.youtube.com/playlist?list=PLxxx") is True

    def test_aparat_playlist(self):
        assert is_playlist_url("https://aparat.com/playlist/abc") is True

    def test_not_playlist(self):
        assert is_playlist_url("https://youtube.com/watch?v=abc") is False


class TestIsPodcastUrl:
    def test_mp3(self):
        assert is_podcast_url("https://example.com/podcast.mp3") is True

    def test_m4a(self):
        assert is_podcast_url("https://example.com/podcast.m4a") is True

    def test_audio_content_type(self):
        assert is_podcast_url("https://example.com/feed", ct="audio/mpeg") is True

    def test_rss_content_type(self):
        assert is_podcast_url("https://example.com/feed", ct="application/rss+xml") is True

    def test_not_podcast(self):
        assert is_podcast_url("https://youtube.com/watch?v=abc") is False
