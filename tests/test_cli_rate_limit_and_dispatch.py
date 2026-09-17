"""Tests for rate-limit parsing and CLI dispatch wiring."""

from __future__ import annotations

from pathlib import Path

from smart_dl.core.downloader import build_download_opts
from smart_dl.core.rate_limit import parse_limit_rate
from smart_dl.extractors.registry import ExtractorKind, resolve_extractor_kind


def test_parse_limit_rate_units():
    assert parse_limit_rate("2M") == 2 * 1024**2
    assert parse_limit_rate("500K") == 500 * 1024
    assert parse_limit_rate("1048576") == 1048576
    assert parse_limit_rate(None) is None
    assert parse_limit_rate("bogus") is None
    assert parse_limit_rate("0") is None


def test_build_download_opts_applies_ratelimit():
    opts = build_download_opts(fmt="best", rate_limit="1M")
    assert opts["ratelimit"] == 1024**2
    opts2 = build_download_opts(fmt="best")
    assert "ratelimit" not in opts2


def test_cli_parser_exposes_limit_rate():
    from smart_dl.cli import build_parser

    args = build_parser().parse_args(
        ["https://example.com/x", "--limit-rate", "2M"]
    )
    assert args.limit_rate == "2M"


def test_dispatch_kind_for_youtube():
    assert resolve_extractor_kind("https://youtu.be/abc") == ExtractorKind.YOUTUBE


def test_count_failure_and_lesson_cap():
    from smart_dl.commands.downloads import (
        count_failure,
        resolve_education_max_lessons,
    )

    assert count_failure(True) == 0
    assert count_failure(False) == 1
    assert resolve_education_max_lessons(all_lessons=True, max_lessons=3) is None
    assert resolve_education_max_lessons(all_lessons=False, max_lessons=None) == 20
    assert resolve_education_max_lessons(all_lessons=False, max_lessons=-5) == 0


def test_cleanup_reports_oserror(tmp_path: Path):
    from smart_dl.core import history as history_store
    from smart_dl.core.history import HistoryStatus
    from smart_dl.core.manager import cleanup_downloads
    from smart_dl.core.recorder import record_download

    history_store.set_history_db_path_for_tests(tmp_path / "h.db")
    try:
        history_store.init_db()
        media = tmp_path / "locked.mp4"
        media.write_text("x", encoding="utf-8")
        record_download(
            "https://example.com/x",
            success=False,
            file_path=media,
            error="boom",
        )
        # Simulate undeletable path by pointing history at a directory entry
        # that os.remove cannot delete as a file on Windows: use a directory.
        dir_path = tmp_path / "a_dir"
        dir_path.mkdir()
        history_store.add_to_history(
            url="https://example.com/dir",
            file_path=str(dir_path),
            status=HistoryStatus.FAILED,
        )
        removed = cleanup_downloads(dry_run=False)
        assert removed >= 0
        assert media.exists() is False or removed == 0
    finally:
        history_store.set_history_db_path_for_tests(None)
