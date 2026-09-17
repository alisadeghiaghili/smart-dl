"""Clipboard link grabber (roadmap R4)."""

from __future__ import annotations

import time
from typing import Callable, Iterable, List, Optional, Set

from smart_dl.utils import is_http_url

__all__ = [
    "ClipboardSource",
    "is_grabbable_url",
    "normalize_clipboard_candidate",
    "watch_clipboard",
]


class ClipboardSource:
    """Callable clipboard reader with injectable backend."""

    def __init__(self, reader: Optional[Callable[[], str]] = None) -> None:
        self._reader = reader

    def __call__(self) -> str:
        if self._reader is not None:
            return self._reader() or ""
        try:
            import pyperclip  # type: ignore

            return pyperclip.paste() or ""
        except Exception:
            try:
                import tkinter as tk

                root = tk.Tk()
                root.withdraw()
                try:
                    return root.clipboard_get() or ""
                finally:
                    root.destroy()
            except Exception:
                return ""


def normalize_clipboard_candidate(text: str) -> str:
    """Trim and strip common wrapping characters around a URL.

    Parameters
    ----------
    text : str
        Raw clipboard text.

    Returns
    -------
    str
        Cleaned candidate (may be empty).
    """
    cleaned = (text or "").strip().strip("\"'`<>")
    return cleaned.strip()


def is_grabbable_url(text: str, *, extra_hosts: Optional[Iterable[str]] = None) -> bool:
    """Return True when clipboard text looks like a media/download URL.

    Parameters
    ----------
    text : str
        Clipboard content.
    extra_hosts : Iterable[str], optional
        Hosts to always accept in addition to generic http(s).

    Returns
    -------
    bool
    """
    candidate = normalize_clipboard_candidate(text)
    if not candidate or len(candidate) > 2048:
        return False
    if candidate.lower().startswith("magnet:?"):
        return True
    if not is_http_url(candidate):
        return False
    if any(ch.isspace() for ch in candidate):
        return False
    hosts = {h.lower() for h in (extra_hosts or [])}
    if hosts:
        lowered = candidate.lower()
        return any(host in lowered for host in hosts)
    # Generic http(s) without whitespace is grabbable (queue handles routing).
    return True


def watch_clipboard(
    *,
    interval: float = 2.0,
    max_items: Optional[int] = None,
    source: Optional[ClipboardSource] = None,
    on_url: Optional[Callable[[str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
    sleep: Callable[[float], None] = time.sleep,
    seen: Optional[Set[str]] = None,
    extra_hosts: Optional[Iterable[str]] = None,
) -> List[str]:
    """Poll the clipboard and collect new grabbable URLs.

    Parameters
    ----------
    interval : float, optional
        Seconds between polls.
    max_items : int, optional
        Stop after this many new URLs (``None`` = until should_stop).
    source : ClipboardSource, optional
        Clipboard reader (injectable for tests).
    on_url : Callable[[str], None], optional
        Callback for each new URL.
    should_stop : Callable[[], bool], optional
        Stop predicate.
    sleep : Callable[[float], None], optional
        Sleep function (injectable for tests).
    seen : set of str, optional
        Dedup set (mutated in place).
    extra_hosts : Iterable[str], optional
        Prefer only these hosts when provided.

    Returns
    -------
    list of str
        New URLs discovered in order.

    Examples
    --------
    >>> watch_clipboard(interval=0, max_items=1, source=ClipboardSource(lambda: "https://youtu.be/a"), sleep=lambda s: None)
    ['https://youtu.be/a']
    """
    reader = source or ClipboardSource()
    known: Set[str] = seen if seen is not None else set()
    found: List[str] = []
    last = ""
    while True:
        if should_stop is not None and should_stop():
            break
        if max_items is not None and len(found) >= max_items:
            break
        raw = reader()
        if raw and raw != last:
            last = raw
            candidate = normalize_clipboard_candidate(raw)
            if candidate and candidate not in known and is_grabbable_url(candidate, extra_hosts=extra_hosts):
                known.add(candidate)
                found.append(candidate)
                if on_url is not None:
                    on_url(candidate)
        if max_items is not None and len(found) >= max_items:
            break
        if interval and interval > 0:
            sleep(interval)
        elif max_items is None:
            # interval=0 without max_items would spin forever in tests only
            break
    return found
