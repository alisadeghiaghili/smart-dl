# SmartDL

> **bad connection? hold my retry loop.**

A resilient, multi-threaded YouTube & podcast downloader built for unstable networks.
Designed for users behind weak connections and VPNs — SmartDL never gives up.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/support-Buy%20Me%20a%20Coffee-yellow?style=flat-square&logo=buy-me-a-coffee)](https://buymeacoffee.com/alisadeghil)

> If SmartDL saved you from a broken download at 3am — you know what to do. ☕  
> **[buymeacoffee.com/alisadeghil](https://buymeacoffee.com/alisadeghil)**

---

## Features

- **YouTube** — full format list (all resolutions, all audio tracks), video info panel, or MP3 conversion
- **Podcasts** — direct MP3/M4A links, RSS feeds, SoundCloud, and more
- **Resume downloads** — picks up exactly where it left off after a disconnect
- **Infinite retry with backoff** — waits and retries on network failure; never fails silently
- **Multi-threaded fragments** — up to 16 concurrent fragment downloads
- **Smart error diagnosis** — explains what went wrong and how to fix it
- **Proxy support** — configure HTTP/SOCKS5 proxy at runtime (v2ray, Clash, etc.)
- **Configurable settings** — adjust retry count and fragment threads on the fly
- **Zero-config setup** — missing Python packages are installed automatically on first run
- **Beautiful CLI** — rich progress bars, color output, and clear status messages

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

No installation needed. Just clone and run:

```bash
git clone https://github.com/alisadeghiaghili/smart-dl.git
cd smart-dl
python smart_dl.py
```

Python dependencies (`yt-dlp`, `rich`, `requests`) are installed automatically on first run.

---

## Usage

```bash
python smart_dl.py
```

On startup:
1. Choose your **output folder** (default: `~/Downloads/SmartDL`)
2. Configure a **proxy** if needed (or press Enter to skip)
3. Paste a **YouTube or podcast URL**
4. Select **quality/format** from the menu
5. Download starts — with resume, retry, and progress bar

### URL prompt shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Proxy settings |
| `s` | Download settings (retries, fragment threads) |

---

## Supported Sources

| Source | Support |
|--------|---------|
| YouTube videos | ✅ |
| YouTube playlists | ✅ |
| Direct MP3/M4A links | ✅ |
| RSS podcast feeds | ✅ |
| SoundCloud | ✅ |
| Anchor / Spotify (public) | ✅ |

---

## Network Resilience

Built specifically for unstable connections:

- Resumes partial downloads automatically (no re-downloading from scratch)
- Exponential backoff retry (5s → 7s → 11s → ... up to 5 min)
- Fatal errors (ffmpeg missing, private video, copyright block) fail immediately — no pointless retrying
- Connection drops are silently handled; download continues when network returns

---

## Disclaimer

SmartDL is intended for **personal use only**. Downloading copyrighted content without permission may violate YouTube’s Terms of Service and applicable laws in your country. The author is not responsible for any misuse of this tool. Always respect content creators and copyright holders.

---

## ☕ Support

SmartDL is free, ad-free, and built on stubbornness.  
If it saved your download, your sanity, or your deadline — a coffee goes a long way:

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://buymeacoffee.com/alisadeghil)

No pressure. But karma is real.

---

## License

[MIT](LICENSE)
