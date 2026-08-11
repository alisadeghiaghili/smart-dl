# Changelog

All notable changes to SmartDL are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] - 2026-08-09

### Added
- Complete rewrite from single-file monolith (1979 lines) to modular package (33 modules)
- SQLite-backed download queue, history, and channel subscriptions
- Video clipping (`--clip START-END`)
- SponsorBlock integration
- Smart Mode (save default preferences)
- Download queue with SQLite persistence
- Download history with search/filter/export
- Channel subscriptions (auto-download new uploads)
- Subtitle download/embed (50+ languages)
- Thumbnail download/embed
- Metadata embedding
- Audio extraction (MP3/M4A/Opus/FLAC/WAV)
- Multiple output formats (MP4/MKV/WebM/AVI)
- Image gallery support (Pixiv/DeviantArt/ArtStation/Flickr/Imgur)
- Torrent/magnet download (aria2c/transmission/qBittorrent)
- Portable mode (USB stick)
- 12 CLI themes (Dracula, Catppuccin, Nord, etc.)
- Geo-bypass and browser impersonation
- Quiet mode with file logging
- 40+ CLI flags for full automation
- Persian platform extractors: Filimo, Namasha, Radio Javan
- Online course download support (Udemy, Hotmart, Kiwify, Teachable, and 15+ platforms)
- Streamlit web GUI
- `--diagnose` CLI flag for environment self-diagnosis
- Parallel downloads via `core/parallel.py` (per-thread direct-to-disk)
- CI pipeline with GitHub Actions (Python 3.8/3.10/3.12, ruff, pytest)
- PyPI publish workflow

### Changed
- Split `smart_dl.py` into `smart_dl/` package with `core/`, `extractors/`, `ui/`, `lang/`
- Proper `pyproject.toml` packaging with setuptools backend
- Retry duration cap (30min vs infinite loop)
- `signal.SIGTERM` crash on Windows fixed
- Shell injection in PATH modification fixed
- `_save_config` error handling improved
- `fmt_size(0)` returning `?` instead of `0 B` fixed
- Variable shadowing built-in `info()` fixed
- Proxy detection: prefer SOCKS over HTTP/HTTPS in Windows registry parse
- Read `ALL_PROXY`, `SOCKS5_PROXY`, `socks_proxy`, `SOCKS_PROXY`, `SOCKS4_PROXY` env vars
- Split proxy read from write: `peek_current_proxy()` is read-only
- `apply_proxy()` validates URL and rejects malformed input
- Collapse nested `make_progress()` in youtube.py into single outer progress
- Replace global `_no_internet_shown` with per-host set
- Honor `SMARTDL_NO_DEPS` in `__init__.py` so tests skip auto-install
- Drop broken `__import__('os')` duplicates of `is_magnet_link` and `is_torrent_file`
- Fix pre-existing F821 (undefined names) and F601 (duplicate dict key)
- ruff --fix cleans up unsorted imports

### Fixed
- SOCKS5 proxy detection bug: old code returned malformed URL like `http://socks=127.0.0.1:10808`
- Frozen spinner symptom in downloads
- `no internet` panel now fires once per host, not once globally

---

## [2.5.3] - 2026-04-16

### Fixed
- Non-YouTube playlist URLs (e.g. Aparat) now return a clean "Unsupported URL"
  error instead of crashing with an unhandled exception
- Connection Error panel now shows the actual failing host from the URL
  instead of always displaying `www.youtube.com`
- Playlist fetch timeout/network errors correctly identify the target host
  in the error panel

---

## [2.5.2] - 2026-04-16

### Added
- `c` shortcut at URL prompt — opens Cookie Settings menu directly
- Cookie Settings menu — view, keep, or clear the saved browser cookie source
- Node.js detection in bot-detection flow — if cookies are valid but Node.js
  is missing, user is prompted to install it via `_fix_youtube_deps()`
- "Almost there!" panel after Node.js installation with clear next-steps

### Changed
- Bot-detection flow now distinguishes between "not logged in" and
  "cookies OK but JS challenge failed" — surfaces the right fix each time
- `YTLogger.warning()` now suppresses additional noisy yt-dlp messages:
  impersonation notices, XML parse errors, generic extractor fallback

### Fixed
- `WinError 10061` proxy-unreachable error in `_download_yt()` — now offers
  clear-and-retry instead of showing a raw traceback
- `_get_yt_formats()` proxy-unreachable path now also clears proxy and retries

---

## [2.5.1] - 2026-04-15

### Added
- `_handle_bot_detection()` — full browser cookie auth flow when YouTube
  triggers a sign-in or bot check
- Auto-scans installed browsers (Firefox, Edge, Chrome, Chromium, Brave)
  for a logged-in YouTube session — no extension or export needed
- Saves working browser as `cookie_browser` in config for future downloads
- Manual sign-in flow: opens browser, waits for user, then re-reads cookies
- `_try_browser_cookies()` — isolated test function that validates cookies
  without affecting the main download options

### Changed
- `_get_yt_formats()` now calls `_handle_bot_detection()` on sign-in wall
  instead of returning None silently

---

## [2.5.0] - 2026-04-14

### Added
- YouTube playlist support — `_handle_playlist()` with full entry enumeration
- Playlist mode selector: apply one quality to all, or pick per-video
- Skipped videos panel with retry option after playlist completes
- `_is_playlist_url()` — detects YouTube and generic `/playlist/` URLs
- `_fix_youtube_deps()` — combined yt-dlp updater + Node.js installer
- Install menu option 3: "Fix YouTube bot detection"
- `_has_nodejs()` — checks for Node.js presence via `shutil.which`
- Windows Terminal install + relaunch flow (`_install_wt`, `_relaunch_in_wt`)
- `_settings_menu()` — accessible via `s` at URL prompt (was inline before)

### Changed
- Install menu restructured: ffmpeg / Windows Terminal / YouTube fix
- Version bumped to 2.5.0

---

## [2.4.0] - 2026-04-12

### Added
- `_handle_bot_detection()` — full browser cookie auth flow for YouTube
  sign-in walls and bot-check errors
- Auto-scan for installed browsers (Firefox, Edge, Chrome, Chromium, Brave)
  to find a logged-in YouTube session — no extension or manual export needed
- `_try_browser_cookies()` — isolated cookie validation without affecting
  main download flow
- Saves working browser as `cookie_browser` in config for future sessions
- Manual sign-in fallback: opens browser, waits for user, then re-reads cookies
- `cookie_settings_menu()` — view, keep, or clear the saved browser cookie source
- `c` shortcut at URL prompt — opens Cookie Settings menu directly
- `_has_nodejs()` — checks Node.js presence via `shutil.which`
- `_fix_youtube_deps()` — combined yt-dlp updater + Node.js installer
- Install menu option 3: "Fix YouTube bot detection"
- Node.js detection in bot-detection flow — prompts install if cookies valid
  but JS challenge fails
- "Almost there!" guidance panel after Node.js installation

### Changed
- `_get_yt_formats()` now calls `_handle_bot_detection()` on sign-in wall
  instead of returning `None` silently
- Bot-detection flow distinguishes between "not logged in" and
  "cookies OK but JS challenge failed"
- `YTLogger.warning()` suppresses additional noisy yt-dlp messages:
  impersonation notices, XML parse errors, generic extractor fallback
- `WinError 10061` proxy-unreachable error now offers clear-and-retry
  in both `_get_yt_formats()` and `_download_yt()`
- Install menu restructured: ffmpeg / Windows Terminal / Fix YouTube

---

## [2.3.1] - 2026-04-10

### Fixed
- Proxy detection: add lowercase env var checks (https_proxy, http_proxy) for Linux/Mac
- Call `_apply_proxy()` after reading Windows registry proxy so env vars
  are set for the current session and config is persisted
- Wrap `_pick_output_folder()` + `_proxy_step()` in try/except in `main()`
- URL prompt already had protection; "Download another?" now also wrapped
- All exit paths consistently call `_bye()` instead of inline prints
- Remove duplicate `if again in ("", "y", "n")` block in "Download another?"
- Fix `_is_rss()` false positive: replace loose "rss"/"feed"/"channel"
  substring checks with tag-based "<rss" / "<feed" checks to avoid
  misidentifying regular HTML pages as RSS feeds
- Remove `_parse_v2ray_link()` (unused)
- Remove duplicate `_has_ffmpeg()` definition
- Remove duplicate `print_section()` definition

---

## [2.3.0] - 2026-04-10

### Added
- `_show_yt_info()` — video info panel (title, channel, duration, views) before quality picker
- `retry_with_backoff()` — exponential backoff (5s → 300s) with graceful Ctrl+C
- `YTLogger` — suppresses noisy yt-dlp warnings, surfaces real errors
- `_diagnose_error()` + `ERROR_HINTS` — human-readable hints for 15+ error types
- `_warn_no_ffmpeg()` panel with install instructions
- `_progress_ctx` + `yt_hook` replacing the old `Hook` class
- `make_progress()` reusable progress bar factory

### Changed
- Quality menu now lists all available formats:
  combined (video+audio), Video HD (per resolution), Audio Only (up to 4), Auto rows
- `_yt_quality_menu()` returns `(fmt, is_audio)` tuple
- `_download_yt()` accepts `is_audio` param, uses `YTLogger`, `yt_hook`, `retry_with_backoff`

### Fixed
- importlib: use `from importlib.util import find_spec` (Python 3.8+ safe)
- Proxy env vars: now checks both UPPERCASE and lowercase variants
- Registry proxy: was read but `_apply_proxy()` was never called → fixed
- Removed duplicate `_has_ffmpeg()` definition

---

## [2.2.0] - 2026-04-09

### Added
- Download settings menu (`s` at URL prompt) — configure max retries and fragment thread count at runtime
- Smart error diagnosis — human-readable explanations and fix hints for common errors
  (ffmpeg missing, private video, geo-block, age-restriction, etc.)
- `_FATAL_ERRORS` list in retry logic — permanent errors now fail immediately
  instead of retrying forever
- Warning suppression for noisy yt-dlp messages (JS runtime warning, DASH container notice)
- "Continue downloading?" prompt after each completed download
- Output folder suggestion with default path (`~/Downloads/SmartDL`) shown before prompt
- Author credit (`by Hellch!ef`) displayed in CLI header

### Changed
- ASCII art header with hacker-style box added to source file
- `retry_with_backoff` now distinguishes fatal vs. network errors

### Fixed
- Raw audio formats (m4a, opus) were incorrectly blocked by the ffmpeg check —
  now only MP3 conversion and video merge require ffmpeg
- ffmpeg check now also applies to `bestvideo+bestaudio` merge formats, not just MP3
- Progress bar was rendering twice after download completion — fixed by moving
  success message outside the Rich `Progress` context
- Proxy menu prompt showed empty `()` — replaced with `(Enter / p)` for clarity

---

## [2.1.0] - 2026-04-09

### Added
- ffmpeg presence check before attempting MP3 or merge downloads
- `_has_ffmpeg()` helper using `shutil.which`
- Warning panel when ffmpeg is missing with install instructions
- Auto-install ffmpeg via winget on Windows (with user confirmation)
- Proxy persistence across sessions — saved to config.json
- DRM error message with clear explanation
- Proxy prompt validation (reject empty/invalid input)
- Windows registry proxy detection (winreg)

---

## [1.0.0] - 2026-04-09

### Added
- Initial release
