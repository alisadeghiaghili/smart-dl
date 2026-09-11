"""Retry with exponential backoff and error classification.

Terminal outcomes raise :class:`RetryGaveUp` so callers never treat a
silent give-up as success.
"""

from __future__ import annotations

import time
from typing import Callable, Optional, TypeVar

from smart_dl.ui import info, warn
from smart_dl.ui.progress import stop_event

__all__ = [
    "DNS_KEYWORDS",
    "ERROR_HINTS",
    "FATAL_ERRORS",
    "RESET_KEYWORDS",
    "RetryGaveUp",
    "SUPPRESS_WARNINGS",
    "diagnose_error",
    "is_network_error",
    "retry_with_backoff",
]

T = TypeVar("T")

RESET_KEYWORDS = [
    "10054",
    "connection aborted",
    "connection reset",
    "connection broken",
    "forcibly closed",
    "connectionreseterror",
    "remotedisconnected",
]

DNS_KEYWORDS = [
    "getaddrinfo",
    "failed to resolve",
    "errno 11001",
    "name or service not known",
    "nodename nor servname",
    "name resolution failed",
]

FATAL_ERRORS = [
    "ffmpeg is not installed",
    "ffmpeg not found",
    "abort-on-error",
    "aborting due to",
    "requested merging of multiple formats",
    "video unavailable",
    "private video",
    "age-restricted",
    "copyright",
    "format not available",
]

SUPPRESS_WARNINGS = [
    "no supported javascript runtime",
    "js runtime",
    "--js-runtimes",
    "youtube extraction without a js",
    "writing dash",
    "only some players",
    "falling back on generic information extractor",
    "the extractor is attempting impersonation",
    "if you encounter errors",
    "impersonate target is available",
    "failed to parse xml",
    "not well-formed",
]

ERROR_HINTS = [
    ("ffmpeg is not installed", "Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("requested merging of multiple formats", "Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("private video", "This video is private — cannot be downloaded."),
    ("sign in to confirm", "Age-restricted — YouTube requires sign-in."),
    ("age-restricted", "Age-restricted — cannot download without authentication."),
    ("video unavailable", "Video unavailable (deleted, region-blocked, or private)."),
    ("blocked in your country", "Geo-blocked. Try a VPN."),
    ("not available in your country", "Geo-blocked. Try a VPN."),
    ("copyright", "Blocked due to a copyright claim."),
    ("requested format is not available", "Selected quality not available. Try a different format."),
    ("format not available", "Selected quality not available. Try a different format."),
    ("unable to extract", "Could not extract video info. URL may be invalid."),
    ("unsupported url", "Unsupported URL."),
    ("connection", "Network error — check connection or proxy (press P)."),
    ("timeout", "Connection timed out — check network or try again."),
    ("no such file", "Output path inaccessible. Check folder permissions."),
]


class RetryGaveUp(Exception):
    """Raised when retry policy ends without a successful call.

    Attributes
    ----------
    last_error : Exception or None
        The most recent underlying exception, if any.
    attempts : int
        Number of failed attempts performed.
    elapsed : float
        Wall-clock seconds spent retrying.
    reason : str
        Short machine-readable reason: ``"dns"``, ``"duration"``,
        ``"max_retries"``, or ``"stopped"``.
    """

    def __init__(
        self,
        message: str,
        *,
        last_error: Optional[BaseException] = None,
        attempts: int = 0,
        elapsed: float = 0.0,
        reason: str = "max_retries",
    ) -> None:
        super().__init__(message)
        self.last_error = last_error
        self.attempts = attempts
        self.elapsed = elapsed
        self.reason = reason


def diagnose_error(exc: BaseException) -> str:
    """Return a user-facing hint for *exc*, or an empty string.

    Parameters
    ----------
    exc : BaseException
        Exception raised by yt-dlp or the download stack.

    Returns
    -------
    str
        Hint text, or ``""`` when no pattern matches.
    """
    msg = str(exc).lower()
    for keyword, hint in ERROR_HINTS:
        if keyword in msg:
            return hint
    return ""


def is_network_error(msg: str) -> bool:
    """Check whether *msg* indicates a transient network failure.

    Parameters
    ----------
    msg : str
        Lowercased error text.

    Returns
    -------
    bool
        ``True`` if the message looks network-related.
    """
    lowered = msg.lower()
    return any(
        token in lowered
        for token in (
            "connection",
            "timeout",
            "network",
            "reset",
            "refused",
            "broken pipe",
            "ssl",
            "certificate",
            "name or service",
            "temporary failure",
            "unreachable",
            "no route",
            "http error 5",
            "503",
            "502",
            "429",
            "rate limit",
        )
    )


def _is_fatal(msg: str) -> bool:
    return any(token in msg for token in FATAL_ERRORS)


def _is_dns(msg: str) -> bool:
    return any(token in msg for token in DNS_KEYWORDS)


def retry_with_backoff(
    func: Callable[[], T],
    *,
    max_retries: int = 999,
    base_delay: float = 5.0,
    max_delay: float = 300.0,
    max_duration: float = 1800.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call *func*, retrying transient failures with exponential backoff.

    ``max_retries`` of ``0`` or values ``>= 999`` means unlimited attempts
    (still bounded by *max_duration*).

    Parameters
    ----------
    func : Callable[[], T]
        Zero-argument callable to invoke.
    max_retries : int, optional
        Maximum non-network failure attempts before giving up.
        ``0`` or ``>= 999`` means unlimited (default ``999``).
    base_delay : float, optional
        Initial delay in seconds (default ``5``).
    max_delay : float, optional
        Delay cap in seconds (default ``300``).
    max_duration : float, optional
        Total wall-clock budget in seconds (default ``1800``).
    sleep : Callable[[float], None], optional
        Sleep implementation (injectable for tests).

    Returns
    -------
    T
        Whatever *func* returns.

    Raises
    ------
    RetryGaveUp
        On DNS failure, duration cap, max retries, or user stop.
    Exception
        Fatal errors from *func* are re-raised immediately.

    Examples
    --------
    >>> def work():
    ...     return 42
    >>> retry_with_backoff(work, base_delay=0, max_retries=1)
    42
    """
    unlimited = max_retries <= 0 or max_retries >= 999
    attempt = 0
    delay = float(base_delay)
    start = time.monotonic()
    last_error: Optional[BaseException] = None

    while not stop_event.is_set():
        try:
            return func()
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()

            if isinstance(exc, (PermissionError, NotADirectoryError, FileExistsError)) or _is_fatal(msg):
                raise

            if _is_dns(msg):
                raise RetryGaveUp(
                    "DNS resolution failed — host unreachable",
                    last_error=exc,
                    attempts=attempt,
                    elapsed=time.monotonic() - start,
                    reason="dns",
                ) from exc

            attempt += 1
            elapsed = time.monotonic() - start

            net = is_network_error(msg)
            if (not unlimited and attempt >= max_retries) and not net:
                raise

            if elapsed >= max_duration:
                warn(
                    "Retried for "
                    + str(int(elapsed))
                    + "s — giving up. Try again later or check your connection."
                )
                raise RetryGaveUp(
                    "Retry duration cap exceeded",
                    last_error=exc,
                    attempts=attempt,
                    elapsed=elapsed,
                    reason="duration",
                ) from exc

            delay = min(delay * 1.5, max_delay)
            if any(token in msg for token in RESET_KEYWORDS):
                warn(
                    "Connection reset by server (attempt "
                    + str(attempt)
                    + ") — retrying in "
                    + str(int(delay))
                    + "s..."
                )
                if attempt == 3:
                    info("Server keeps dropping connections — likely network filtering.")
                    info("Try setting a proxy: press [bold cyan]P[/bold cyan] at the URL prompt.")
            else:
                warn("Error (attempt " + str(attempt) + "): " + str(exc)[:80])
                info("Retrying in " + str(int(delay)) + "s...")

            remaining = float(delay)
            while remaining > 0:
                if stop_event.is_set():
                    raise RetryGaveUp(
                        "Stopped by user",
                        last_error=exc,
                        attempts=attempt,
                        elapsed=time.monotonic() - start,
                        reason="stopped",
                    ) from exc
                sleep(1.0)
                remaining -= 1.0

    raise RetryGaveUp(
        "Stopped by user",
        last_error=last_error,
        attempts=attempt,
        elapsed=time.monotonic() - start,
        reason="stopped",
    )
