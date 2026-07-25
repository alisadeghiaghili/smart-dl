"""Persian platform extractors — Filimo, Namasha, Radio Javan, and more."""
from __future__ import annotations
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict

from smart_dl.ui import console, success, warn, error, info, print_section
from smart_dl.core.proxy import get_current_proxy

try:
    from smart_dl.lang import t
except ImportError:
    def t(key: str, **kw) -> str:
        return key


# ─── Filimo ──────────────────────────────────────────────────────────────
def is_filimo_url(url: str) -> bool:
    """Check if URL is from Filimo."""
    parsed = urlparse(url)
    return "filimo.com" in parsed.netloc.lower()


def extract_filimo_info(url: str) -> Optional[Dict]:
    """Extract video info from Filimo URL."""
    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            # Try og:title
            title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', resp.text)
            if not title_match:
                title_match = re.search(r'<title>([^<]+)</title>', resp.text)
            title = title_match.group(1).strip() if title_match else "Filimo Video"

            # Try og:video
            video_match = re.search(r'<meta[^>]+property="og:video"[^>]+content="([^"]+)"', resp.text)
            video_url = video_match.group(1) if video_match else None

            return {
                "platform": "Filimo",
                "title": title,
                "url": url,
                "video_url": video_url,
            }
    except Exception:
        pass

    return None


def download_filimo(url: str, out_folder: Path):
    """Download video from Filimo."""
    print_section("Analyzing Filimo link", "\U0001f3ac")

    info_dict = extract_filimo_info(url)
    if info_dict:
        info(f"Title: {info_dict.get('title', '?')}")

    # Try yt-dlp (Filimo may be supported)
    from smart_dl.extractors.youtube import get_yt_formats, yt_quality_menu, download_yt

    vid_info = get_yt_formats(url)
    if vid_info:
        fmt, is_audio = yt_quality_menu(vid_info)
        if fmt is not None:
            download_yt(url, out_folder, fmt, is_audio)
    else:
        error("Could not extract video from Filimo.")
        info("Make sure the video is public and the URL is correct.")


# ─── Namasha ─────────────────────────────────────────────────────────────
def is_namasha_url(url: str) -> bool:
    """Check if URL is from Namasha."""
    parsed = urlparse(url)
    return "namasha.com" in parsed.netloc.lower()


def extract_namasha_info(url: str) -> Optional[Dict]:
    """Extract video info from Namasha URL."""
    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', resp.text)
            if not title_match:
                title_match = re.search(r'<title>([^<]+)</title>', resp.text)
            title = title_match.group(1).strip() if title_match else "Namasha Video"

            return {
                "platform": "Namasha",
                "title": title,
                "url": url,
            }
    except Exception:
        pass

    return None


def download_namasha(url: str, out_folder: Path):
    """Download video from Namasha."""
    print_section("Analyzing Namasha link", "\U0001f3ac")

    info_dict = extract_namasha_info(url)
    if info_dict:
        info(f"Title: {info_dict.get('title', '?')}")

    from smart_dl.extractors.youtube import get_yt_formats, yt_quality_menu, download_yt

    vid_info = get_yt_formats(url)
    if vid_info:
        fmt, is_audio = yt_quality_menu(vid_info)
        if fmt is not None:
            download_yt(url, out_folder, fmt, is_audio)
    else:
        error("Could not extract video from Namasha.")


# ─── Radio Javan ─────────────────────────────────────────────────────────
def is_radiojavan_url(url: str) -> bool:
    """Check if URL is from Radio Javan."""
    parsed = urlparse(url)
    return "radiojavan.com" in parsed.netloc.lower()


def extract_radiojavan_info(url: str) -> Optional[Dict]:
    """Extract music info from Radio Javan URL."""
    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', resp.text)
            if not title_match:
                title_match = re.search(r'<title>([^<]+)</title>', resp.text)
            title = title_match.group(1).strip() if title_match else "Radio Javan Track"

            # Try to find MP3 link
            mp3_match = re.search(r'(https?://[^"\']+\.mp3)', resp.text)
            mp3_url = mp3_match.group(1) if mp3_match else None

            return {
                "platform": "Radio Javan",
                "title": title,
                "url": url,
                "mp3_url": mp3_url,
            }
    except Exception:
        pass

    return None


def download_radiojavan(url: str, out_folder: Path):
    """Download music from Radio Javan."""
    print_section("Analyzing Radio Javan link", "\U0001f3b5")

    info_dict = extract_radiojavan_info(url)
    if info_dict:
        info(f"Title: {info_dict.get('title', '?')}")

        # If we found a direct MP3 link, download it
        mp3_url = info_dict.get("mp3_url")
        if mp3_url:
            from smart_dl.utils import safe_filename
            fname = safe_filename(info_dict.get("title", "track")) + ".mp3"
            fpath = out_folder / fname
            try:
                prx = get_current_proxy()
                proxies = {"http": prx, "https": prx} if prx else None
                resp = requests.get(mp3_url, proxies=proxies, stream=True, timeout=30)
                resp.raise_for_status()
                with open(fpath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                success(f"Downloaded: {fname}")
                return
            except Exception as e:
                warn(f"Direct download failed: {str(e)[:100]}")

    # Fallback to yt-dlp
    from smart_dl.extractors.youtube import get_yt_formats, yt_quality_menu, download_yt

    vid_info = get_yt_formats(url)
    if vid_info:
        fmt, is_audio = yt_quality_menu(vid_info)
        if fmt is not None:
            download_yt(url, out_folder, fmt, is_audio)
    else:
        error("Could not extract music from Radio Javan.")


# ─── Universal Persian Platform Router ───────────────────────────────────
PERSIAN_EXTRACTORS = {
    "filimo.com": ("Filimo", download_filimo),
    "namasha.com": ("Namasha", download_namasha),
    "radiojavan.com": ("Radio Javan", download_radiojavan),
}


def is_persian_platform(url: str) -> bool:
    """Check if URL is from any supported Persian platform."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in PERSIAN_EXTRACTORS


def get_persian_platform(url: str) -> Optional[str]:
    """Get the platform name for a Persian URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    if domain in PERSIAN_EXTRACTORS:
        return PERSIAN_EXTRACTORS[domain][0]
    return None


def download_persian_platform(url: str, out_folder: Path):
    """Download from any supported Persian platform."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    if domain in PERSIAN_EXTRACTORS:
        name, downloader = PERSIAN_EXTRACTORS[domain]
        info(f"Detected Persian platform: {name}")
        downloader(url, out_folder)
    else:
        error(f"Unsupported Persian platform: {domain}")
