"""Wave 3 tests: R5 scheduler + R6 subs-check CLI."""

from __future__ import annotations

import time
from pathlib import Path

from smart_dl.cli import build_parser
from smart_dl.core import queue as queue_store
from smart_dl.core.scheduler import (
    add_scheduled_url,
    clear_schedule,
    get_schedule,
    parse_run_at,
    process_due,
    remove_scheduled,
    set_schedule_db_path_for_tests,
)


def test_parse_run_at_relative_and_clock():
    now = 1_700_000_000.0
    assert parse_run_at("+2h", now=now) == now + 2 * 3600
    assert parse_run_at("+30m", now=now) == now + 1800
    assert parse_run_at(str(int(now)), now=now) == now
    # HH:MM in the future or tomorrow
    ts = parse_run_at("23:59", now=now)
    assert ts > now


def test_parse_run_at_invalid():
    try:
        parse_run_at("not-a-time")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_scheduler_add_list_remove_clear(tmp_path: Path):
    set_schedule_db_path_for_tests(tmp_path / "sched.db")
    try:
        now = time.time()
        id1 = add_scheduled_url("https://example.com/a", "+1h", now=now)
        id2 = add_scheduled_url("https://example.com/b", now + 5, now=now)
        assert id1 > 0 and id2 > 0
        rows = get_schedule("pending")
        assert len(rows) == 2
        assert rows[0]["run_at"] <= rows[1]["run_at"]
        assert remove_scheduled(id1) is True
        assert len(get_schedule("pending")) == 1
        assert clear_schedule() >= 1
        assert get_schedule("pending") == []
    finally:
        set_schedule_db_path_for_tests(None)


def test_process_due_enqueues_only_past_jobs(tmp_path: Path):
    set_schedule_db_path_for_tests(tmp_path / "sched.db")
    queue_store.set_queue_db_path_for_tests(tmp_path / "queue.db")
    try:
        queue_store.init_db()
        now = time.time()
        add_scheduled_url("https://example.com/past", now - 10)
        add_scheduled_url("https://example.com/future", now + 3600)
        captured = []

        def fake_enqueue(urls):
            captured.extend(urls)
            return len(urls)

        result = process_due(now=now, enqueue=fake_enqueue)
        assert result["due"] == 1
        assert result["enqueued"] == 1
        assert captured == ["https://example.com/past"]
        pending = get_schedule("pending")
        assert len(pending) == 1
        assert "future" in pending[0]["url"]
        enqueued = get_schedule("enqueued")
        assert len(enqueued) == 1
        # second run: nothing new due
        result2 = process_due(now=now, enqueue=fake_enqueue)
        assert result2["due"] == 0
    finally:
        set_schedule_db_path_for_tests(None)
        queue_store.set_queue_db_path_for_tests(None)


def test_process_due_default_enqueue_into_queue_db(tmp_path: Path):
    set_schedule_db_path_for_tests(tmp_path / "sched.db")
    queue_store.set_queue_db_path_for_tests(tmp_path / "queue.db")
    try:
        queue_store.init_db()
        now = time.time()
        add_scheduled_url("https://example.com/q1", now - 1)
        result = process_due(now=now)
        assert result["due"] == 1
        assert result["enqueued"] == 1
        q = queue_store.get_queue()
        assert any(item["url"] == "https://example.com/q1" for item in q)
    finally:
        set_schedule_db_path_for_tests(None)
        queue_store.set_queue_db_path_for_tests(None)


def test_cli_schedule_and_subs_flags():
    args = build_parser().parse_args(
        ["--schedule", "add", "https://x", "--at", "02:30"]
    )
    assert args.schedule[0] == "add"
    assert args.at == "02:30"
    args = build_parser().parse_args(["--subs-check"])
    assert args.subs_check is True


def test_handle_schedule_add_list_clear(tmp_path: Path, capsys=None):
    set_schedule_db_path_for_tests(tmp_path / "sched.db")
    try:
        from smart_dl.commands.schedule_cmds import handle_schedule

        handle_schedule(["add", "https://youtube.com/watch?v=z", "--at", "+3h"])
        rows = get_schedule("pending")
        assert len(rows) == 1
        handle_schedule(["list"])
        handle_schedule(["clear"])
        assert get_schedule("pending") == []
    finally:
        set_schedule_db_path_for_tests(None)
