# Changelog

All notable changes to SmartDL are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.2.0] — 2026-04-09

### Added
- Download settings menu (`s` at URL prompt) — configure max retries and fragment thread count at runtime
- Smart error diagnosis — human-readable explanations and fix hints for common errors (ffmpeg missing, private video, geo-block, age-restriction, etc.)
- `_FATAL_ERRORS` list in retry logic — permanent errors (ffmpeg, copyright, private video) now fail immediately instead of retrying forever
- Warning suppression for noisy yt-dlp messages (JS runtime warning, DASH container notice)
- "Continue downloading?" prompt after each completed download
- Output folder suggestion with default path (`~/Downloads/SmartDL`) shown before prompt
- Author credit (`by Hellch!ef`) displayed in CLI header

### Fixed
- Raw audio formats (m4a, opus) were incorrectly blocked by the ffmpeg check — now only MP3 conversion and video merge require ffmpeg
- ffmpeg check now also applies to `bestvideo+bestaudio` merge formats, not just MP3
- Progress bar was rendering twice after download completion — fixed by moving success message outside the Rich `Progress` context
- Proxy menu prompt showed empty `()` — replaced with `(Enter / p)` for clarity

### Changed
- ASCII art header with hacker-style box added to source file
- `retry_with_backoff` now distinguishes fatal vs. network errors

---

## [2.1.0] — 2026-04-09

### Added
- ffmpeg presence check before attempting MP3 or merge downloads
- Warning panel shown when ffmpeg is missing with install instructions
- Multi-thread fragment downloads (default: 4 concurrent)
- Infinite retry with exponential backoff for network errors
- Resume support via yt-dlp `continuedl` option
- Proxy configuration menu at runtime (HTTP and SOCKS5)
- Common proxy port presets (v2rayN, Clash, Squid)
- RSS feed parsing for podcast batch downloads
- Episode selection for RSS feeds

### Changed
- Rebranded to SmartDL
- Rich-based CLI with progress bars, panels, and color output

---

## [1.0.0] — 2026-04-09

### Added
- Initial release
- YouTube video/audio download via yt-dlp
- Direct podcast URL download
- Auto-install missing Python dependencies on first run
- Output folder selection
