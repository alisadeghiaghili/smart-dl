"""Retry logic with exponential backoff and error classification."""
import time

from smart_dl.ui import info, warn
from smart_dl.ui.progress import stop_event

# Network error keywords for classification
RESET_KEYWORDS = [
    "10054", "connection aborted", "connection reset",
    "connection broken", "forcibly closed", "connectionreseterror",
    "remotedisconnected",
]

DNS_KEYWORDS = [
    "getaddrinfo", "failed to resolve", "errno 11001",
    "name or service not known", "nodename nor servname",
    "name resolution failed",
]

FATAL_ERRORS = [
    "ffmpeg is not installed", "ffmpeg not found", "abort-on-error",
    "aborting due to", "requested merging of multiple formats",
    "video unavailable", "private video",
    "age-restricted", "copyright", "format not available",
]

SUPPRESS_WARNINGS = [
    "no supported javascript runtime", "js runtime", "--js-runtimes",
    "youtube extraction without a js", "writing dash", "only some players",
    "falling back on generic information extractor",
    "the extractor is attempting impersonation",
    "if you encounter errors",
    "impersonate target is available",
    "failed to parse xml",
    "not well-formed",
]

ERROR_HINTS = [
    ("ffmpeg is not installed",              "Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("requested merging of multiple formats","Fix: winget install Gyan.FFmpeg  (then reopen terminal)"),
    ("private video",                        "This video is private \u2014 cannot be downloaded."),
    ("sign in to confirm",                   "Age-restricted \u2014 YouTube requires sign-in."),
    ("age-restricted",                       "Age-restricted \u2014 cannot download without authentication."),
    ("video unavailable",                    "Video unavailable (deleted, region-blocked, or private)."),
    ("blocked in your country",              "Geo-blocked. Try a VPN."),
    ("not available in your country",        "Geo-blocked. Try a VPN."),
    ("copyright",                            "Blocked due to a copyright claim."),
    ("requested format is not available",    "Selected quality not available. Try a different format."),
    ("format not available",                 "Selected quality not available. Try a different format."),
    ("unable to extract",                    "Could not extract video info. URL may be invalid."),
    ("unsupported url",                      "Unsupported URL."),
    ("connection",                           "Network error \u2014 check connection or proxy (press P)."),
    ("timeout",                              "Connection timed out \u2014 check network or try again."),
    ("no such file",                         "Output path inaccessible. Check folder permissions."),
]


def diagnose_error(e: Exception) -> str:
    """Return a user-friendly hint for a given exception."""
    msg = str(e).lower()
    for keyword, hint in ERROR_HINTS:
        if keyword in msg:
            return hint
    return ""


def is_network_error(msg: str) -> bool:
    """Check if an error message indicates a network issue."""
    return any(x in msg for x in [
        "connection","timeout","network","reset","refused","broken pipe",
        "ssl","certificate","name or service","temporary failure",
        "unreachable","no route","http error 5","503","502","429","rate limit",
    ])


def retry_with_backoff(func, max_retries=999, base_delay=5, max_delay=300, max_duration=1800):
    """Retry func() with exponential backoff. Caps at max_duration seconds."""
    attempt, delay = 0, base_delay
    start_time = time.monotonic()
    while not stop_event.is_set():
        try:
            return func()
        except Exception as e:
            msg = str(e).lower()
            if any(f in msg for f in FATAL_ERRORS):
                raise
            if any(x in msg for x in DNS_KEYWORDS):
                from smart_dl.core.network import show_no_internet_panel
                show_no_internet_panel()
                return None
            attempt += 1
            elapsed = time.monotonic() - start_time
            net = is_network_error(msg)
            if attempt >= max_retries and not net:
                raise
            if elapsed >= max_duration:
                warn("Retried for " + str(int(elapsed)) + "s \u2014 giving up. Try again later or check your connection.")
                return None
            if stop_event.is_set():
                break
            delay = min(delay * 1.5, max_delay)
            if any(x in msg for x in RESET_KEYWORDS):
                warn("Connection reset by server (attempt " + str(attempt)
                     + ") \u2014 retrying in " + str(int(delay)) + "s...")
                if attempt == 3:
                    info("Server keeps dropping connections \u2014 likely network filtering.")
                    info("Try setting a proxy: press [bold cyan]P[/bold cyan] at the URL prompt.")
            else:
                warn("Error (attempt " + str(attempt) + "): " + str(e)[:80])
                info("Retrying in " + str(int(delay)) + "s...")
            for _ in range(int(delay)):
                if stop_event.is_set(): return None
                time.sleep(1)
    return None
