"""Telegram completion notifications (roadmap R7)."""

from __future__ import annotations

from typing import Any, Callable, Optional, Tuple

__all__ = [
    "get_telegram_settings",
    "notify_download_complete",
    "notify_test",
    "send_telegram_message",
    "telegram_enabled",
]

HttpClient = Callable[..., Any]


def get_telegram_settings(config: Optional[dict] = None) -> Tuple[str, str]:
    """Read bot token and chat id from config.

    Parameters
    ----------
    config : dict, optional
        Config mapping; loaded when omitted.

    Returns
    -------
    (str, str)
        ``(bot_token, chat_id)`` — either may be empty.
    """
    from smart_dl.core.config import load_config

    cfg = config if config is not None else load_config()
    token = str(cfg.get("telegram_bot_token") or "").strip()
    chat_id = str(cfg.get("telegram_chat_id") or "").strip()
    return token, chat_id


def telegram_enabled(config: Optional[dict] = None) -> bool:
    """Return True when Telegram notify is configured and not disabled.

    Parameters
    ----------
    config : dict, optional
        Config mapping.

    Returns
    -------
    bool
    """
    from smart_dl.core.config import load_config

    cfg = config if config is not None else load_config()
    if cfg.get("telegram_notify") is False:
        return False
    token, chat_id = get_telegram_settings(cfg)
    return bool(token and chat_id)


def send_telegram_message(
    text: str,
    *,
    config: Optional[dict] = None,
    http: Optional[HttpClient] = None,
    timeout: float = 15.0,
) -> bool:
    """Send a Telegram bot message.

    The bot token is never included in logs or raised messages.

    Parameters
    ----------
    text : str
        Message body.
    config : dict, optional
        Config with token/chat id.
    http : Callable, optional
        Injectable HTTP client; must accept ``post(url, json=..., timeout=...)``.
    timeout : float, optional
        Request timeout seconds.

    Returns
    -------
    bool
        ``True`` when Telegram API returned ``ok``.
    """
    from smart_dl.ui import warn

    token, chat_id = get_telegram_settings(config)
    if not token or not chat_id:
        warn("Telegram notify not configured (telegram_bot_token / telegram_chat_id)")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text[:4000]}
    try:
        if http is not None:
            resp = http(url, json=payload, timeout=timeout)
        else:
            import requests

            resp = requests.post(url, json=payload, timeout=timeout)
        if getattr(resp, "status_code", 0) and int(resp.status_code) >= 400:
            # Do not echo URL (contains token).
            warn(f"Telegram notify failed (HTTP {resp.status_code})")
            return False
        try:
            data = resp.json() if callable(getattr(resp, "json", None)) else {}
        except Exception:
            data = {}
        if isinstance(data, dict) and data.get("ok") is False:
            warn("Telegram notify rejected by API")
            return False
        return True
    except Exception as exc:  # noqa: BLE001 — never leak token in message
        warn(f"Telegram notify error: {type(exc).__name__}")
        return False


def notify_download_complete(
    *,
    url: str,
    success: bool,
    title: str = "",
    error: str = "",
    config: Optional[dict] = None,
    http: Optional[HttpClient] = None,
) -> bool:
    """Send a download completion notification when Telegram is enabled.

    Parameters
    ----------
    url : str
        Source URL.
    success : bool
        Download outcome.
    title : str, optional
        Media title.
    error : str, optional
        Failure reason.
    config : dict, optional
        Config mapping.
    http : Callable, optional
        Injectable HTTP client.

    Returns
    -------
    bool
        ``True`` when a message was sent successfully.
    """
    if not telegram_enabled(config):
        return False
    status = "OK" if success else "FAILED"
    label = (title or url)[:80]
    if success:
        text = f"SmartDL {status}: {label}\n{url}"
    else:
        reason = (error or "unknown")[:120]
        text = f"SmartDL {status}: {label}\n{url}\n{reason}"
    return send_telegram_message(text, config=config, http=http)


def notify_test(
    *,
    config: Optional[dict] = None,
    http: Optional[HttpClient] = None,
) -> bool:
    """Send a test message for ``--notify-test``.

    Parameters
    ----------
    config : dict, optional
        Config mapping.
    http : Callable, optional
        Injectable HTTP client.

    Returns
    -------
    bool
    """
    return send_telegram_message("SmartDL Telegram notify test", config=config, http=http)
