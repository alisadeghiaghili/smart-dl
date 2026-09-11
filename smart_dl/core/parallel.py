"""Parallel direct-to-disk downloads.

Uses ``shutil.copyfileobj`` for lower per-chunk Python overhead, one
``requests.Session`` per worker (a shared Session is not thread-safe),
and atomic temp-file + rename so a cancelled download never leaves a
partial file at the destination path.
"""

from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Event
from typing import List, Optional, Tuple

import requests

__all__ = ["DownloadResult", "parallel_downloads"]


class DownloadResult(dict):
    """Outcome of one parallel download item.

    Keys
    ----
    url : str
    dest : str
    ok : bool
    path : str or None
        Final path on success.
    error : str
        Failure reason (empty on success).
    """

    @property
    def ok(self) -> bool:
        return bool(self.get("ok"))

    @property
    def path(self) -> Optional[Path]:
        raw = self.get("path")
        return Path(raw) if raw else None


def _copy_one(
    url: str,
    dest: Path,
    cancel: Optional[Event] = None,
    session: Optional[requests.Session] = None,
    chunk_size: int = 64 * 1024,
    proxy: Optional[str] = None,
) -> DownloadResult:
    """Stream one URL to disk atomically.

    Parameters
    ----------
    url : str
        Source URL.
    dest : pathlib.Path
        Final destination path.
    cancel : threading.Event, optional
        Cooperative cancel flag.
    session : requests.Session, optional
        Worker-owned session. Built dynamically if omitted.
    chunk_size : int, optional
        Copy buffer size.
    proxy : str, optional
        Proxy URL if session is created dynamically.

    Returns
    -------
    DownloadResult
        Success or failure metadata; never raises for I/O/network errors.
    """
    result = DownloadResult(url=url, dest=str(dest), ok=False, path=None, error="")
    if cancel and cancel.is_set():
        result["error"] = "cancelled"
        return result

    if session is None:
        session = requests.Session()
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    try:
        with session.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            resp.raw.decode_content = True
            with tmp.open("wb") as handle:
                shutil.copyfileobj(resp.raw, handle, length=chunk_size)
        if cancel and cancel.is_set():
            tmp.unlink(missing_ok=True)
            result["error"] = "cancelled"
            return result
        tmp.replace(dest)
        result["ok"] = True
        result["path"] = str(dest)
        return result
    except Exception as exc:  # noqa: BLE001 — isolate worker failures
        tmp.unlink(missing_ok=True)
        result["error"] = str(exc)[:200]
        return result


def parallel_downloads(
    items: List[Tuple[str, Path]],
    proxy: Optional[str] = None,
    max_workers: int = 4,
    cancel: Optional[Event] = None,
    chunk_size: int = 64 * 1024,
) -> List[Optional[Path]]:
    """Download ``(url, dest)`` pairs in parallel.

    Parameters
    ----------
    items : list of (str, pathlib.Path)
        Download jobs.
    proxy : str, optional
        Optional proxy URL applied to each worker session.
    max_workers : int, optional
        Thread pool size (minimum 1).
    cancel : threading.Event, optional
        Set to stop remaining work cooperatively.
    chunk_size : int, optional
        Read/write buffer size.

    Returns
    -------
    list of pathlib.Path or None
        Destination path on success, ``None`` on failure/cancel, in the
        same order as *items*.
    """
    if not items:
        return []

    cancel = cancel or Event()
    workers = max(1, int(max_workers))
    results: List[Optional[Path]] = [None] * len(items)

    def _worker(url: str, dest: Path) -> DownloadResult:
        session = requests.Session()
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
        try:
            return _copy_one(url, dest, cancel, session, chunk_size)
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {}
        for index, (url, dest) in enumerate(items):
            if cancel.is_set():
                break
            future = pool.submit(_worker, url, dest)
            future_map[future] = index

        for future in as_completed(list(future_map.keys())):
            index = future_map[future]
            try:
                outcome = future.result()
            except Exception:  # noqa: BLE001
                continue
            if outcome.ok and outcome.path is not None:
                results[index] = outcome.path
            else:
                results[index] = None

    return results


def parallel_download_results(
    items: List[Tuple[str, Path]],
    proxy: Optional[str] = None,
    max_workers: int = 4,
    cancel: Optional[Event] = None,
    chunk_size: int = 64 * 1024,
) -> List[DownloadResult]:
    """Like :func:`parallel_downloads` but returns detailed results.

    Parameters
    ----------
    items : list of (str, pathlib.Path)
        Download jobs.
    proxy : str, optional
        Optional proxy URL.
    max_workers : int, optional
        Thread pool size.
    cancel : threading.Event, optional
        Cooperative cancel flag.
    chunk_size : int, optional
        Buffer size.

    Returns
    -------
    list of DownloadResult
        One result per input item, same order.
    """
    if not items:
        return []
    cancel = cancel or Event()
    workers = max(1, int(max_workers))
    results: List[DownloadResult] = [
        DownloadResult(url=u, dest=str(d), ok=False, path=None, error="not started")
        for u, d in items
    ]

    def _session() -> requests.Session:
        session = requests.Session()
        if proxy:
            session.proxies = {"http": proxy, "https": proxy}
        return session

    sessions = [_session() for _ in range(workers)]
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_map = {}
            for index, (url, dest) in enumerate(items):
                if cancel.is_set():
                    results[index]["error"] = "cancelled"
                    continue
                session = sessions[index % workers]
                future = pool.submit(_copy_one, url, dest, cancel, session, chunk_size)
                future_map[future] = index
            for future in as_completed(list(future_map.keys())):
                index = future_map[future]
                try:
                    results[index] = future.result()
                except Exception as exc:  # noqa: BLE001
                    results[index]["error"] = str(exc)[:200]
    finally:
        for session in sessions:
            session.close()
    return results
