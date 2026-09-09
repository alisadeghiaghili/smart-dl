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

import os
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
    chunk_size: int = 64 * 1024,
) -> Optional[Path]:
    """Stream one URL to disk using shutil.copyfileobj.

    Writes to a ``.part`` temp file and atomically renames it on success, so a
    truncated/failed transfer never leaves a corrupt file at the real path.
    When the server advertises a Content-Length, a short body is treated as
    failure. Each worker builds and closes its own ``requests.Session`` — a
    single Session shared across threads is not thread-safe.

    Returns the dest path on success, None if cancelled or on error.
    """
    if cancel.is_set():
        return None
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    tmp = dest.with_name(dest.name + ".part")
    try:
        with session.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            expected = resp.headers.get("Content-Length")
            expected = int(expected) if (expected or "").isdigit() else None
            with open(tmp, "wb") as f:
                # Fast path: bypass Python per-chunk overhead.
                shutil.copyfileobj(resp.raw, f, length=chunk_size)
            if expected is not None and tmp.stat().st_size != expected:
                raise IOError(
                    "Download truncated: got %d bytes, expected %d"
                    % (tmp.stat().st_size, expected)
                )
        if dest.exists():
            dest.unlink()
        os.replace(tmp, dest)
        return dest
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        return None
    finally:
        session.close()


def parallel_downloads(
    items: list[tuple[str, Path]],
    proxy: Optional[str] = None,
    max_workers: int = 4,
    cancel: Optional[Event] = None,
    chunk_size: int = 64 * 1024,
) -> list[Optional[Path]]:
    """Download a list of (url, dest_path) pairs in parallel.

    Each worker owns its own ``requests.Session`` (thread-safe) and writes via
    an atomic temp-file rename. Stops early if `cancel` is set.

    Returns a list of completed paths (or None for failures/cancellations),
    in the same order as `items`.
    """
    if not items:
        return []

    cancel = cancel or Event()
    if max_workers < 1:
        max_workers = 1

    results: list[Optional[Path]] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_to_idx = {
            ex.submit(_copy_one, url, dest, proxy, cancel, chunk_size): i
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
