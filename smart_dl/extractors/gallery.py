"""Image gallery extractor — Pixiv, DeviantArt, ArtStation, Flickr, Tumblr, Imgur."""
import re
from pathlib import Path
from urllib.parse import urlparse

import requests

from smart_dl.core.proxy import get_current_proxy
from smart_dl.ui import error, info, print_section, success, warn
from smart_dl.utils import safe_filename

try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key


# Supported gallery domains
GALLERY_DOMAINS = {
    "pixiv.net": "Pixiv",
    "www.pixiv.net": "Pixiv",
    "deviantart.com": "DeviantArt",
    "www.deviantart.com": "DeviantArt",
    "artstation.com": "ArtStation",
    "www.artstation.com": "ArtStation",
    "flickr.com": "Flickr",
    "www.flickr.com": "Flickr",
    "flic.kr": "Flickr",
    "tumblr.com": "Tumblr",
    "www.tumblr.com": "Tumblr",
    "imgur.com": "Imgur",
    "i.imgur.com": "Imgur",
    "newgrounds.com": "Newgrounds",
    "www.newgrounds.com": "Newgrounds",
}


def is_gallery_url(url: str) -> bool:
    """Check if URL is from a supported image gallery."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in GALLERY_DOMAINS


def get_gallery_platform(url: str) -> str:
    """Get the platform name for a gallery URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return GALLERY_DOMAINS.get(domain, "Unknown")


def download_gallery(url: str, out_folder: Path):
    """Download images from a gallery URL."""
    print_section("Analyzing gallery link", "\U0001f5bc")

    platform = get_gallery_platform(url)
    info("Detected platform: " + platform)

    # Try yt-dlp first (it supports many gallery sites)
    try:
        import yt_dlp

        from smart_dl.core.proxy import get_current_proxy

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": str(out_folder / "%(title)s.%(ext)s"),
            "writethumbnail": True,
        }
        prx = get_current_proxy()
        if prx:
            ydl_opts["proxy"] = prx

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        if info_dict:
            title = info_dict.get("title", "gallery")
            entries = info_dict.get("entries", [])
            if entries:
                success(f"Downloaded {len(entries)} images from {title}")
            else:
                success(f"Downloaded: {title}")
            return
    except Exception as e:
        warn("yt-dlp gallery download failed: " + str(e)[:100])

    # Fallback: direct image download
    _download_images_direct(url, out_folder)


def _download_images_direct(url: str, out_folder: Path):
    """Fallback: download images directly from the page."""
    from smart_dl.core.parallel import parallel_downloads
    from smart_dl.ui.progress import stop_event
    prx = get_current_proxy()
    proxies = {"http": prx, "https": prx} if prx else None

    try:
        resp = requests.get(url, timeout=15, proxies=proxies,
                          headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        error("Could not fetch gallery page: " + str(e)[:100])
        return

    # Extract image URLs from HTML
    img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # Also check for data-src (lazy loading)
    img_urls += re.findall(r'data-src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # Filter to actual images
    img_urls = [u for u in img_urls if any(u.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
    # Make absolute
    img_urls = [u if u.startswith('http') else urlparse(url).scheme + '://' + urlparse(url).netloc + u for u in img_urls]
    # Deduplicate
    img_urls = list(dict.fromkeys(img_urls))

    if not img_urls:
        error("No images found on the page.")
        return

    info(f"Found {len(img_urls)} images")

    # Build (url, dest) pairs
    out_folder.mkdir(parents=True, exist_ok=True)
    items: list[tuple[str, Path]] = []
    for i, img_url in enumerate(img_urls, 1):
        fname = safe_filename(urlparse(img_url).path.split('/')[-1] or f"image_{i}")
        if not any(fname.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            fname += ".jpg"
        items.append((img_url, out_folder / fname))

    # Parallel download — uses shutil.copyfileobj per worker, much faster
    # than the old single-threaded chunked loop.
    results = parallel_downloads(
        items, proxy=prx, max_workers=4, cancel=stop_event
    )
    downloaded = sum(1 for r in results if r is not None)

    success(f"Downloaded {downloaded}/{len(img_urls)} images to {out_folder}")
