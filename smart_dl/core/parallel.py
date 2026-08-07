"""Parallel direct-to-disk downloads using shutil.copyfileobj.

The standard chunked-loop pattern (`for chunk in iter_content(8192): f.write(chunk)`)
crosses the Python/C boundary every 8 KB. `shutil.copyfileobj(resp.raw, f, length=64*1024)`
does the same work in a tight loop with one boundary crossing per 64 KB — measurably
faster for large files, and significantly so under concurrency.

Usage:
    items = [(url1, dest1), (url2, dest2), ...]
    parallel_downloads(items, proxy="socks5://127.0.0.1:10808", max_workers=4)
"""
from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Optional

import requests


def _copy_one(
    url: str,
    dest: Path,
    proxy: Optional[str],
    cancel: Event,
    session: requests.Session,
    chunk_size: int = 64 * 1024,
) -> Optional[Path]:
    """Stream one URL to disk using shutil.copyfileobj.

    Returns the dest path on success, None if cancelled or on error.
    """
    if cancel.is_set():
        return None
    try:
        with session.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                # Fast path: bypass Python per-chunk overhead.
                shutil.copyfileobj(resp.raw, f, length=chunk_size)
        return dest
    except Exception:
        return None


def parallel_downloads(
    items: list[tuple[str, Path]],
    proxy: Optional[str] = None,
    max_workers: int = 4,
    cancel: Optional[Event] = None,
    chunk_size: int = 64 * 1024,
) -> list[Optional[Path]]:
    """Download a list of (url, dest_path) pairs in parallel.

    Each worker uses the same shared `requests.Session` so connection pools
    are reused. Stops early if `cancel` is set.

    Returns a list of completed paths (or None for failures/cancellations),
    in the same order as `items`.
    """
    if not items:
        return []

    cancel = cancel or Event()
    if max_workers < 1:
        max_workers = 1

    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    results: list[Optional[Path]] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_idx = {
            ex.submit(_copy_one, url, dest, proxy, cancel, session, chunk_size): i
            for i, (url, dest) in enumerate(items)
        }
        for fut in future_to_idx:
            if cancel.is_set():
                break
            i = future_to_idx[fut]
            try:
                results[i] = fut.result()
            except Exception:
                results[i] = None
    return results
