"""CLI subscription command handlers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, List

__all__ = [
    "handle_check_updates",
    "handle_my_subs",
    "handle_subscribe",
    "handle_unsubscribe",
]


def handle_subscribe(url: str) -> None:
    """Subscribe to a channel/playlist URL.

    Parameters
    ----------
    url : str
        Channel or playlist URL.

    Returns
    -------
    None
    """
    from smart_dl.core.subscriptions import add_subscription, init_db
    from smart_dl.ui import success

    init_db()
    sub_id = add_subscription(url)
    success(f"Subscribed! 🎉 (ID: {sub_id})")


def handle_unsubscribe(sub_id: int) -> None:
    """Remove a subscription by id.

    Parameters
    ----------
    sub_id : int
        Subscription primary key.

    Returns
    -------
    None
    """
    from smart_dl.core.subscriptions import init_db, remove_subscription
    from smart_dl.ui import success

    init_db()
    remove_subscription(sub_id)
    success(f"Unsubscribed from ID {sub_id}.")


def _auto_download_ids(subs: Iterable[dict]) -> set:
    return {
        int(sub["id"])
        for sub in subs
        if int(sub.get("auto_download") or 0) == 1
    }


def handle_check_updates() -> None:
    """Check subscriptions for new uploads and optionally download them.

    Auto-download runs when ``SMARTDL_SUBS_AUTODL=1`` is set **or** the
    subscription row has ``auto_download`` enabled.

    Returns
    -------
    None
    """
    from smart_dl.core import sub_updates
    from smart_dl.core.subscriptions import get_subscriptions, init_db
    from smart_dl.lang import t
    from smart_dl.ui import error, info, success
    from smart_dl.ui.progress import stop_event

    init_db()
    if not get_subscriptions():
        info(t("cli_no_subs"))
        return

    result = sub_updates.check_all_subscriptions()
    info(f"Checked {result['checked']} subscription(s).")
    if result["total_new"] == 0:
        success(t("cli_no_new_uploads"))
        return

    success(f"Found {result['total_new']} new upload(s):")
    for upload in result["new_uploads"]:
        info(f"  {upload.video_id}  {upload.title[:60]}  {upload.url[:70]}")

    auto_env = os.environ.get("SMARTDL_SUBS_AUTODL") == "1"
    sub_auto_ids = _auto_download_ids(get_subscriptions())
    pending: List[Any] = [
        up
        for up in result["new_uploads"]
        if auto_env or int(up.get("sub_id") or 0) in sub_auto_ids
    ]
    if not pending:
        return

    from smart_dl.core.paths import get_default_download_dir
    from smart_dl.core.sub_updates import record_subscription_download
    from smart_dl.extractors.youtube import download_yt

    out = get_default_download_dir()
    out.mkdir(parents=True, exist_ok=True)
    for upload in pending:
        if stop_event.is_set():
            break
        info(f"Downloading {upload.title[:50]}...")
        ok = download_yt(upload.url, Path(out), "bestvideo+bestaudio/best", False)
        if ok:
            record_subscription_download(
                int(upload["sub_id"]),
                upload.url,
                title=upload.title,
                video_id=upload.video_id,
            )
        else:
            error(f"Failed: {upload.title[:50]}")


def handle_my_subs() -> None:
    """Print subscription table and aggregate stats.

    Returns
    -------
    None
    """
    from rich import box
    from rich.table import Table

    from smart_dl.core.subscriptions import get_subscription_stats, get_subscriptions, init_db
    from smart_dl.ui import console, info

    init_db()
    subs = get_subscriptions()
    stats = get_subscription_stats()
    if not subs:
        info("No subscriptions found.")
        return

    table = Table(box=box.ROUNDED, show_header=True, border_style="cyan")
    table.add_column("#", width=5)
    table.add_column("Name", max_width=30)
    table.add_column("URL", max_width=50)
    table.add_column("Platform", width=10)
    table.add_column("Auto-DL", width=8)
    for sub in subs:
        table.add_row(
            str(sub["id"]),
            sub["name"] or "?",
            sub["url"][:50],
            sub["platform"],
            "yes" if sub["auto_download"] else "no",
        )
    console.print(table)
    console.print(
        f"\n[bold]{stats['active']}[/bold] active subscriptions, "
        f"[bold]{stats['videos_downloaded']}[/bold] videos downloaded 📥"
    )
