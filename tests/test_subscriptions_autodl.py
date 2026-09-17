"""Subscription auto-download selection tests."""

from __future__ import annotations

from smart_dl.core.subscriptions import (
    add_subscription,
    get_subscriptions,
    init_db,
    set_subscriptions_db_path_for_tests,
)


def test_auto_download_flag_roundtrip(tmp_path):
    db = tmp_path / "subs.db"
    set_subscriptions_db_path_for_tests(db)
    try:
        init_db()
        sid = add_subscription(
            "https://youtube.com/@auto",
            name="auto",
            auto_download=True,
        )
        sid2 = add_subscription(
            "https://youtube.com/@manual",
            name="manual",
            auto_download=False,
        )
        assert sid > 0 and sid2 > 0
        rows = {r["id"]: r for r in get_subscriptions()}
        assert int(rows[sid]["auto_download"]) == 1
        assert int(rows[sid2]["auto_download"]) == 0

        auto_ids = {
            int(sub["id"])
            for sub in get_subscriptions()
            if int(sub.get("auto_download") or 0) == 1
        }
        assert sid in auto_ids
        assert sid2 not in auto_ids
    finally:
        set_subscriptions_db_path_for_tests(None)
