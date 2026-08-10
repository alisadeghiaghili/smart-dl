"""SmartDL Web GUI — Streamlit-based web interface."""
import os
import sys
from pathlib import Path

# Ensure we can import smart_dl
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ['SMARTDL_NO_DEPS'] = '1'

import streamlit as st
import yt_dlp

from smart_dl import VERSION
from smart_dl.core.downloader import build_download_opts, get_smart_mode, save_smart_mode
from smart_dl.core.history import get_history, get_history_stats
from smart_dl.core.history import init_db as init_history_db
from smart_dl.core.proxy import apply_proxy, clear_proxy, get_current_proxy
from smart_dl.core.queue import clear_queue, get_queue, get_queue_stats
from smart_dl.core.queue import init_db as init_queue_db
from smart_dl.utils import fmt_dur, fmt_size, is_aparat_url, is_playlist_url, is_youtube_url

# Page config
st.set_page_config(
    page_title="SmartDL v" + VERSION,
    page_icon="⬇️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Init databases
init_queue_db()
init_history_db()


def get_yt_info(url: str):
    """Fetch video info from URL."""
    ydl_opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    prx = get_current_proxy()
    if prx:
        ydl_opts["proxy"] = prx
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        st.error(f"Error: {str(e)[:200]}")
        return None


def do_download(url: str, out_dir: str, fmt: str, is_audio: bool = False,
                clip: str = None, sponsorblock: bool = False,
                audio_format: str = "mp3", audio_quality: str = "192",
                embed_metadata: bool = False, embed_thumbnail: bool = False):
    """Download a URL."""
    from smart_dl.core.retry import retry_with_backoff
    from smart_dl.settings import DL_SETTINGS

    opts = build_download_opts(
        fmt=fmt, is_audio=is_audio, clip=clip, sponsorblock=sponsorblock,
        audio_format=audio_format, audio_quality=audio_quality,
        embed_metadata=embed_metadata, embed_thumbnail=embed_thumbnail,
    )
    opts["outtmpl"] = str(Path(out_dir) / "%(title)s [%(format_id)s].%(ext)s")
    opts["quiet"] = True
    opts["progress_hooks"] = []

    def _do():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    maxr = DL_SETTINGS["max_retries"]
    try:
        retry_with_backoff(_do, max_retries=maxr)
        return True
    except Exception as e:
        st.error(f"Download failed: {str(e)[:200]}")
        return False


# ─── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/SmartDL-v" + VERSION + "-cyan?style=for-the-badge", use_container_width=True)
    st.markdown("---")

    # Settings
    st.subheader("⚙️ Settings")
    out_dir = st.text_input("Output Directory", str(Path.home() / "Downloads" / "SmartDL"), help="The folder where all your downloaded media will be saved.")

    # Proxy
    proxy = get_current_proxy()
    proxy_input = st.text_input("Proxy", proxy or "", placeholder="socks5://127.0.0.1:10808", help="Use this if YouTube or other sites are blocked. E.g., http://127.0.0.1:8080 or socks5://127.0.0.1:10808")
    if proxy_input and proxy_input != proxy:
        apply_proxy(proxy_input)
        st.success("Proxy set!")
    elif not proxy_input and proxy:
        clear_proxy()

    # Smart Mode
    smart = get_smart_mode()
    smart_enabled = st.toggle("Smart Mode", smart.get("enabled", False), help="Enable to automatically apply your favorite settings (quality, format, etc.) to all future downloads without asking.")
    if smart_enabled != smart.get("enabled"):
        smart["enabled"] = smart_enabled
        save_smart_mode(smart)

    st.markdown("---")

    # Queue stats
    stats = get_queue_stats()
    st.subheader("📊 Stats")
    col1, col2 = st.columns(2)
    col1.metric("Queue", stats["pending"])
    col2.metric("Completed", stats["completed"])

    # History stats
    h_stats = get_history_stats()
    col1, col2 = st.columns(2)
    col1.metric("Downloads", h_stats["total_downloads"])
    col2.metric("Size", fmt_size(h_stats["total_size"]))


# ─── Main Content ─────────────────────────────────────────────────────────
st.title("⬇️ SmartDL v" + VERSION)
st.caption("Resilient media downloader for unstable networks")

# URL input
url = st.text_input("🔗 Paste URL", placeholder="https://youtube.com/watch?v=... or https://aparat.com/v/...")

if url:
    # Detect platform
    if is_youtube_url(url):
        platform = "YouTube"
    elif is_aparat_url(url):
        platform = "Aparat"
    elif is_playlist_url(url):
        platform = "Playlist"
    else:
        platform = "Other"

    st.info(f"Detected: **{platform}**")

    if st.button("🔍 Analyze", type="primary"):
        with st.spinner("Fetching video info..."):
            info = get_yt_info(url)

        if info:
            st.session_state["info"] = info
            st.session_state["url"] = url

# Display video info if available
if "info" in st.session_state:
    info = st.session_state["info"]
    url = st.session_state.get("url", "")

    # Video info card
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(info.get("title", "Unknown"))
        st.write(f"**Channel:** {info.get('uploader') or info.get('channel', '?')}")
        st.write(f"**Duration:** {fmt_dur(info.get('duration'))}")
        views = info.get("view_count")
        if views:
            st.write(f"**Views:** {views:,}")

    with col2:
        # Thumbnail
        thumbs = info.get("thumbnails", [])
        if thumbs:
            best = max(thumbs, key=lambda t: (t.get("width", 0) * t.get("height", 0)))
            st.image(best.get("url", ""), use_container_width=True)

    st.markdown("---")

    # Format selection
    fmts = info.get("formats", [])
    if fmts:
        st.subheader("📋 Available Formats")

        # Categorize formats
        combos = [f for f in fmts if f.get("vcodec", "none") != "none" and f.get("acodec", "none") != "none"]
        video_only = [f for f in fmts if f.get("vcodec", "none") != "none" and f.get("acodec", "none") == "none"]
        audio_only = [f for f in fmts if f.get("vcodec", "none") == "none" and f.get("acodec", "none") != "none"]

        # Format selector
        format_type = st.radio("Format Type", ["Video+Audio", "Video Only", "Audio Only", "Best Quality", "Audio MP3"], horizontal=True)

        if format_type == "Video+Audio":
            options = []
            for f in combos[:10]:
                h = f.get("height", "?")
                ext = f.get("ext", "?")
                vc = (f.get("vcodec") or "")[:10]
                ac = (f.get("acodec") or "")[:8]
                sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
                label = f"{h}p {ext} ({vc}+{ac}) — {sz}"
                options.append((label, f.get("format_id", "best")))

            if options:
                choice = st.selectbox("Select quality", options, format_func=lambda x: x[0])
                selected_fmt = choice[1]
            else:
                selected_fmt = "best"
                st.warning("No combined formats available")

        elif format_type == "Video Only":
            options = []
            for h in [2160, 1440, 1080, 720, 480, 360, 240, 144]:
                m = [f for f in video_only if f.get("height") == h]
                if m:
                    f = m[0]
                    sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
                    label = f"{h}p — {sz} (needs ffmpeg)"
                    options.append((label, f"bestvideo[height<={h}]+bestaudio/best"))

            if options:
                choice = st.selectbox("Select resolution", options, format_func=lambda x: x[0])
                selected_fmt = choice[1]
            else:
                selected_fmt = "bestvideo+bestaudio/best"

        elif format_type == "Audio Only":
            options = []
            for f in audio_only[:4]:
                abr = f.get("abr", "?")
                sz = fmt_size(f.get("filesize") or f.get("filesize_approx"))
                label = f"{abr} kbps — {sz}"
                options.append((label, f.get("format_id", "best")))

            if options:
                choice = st.selectbox("Select bitrate", options, format_func=lambda x: x[0])
                selected_fmt = choice[1]
            else:
                selected_fmt = "bestaudio/best"

        elif format_type == "Best Quality":
            selected_fmt = "bestvideo+bestaudio/best"

        else:  # Audio MP3
            selected_fmt = "bestaudio/best"

        is_audio = format_type in ("Audio Only", "Audio MP3")

        # Advanced options
        with st.expander("🎛️ Advanced Options"):
            col1, col2 = st.columns(2)
            with col1:
                clip = st.text_input("Video Clip", placeholder="00:01:30-00:05:00", help="Download only a specific segment. Format: HH:MM:SS-HH:MM:SS (e.g., 00:01:30-00:05:00).")
                sponsorblock = st.checkbox("SponsorBlock", help="Automatically skip/remove sponsor segments from YouTube videos.")
                embed_metadata = st.checkbox("Embed Metadata", help="Save video title, author, and description directly into the file.")
            with col2:
                audio_format = st.selectbox("Audio Format", ["mp3", "m4a", "opus", "flac", "wav"], help="The format used when extracting audio.")
                audio_quality = st.selectbox("Audio Quality", ["128", "192", "256", "320"], help="Audio bitrate in kbps. Higher means better quality but larger file size.")
                embed_thumbnail = st.checkbox("Embed Thumbnail", help="Embed the video thumbnail as the cover art for the downloaded file.")

        # Download button
        if st.button("⬇️ Download", type="primary", use_container_width=True):
            with st.spinner("Downloading..."):
                success = do_download(
                    url, out_dir, selected_fmt, is_audio,
                    clip=clip or None, sponsorblock=sponsorblock,
                    audio_format=audio_format, audio_quality=audio_quality,
                    embed_metadata=embed_metadata, embed_thumbnail=embed_thumbnail,
                )
                if success:
                    st.success("Download complete!")
                    st.balloons()


# ─── Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📥 Queue", "📜 History", "ℹ️ About"])

with tab1:
    st.subheader("Download Queue")

    queue = get_queue()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start Queue", disabled=not bool(queue)):
            st.info("Queue processing started")
    with col2:
        if st.button("🗑️ Clear Queue", disabled=not bool(queue)):
            clear_queue()
            st.success("Queue cleared")
            st.rerun() # Refresh to update button state
    with col3:
        st.metric("Pending", get_queue_stats()["pending"])

    if queue:

        for item in queue:
            status_color = {"pending": "🟡", "active": "🔵", "completed": "🟢", "failed": "🔴"}.get(item["status"], "⚪")
            st.write(f"{status_color} [{item['id']}] {item['url'][:60]} — {item['status']}")
    else:
        st.info("Queue is empty. Paste a URL above to add downloads.")

with tab2:
    st.subheader("Download History")
    history = get_history(limit=20)
    if history:
        for h in history:
            from datetime import datetime
            ts = h.get("downloaded_at", 0)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "?"
            st.write(f"**{h.get('title', '?')[:50]}** — {h.get('platform', '?')} — {date_str}")
    else:
        st.info("No download history yet.")

with tab3:
    st.subheader("About SmartDL")
    st.markdown(f"""
    **SmartDL v{VERSION}** — Resilient media downloader for unstable networks.

    ### Features
    - YouTube, Aparat, 1800+ sites
    - Video clipping, SponsorBlock
    - Subtitles, thumbnails, metadata
    - Download queue & history
    - Persian/Farsi UI
    - Proxy support (v2ray, Clash, Hiddify)

    ### Links
    - [GitHub](https://github.com/alisadeghiaghili/smart-dl)
    - [Buy Me a Coffee](https://buymeacoffee.com/alisadeghil)
    """)


# ─── Run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pass
