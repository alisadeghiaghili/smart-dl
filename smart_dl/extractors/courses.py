"""Online course extractor — Udemy, Hotmart, Kiwify, Teachable, and more."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import requests

from smart_dl.core.proxy import get_current_proxy
from smart_dl.ui import console, error, info, print_section, warn

try:
    from smart_dl.lang import t
except ImportError:
    def t(key: str, **kw) -> str:
        return key


# ─── Platform Detection ──────────────────────────────────────────────────
COURSE_DOMAINS = {
    "udemy.com": "Udemy",
    "www.udemy.com": "Udemy",
    "hotmart.com": "Hotmart",
    "www.hotmart.com": "Hotmart",
    "kiwify.com": "Kiwify",
    "www.kiwify.com": "Kiwify",
    "teachable.com": "Teachable",
    "www.teachable.com": "Teachable",
    "kajabi.com": "Kajabi",
    "www.kajabi.com": "Kajabi",
    "skool.com": "Skool",
    "www.skool.com": "Skool",
    "thinkific.com": "Thinkific",
    "www.thinkific.com": "Thinkific",
    "gumroad.com": "Gumroad",
    "www.gumroad.com": "Gumroad",
    "rocketseat.com.br": "Rocketseat",
    "wondrium.com": "Wondrium",
    "www.wondrium.com": "Wondrium",
    "podia.com": "Podia",
    "www.podia.com": "Podia",
    "learnworlds.com": "LearnWorlds",
    "www.learnworlds.com": "LearnWorlds",
    "payhip.com": "Payhip",
    "www.payhip.com": "Payhip",
    "shopify.com": "Shopify",
    "www.shopify.com": "Shopify",
}


def is_course_url(url: str) -> bool:
    """Check if URL is from a supported course platform."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in COURSE_DOMAINS


def get_course_platform(url: str) -> str:
    """Get the platform name for a course URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return COURSE_DOMAINS.get(domain, "Unknown")


# ─── Udemy Extractor ─────────────────────────────────────────────────────
def extract_udemy_info(url: str) -> Optional[Dict]:
    """Extract course info from Udemy URL."""
    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None

    # Try to extract course ID from URL
    # Udemy URLs: /course/course-name/ or /course/course-name/learn/
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    course_slug = None
    if len(path_parts) >= 2 and path_parts[0] == "course":
        course_slug = path_parts[1]
    elif len(path_parts) >= 1:
        course_slug = path_parts[0]

    if not course_slug:
        return None

    # Try Udemy API (public endpoint)
    api_url = f"https://www.udemy.com/api-2.0/courses/{course_slug}/?fields[course]=title,primary_category,primary_subcategory,avg_rating,num_reviews,content_info,instructional_level,locale,created_published_time,url,desc"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(api_url, headers=headers, proxies=proxies, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "platform": "Udemy",
                "title": data.get("title", "Unknown"),
                "url": url,
                "slug": course_slug,
                "rating": data.get("avg_rating"),
                "reviews": data.get("num_reviews"),
                "level": data.get("instructional_level"),
                "content_info": data.get("content_info", ""),
            }
    except Exception:
        pass

    # Fallback: scrape the page
    try:
        resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        if resp.status_code == 200:
            # Try to extract from meta tags
            title_match = re.search(r'<meta[^>]+name="title"[^>]+content="([^"]+)"', resp.text)
            if not title_match:
                title_match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', resp.text)
            title = title_match.group(1) if title_match else course_slug.replace("-", " ").title()

            return {
                "platform": "Udemy",
                "title": title,
                "url": url,
                "slug": course_slug,
            }
    except Exception:
        pass

    return None


# ─── Hotmart Extractor ──────────────────────────────────────────────────
def extract_hotmart_info(url: str) -> Optional[Dict]:
    """Extract course info from Hotmart URL."""
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
            title = title_match.group(1).strip() if title_match else "Hotmart Course"

            return {
                "platform": "Hotmart",
                "title": title,
                "url": url,
            }
    except Exception:
        pass

    return None


# ─── Generic Course Extractor ────────────────────────────────────────────
def extract_course_info(url: str) -> Optional[Dict]:
    """Extract course info from any supported platform."""
    platform = get_course_platform(url)

    if platform == "Udemy":
        return extract_udemy_info(url)
    elif platform == "Hotmart":
        return extract_hotmart_info(url)
    else:
        # Generic extraction
        return _extract_generic_course(url, platform)


def _extract_generic_course(url: str, platform: str) -> Optional[Dict]:
    """Generic course info extraction."""
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
            title = title_match.group(1).strip() if title_match else f"{platform} Course"

            return {
                "platform": platform,
                "title": title,
                "url": url,
            }
    except Exception:
        pass

    return None


# ─── Course Download ─────────────────────────────────────────────────────
def download_course(url: str, out_folder: Path):
    """Download a course from any supported platform."""
    print_section("Analyzing course link", "\U0001f393")

    platform = get_course_platform(url)
    info(f"Detected platform: {platform}")

    # Extract course info
    course_info = extract_course_info(url)
    if course_info:
        _show_course_info(course_info)
    else:
        warn("Could not extract course info. Trying yt-dlp...")

    # Try yt-dlp for actual download
    from smart_dl.extractors.youtube import download_yt, get_yt_formats, yt_quality_menu

    vid_info = get_yt_formats(url)
    if vid_info:
        fmt, is_audio = yt_quality_menu(vid_info)
        if fmt is not None:
            download_yt(url, out_folder, fmt, is_audio)
    else:
        error(f"Could not download from {platform}.")
        info("Make sure you have access to this course and the URL is correct.")


def _show_course_info(course_info: Dict):
    """Display course info panel."""
    from rich.panel import Panel

    title = course_info.get("title", "Unknown")
    platform = course_info.get("platform", "Unknown")
    rating = course_info.get("rating")
    reviews = course_info.get("reviews")
    level = course_info.get("level")

    body = (
        f"[bold white]{title}[/bold white]\n"
        f"[dim]Platform:[/dim] [cyan]{platform}[/cyan]"
    )
    if rating:
        body += f"   [dim]Rating:[/dim] [yellow]{rating:.1f}[/yellow]"
    if reviews:
        body += f"   [dim]Reviews:[/dim] [green]{reviews:,}[/green]"
    if level:
        body += f"\n[dim]Level:[/dim] [magenta]{level}[/magenta]"

    console.print(Panel(body, border_style="cyan", title="[bold]Course Info[/bold]", padding=(0,2)))
