# SmartDL v3.18.0

> **bad connection? hold my retry loop.**

A resilient, multi-threaded media downloader built for unstable networks.
Designed for users behind weak connections and VPNs — SmartDL never gives up.

[![Python](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.11%20|%203.12%20|%203.13%20|%203.14-blue?style=flat-square)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/support-Buy%20Me%20a%20Coffee-yellow?style=flat-square&logo=buy-me-a-coffee)](https://buymeacoffee.com/alisadeghil)
[![GitHub Downloads](https://img.shields.io/github/downloads/alisadeghiaghili/smart-dl/total?style=flat-square&label=downloads&color=blue)](https://github.com/alisadeghiaghili/smart-dl/releases)

> If SmartDL saved you from a broken download at 3am — you know what to do. ☕  
> **[buymeacoffee.com/alisadeghil](https://buymeacoffee.com/alisadeghil)**

---

## Features

### Core
- **YouTube** — full format list (all resolutions, all audio tracks), video info panel
- **Aparat, Maktabkhooneh & Faradars** — native support for Iranian video & education platforms
- **1800+ sites via yt-dlp** — TikTok, Instagram, Twitter/X, Reddit, Twitch, Vimeo, SoundCloud, and more
- **Podcasts** — direct MP3/M4A links, RSS feeds, SoundCloud, Castbox, and more

### Network Resilience
- **Infinite retry with backoff** — waits and retries on network failure; never fails silently
- **Resume downloads** — picks up exactly where it left off after a disconnect
- **Multi-threaded fragments** — up to 16 concurrent fragment downloads
- **Smart error diagnosis** — explains what went wrong and how to fix it
- **Proxy support** — configure HTTP/SOCKS5 proxy at runtime (v2ray, Clash, Hiddify, Nekoray)

### Download Features
- **Video clipping** — download only a segment (`--clip 00:01:30-00:05:00`)
- **SponsorBlock** — skip sponsor segments automatically
- **Subtitles** — download, search, and embed subtitles in 50+ languages
- **Thumbnails** — download and embed video thumbnails
- **Metadata** — embed title, artist, and other metadata
- **Audio extraction** — MP3, M4A, Opus, FLAC, WAV with quality control
- **Multiple formats** — MP4, MKV, WebM, AVI output

### Smart Mode
- **Save preferences** — set default quality, format, audio settings once
- **Auto-apply** — all downloads use your saved preferences

### Queue & History
- **Download queue** — add multiple URLs, process sequentially or in parallel
- **Download history** — SQLite database with search, filter, and export
- **Subscriptions** — follow channels and auto-download new uploads

### Extra Features
- **Image galleries** — download from Pixiv, DeviantArt, ArtStation, Flickr, Imgur
- **Torrent/magnet** — download torrents via aria2c, transmission, or qBittorrent
- **Portable mode** — run from USB stick without touching system directories
- **12 CLI themes** — Dracula, Catppuccin, Nord, Tokyo Night, and more
- **Persian/Farsi UI** — full Persian language support
- **CLI automation** — 40+ flags for scripting and automation

---

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) — required for HD video (merge) and MP3 conversion

### Install ffmpeg (Windows)

```bash
winget install Gyan.FFmpeg
```

Then close and reopen your terminal.

---

## Installation

### Option 1: pip (recommended)

```bash
pip install smart-dl
```

### Option 2: Windows portable EXE (no Python install)

Download `SmartDL-v*-win-x64.zip` from the [Releases](https://github.com/alisadeghiaghili/smart-dl/releases) page, verify `SHA256SUMS.txt`, extract, and run `SmartDL.exe`.

**If Windows SmartScreen appears:** the EXE is not code-signed. Choose **More info → Run anyway**, or install via pip instead. Antivirus false positives on PyInstaller onedir bundles are common; the zip hash on the release page lets you confirm the file you downloaded.

### Option 3: clone and run

```bash
git clone https://github.com/alisadeghiaghili/smart-dl.git
cd smart-dl
python smart_dl.py
```

Python dependencies (`yt-dlp`, `rich`, `requests`) are declared in `pyproject.toml`. Install with `pip install -e .` (or `pip install smart-dl`). Optional auto-install on first interactive run is available via `SMARTDL_AUTO_DEPS=1`.

---

## Usage

### Interactive Mode

```bash
python smart_dl.py
```

On startup:
1. Choose your **output folder** (default: `~/Downloads/SmartDL`)
2. Configure a **proxy** if needed (or press Enter to skip)
3. Paste a **URL** (YouTube, Aparat, podcast, or any supported site)
4. Select **quality/format** from the menu
5. Download starts — with resume, retry, and progress bar

### URL Prompt Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Proxy settings |
| `s` | Download settings (retries, fragment threads) |
| `c` | Cookie settings (browser auth) |
| `i` | Install dependencies (ffmpeg, Node.js) |

### CLI Mode

```bash
# Basic download
smart-dl "https://youtube.com/watch?v=abc123"

# Quality and format (presets: worst, 360, 480, 720, 1080, 1440, 4k, 8k, best)
smart-dl URL -q 1080 -o ~/Downloads
smart-dl URL -q 4k --format mkv

# Video clipping
smart-dl URL --clip 00:01:30-00:05:00

# Audio extraction
smart-dl URL --audio-only --audio-format flac --audio-quality 320

# SponsorBlock
smart-dl URL --sponsorblock

# Subtitles
smart-dl URL --subtitles en,fa --embed-subs

# Thumbnails and metadata
smart-dl URL --thumbnail --embed-thumbnail --embed-metadata

# Batch download
smart-dl --batch urls.txt -o ~/Downloads

# Queue management
smart-dl --queue add URL1 URL2 URL3
smart-dl --queue start
smart-dl --queue pause
smart-dl --queue resume
smart-dl --queue list
smart-dl --queue stats

# Download history
smart-dl --history list --sort date
smart-dl --history search "keyword"
smart-dl --history stats

# Subscriptions
smart-dl --subscribe https://youtube.com/@channel
smart-dl --check-updates          # list new uploads
# SMARTDL_SUBS_AUTODL=1 smart-dl --check-updates  # also download them
smart-dl --my-subs

# Smart Mode
smart-dl --smart-mode on
smart-dl --smart-mode config  # interactive settings

# Image galleries
smart-dl https://www.pixiv.net/artworks/12345

# Education courses (Maktabkhooneh / Faradars / Coursera)
smart-dl "https://www.coursera.org/learn/machine-learning"
smart-dl "https://www.coursera.org/learn/machine-learning" --max-lessons 5
smart-dl "https://maktabkhooneh.org/course/..." --all   # remove the 20-lesson default cap

# Torrent
smart-dl --torrent magnet:?xt=urn:btih:...

# Themes
smart-dl --theme catppuccin
smart-dl --list-themes

# Persian UI
smart-dl --lang fa

# Proxy
smart-dl --proxy socks5://127.0.0.1:10808

# Portable mode
smart-dl --portable

# Podcasts
smart-dl "https://feeds.npr.org/510289/podcast.xml"
smart-dl "https://example.com/show.xml" --all-episodes
smart-dl "https://castbox.fm/channel/id2386830" --all-episodes
smart-dl "https://soundcloud.com/user/track"

# Quiet mode with file logging
smart-dl URL --quiet --log download.log
```

### Notes

- Failed downloads exit with code `1` and do **not** print a success message.
- History records every download outcome (`--history list` / `--history stats`).
- Portable mode (`--portable` or a `portable.txt` next to the app) stores config and databases under `./data`.
- Dependency auto-install is off by default. Set `SMARTDL_AUTO_DEPS=1` only if you want first-run `pip install`.

### Authenticated courses (Maktabkhooneh / Coursera / Faradars)

Paid or enrolled lessons need a logged-in browser session:

1. Sign in to the site in Firefox/Edge/Chrome.
2. In SmartDL interactive mode press `c` and pick that browser (or set cookie browser in config).
3. Re-run the course URL. yt-dlp and the Coursera items API will reuse those cookies.

Faradars does not publish public lesson lists for most courses — use a course URL after login.

**Alternative:** export a Netscape `cookies.txt` from an extension and pass it:

```bash
smart-dl --cookies-file path/to/cookies.txt "https://www.youtube.com/watch?v=..."
```

---

## Supported Platforms

| Platform | Support |
|----------|---------|
| YouTube (videos, playlists, channels, Shorts) | ✅ |
| Aparat (videos, playlists) | ✅ |
| TikTok / Instagram / Twitter / Reddit / Twitch / Vimeo / … | via yt-dlp |
| 1800+ yt-dlp sites | via yt-dlp |
| Direct MP3/M4A links | ✅ |
| RSS podcast feeds | ✅ |
| Filimo / Namasha / Radio Javan | metadata + yt-dlp |
| Maktabkhooneh / Faradars | course outline + lessons via cookies (paid = your logged-in session) |
| Coursera | course title + weekly modules (public); lecture items when browser cookies are available |
| Udemy / Hotmart / Teachable / … | **public metadata only** — paid/DRM content is not downloadable without your own authorized access and will usually fail |

---

## Network Resilience

Built specifically for unstable connections:

- Resumes partial downloads automatically (no re-downloading from scratch)
- Exponential backoff retry (5s → 7s → 11s → ... up to 5 min)
- 30-minute retry duration cap (configurable)
- Fatal errors (ffmpeg missing, private video, copyright block) fail immediately
- Connection drops are silently handled; download continues when network returns

---

## Disclaimer

SmartDL is intended for **personal use only**. Downloading copyrighted content without permission may violate YouTube's Terms of Service and applicable laws in your country. The author is not responsible for any misuse of this tool. Always respect content creators and copyright holders.

---

## ☕ Support

SmartDL is free and always will be.  
Sponsorships fund faster releases, better diagnostics, and long-term maintenance.

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/alisadeghil)

---

## License

[Apache-2.0](LICENSE) — permissive with an explicit patent grant; proprietary tools may link without copyleft.

See [ROADMAP.md](ROADMAP.md) for planned features.
