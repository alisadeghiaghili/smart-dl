"""Cleanup safety tests against the production history status vocabulary."""

from __future__ import annotations

from pathlib import Path

from smart_dl.core import history as history_store
from smart_dl.core.history import HistoryStatus
from smart_dl.core.manager import cleanup_downloads
from smart_dl.core.recorder import record_download


def _use_history_db(tmp_path: Path) -> Path:
    """Point history at an isolated SQLite file under *tmp_path*.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest temporary directory.

    Returns
    -------
    pathlib.Path
        The history database path under test.
    """
    db_path = tmp_path / "history.sqlite3"
    history_store.set_history_db_path_for_tests(db_path)
    history_store.init_db()
    return db_path


def _reset_history_db_path() -> None:
    history_store.set_history_db_path_for_tests(None)


def test_history_status_vocabulary_is_canonical() -> None:
    """Production writers and queries must share completed/failed only."""
    assert HistoryStatus.COMPLETED == "completed"
    assert HistoryStatus.FAILED == "failed"
    assert HistoryStatus.values() == frozenset({"completed", "failed"})


def test_cleanup_skips_file_re_downloaded_successfully(tmp_path: Path) -> None:
    """Failed then completed rows on the same path must not delete the file.

    Uses the real history store so a wrong status synonym cannot silently pass.
    """
    media = tmp_path / "video.mp4"
    media.write_text("payload", encoding="utf-8")

    _use_history_db(tmp_path)
    try:
        record_download(
            "https://example.com/v1",
            success=False,
            title="first attempt",
            file_path=media,
            error="network reset",
        )
        record_download(
            "https://example.com/v1",
            success=True,
            title="retry ok",
            file_path=media,
        )

        completed = history_store.get_history(status=HistoryStatus.COMPLETED)
        failed = history_store.get_history(status=HistoryStatus.FAILED)
        assert len(completed) == 1
        assert len(failed) == 1
        assert completed[0]["status"] == HistoryStatus.COMPLETED
        assert failed[0]["status"] == HistoryStatus.FAILED

        removed = cleanup_downloads(dry_run=False)
        assert removed == 0
        assert media.exists()
    finally:
        _reset_history_db_path()


def test_cleanup_removes_pure_failed_file(tmp_path: Path) -> None:
    """Files only referenced by failed history rows are deleted."""
    media = tmp_path / "failed_video.mp4"
    media.write_text("partial", encoding="utf-8")

    _use_history_db(tmp_path)
    try:
        record_download(
            "https://example.com/v2",
            success=False,
            title="broken",
            file_path=media,
            error="timeout",
        )

        dry = cleanup_downloads(dry_run=True)
        assert dry == 0
        assert media.exists()

        removed = cleanup_downloads(dry_run=False)
        assert removed == 1
        assert not media.exists()
    finally:
        _reset_history_db_path()


def test_cleanup_does_not_treat_success_synonym_as_completed(tmp_path: Path) -> None:
    """Regression: cleanup must query ``completed``, not a ``success`` synonym.

    If someone reintroduces ``status="success"`` in cleanup, completed rows are
    invisible and a re-downloaded file gets deleted. This test writes a
    completed row with production vocabulary and asserts cleanup stays safe.
    """
    media = tmp_path / "redownloaded.mp4"
    media.write_text("ok", encoding="utf-8")

    _use_history_db(tmp_path)
    try:
        history_store.add_to_history(
            url="https://example.com/v3",
            title="legacy failed marker",
            file_path=str(media),
            status=HistoryStatus.FAILED,
        )
        history_store.add_to_history(
            url="https://example.com/v3",
            title="success synonym must not be required",
            file_path=str(media),
            status=HistoryStatus.COMPLETED,
        )

        completed_paths = {
            r["file_path"]
            for r in history_store.get_history(status=HistoryStatus.COMPLETED)
            if r.get("file_path")
        }
        assert str(media) in completed_paths
        assert cleanup_downloads() == 0
        assert media.exists()
    finally:
        _reset_history_db_path()
