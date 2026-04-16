# Changelog

All notable changes to SmartDL are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
- **Proxy detection**: lowercase env vars (`https_proxy`, `http_proxy`) now
  checked for Linux/Mac compatibility; Windows registry proxy now correctly
  calls `_apply_proxy()` to persist config and set env vars for the session
- **Keyboard interrupt / EOFError**: `_pick_output_folder()` and `_proxy_step()`
  wrapped in `try/except` in `main()`; "Download another?" prompt now also
  protected — all exit paths consistently call `_bye()`
- **RSS false positive**: `_is_rss()` now uses tag-based `<rss`/`<feed` checks
  instead of loose substring matching that triggered on any page containing
  "channel" or "feed"
- **Duplicate code**: removed duplicate `_has_ffmpeg()` definition, duplicate
  `print_section()` definition, duplicate `if again in (…)` block, and unused
  `_parse_v2ray_link()` function

---

## [2.3.0] - 2026-04-10

### Added
- `_show_yt_info()` — video info panel (title, channel, duration, views) before quality picker
- `retry_with_backoff()` — exponential backoff (5s→300s), Ctrl+C aware, skips fatal errors
- `YTLogger` — suppresses noisy yt-dlp warnings, surfaces actionable errors only
- `_diagnose_error()` + `ERROR_HINTS` — human-readable hints for 15+ error types
- `_warn_no_ffmpeg()` — rich panel with install instructions
- `make_progress()` — reusable rich Progress bar factory
- `yt_hook` + `_progress_ctx` — replaces old `Hook` class

### Changed
- Quality menu now lists all available formats:
  combined (video+audio), Video HD (per resolution), Audio Only (up to 4), Auto rows
- `_yt_quality_menu()` returns `(fmt, is_audio)` tuple
- `_download_yt()` accepts `is_audio` param, uses `YTLogger`, `yt_hook`, `retry_with_backoff`

### Fixed
- `importlib.util.find_spec` import — compatible with Python 3.8–3.14
- Proxy env vars — now checks both `HTTPS_PROXY` (Windows) and `https_proxy` (Linux/Mac)
- Registry proxy — `_apply_proxy()` was not called after reading from registry
- Removed duplicate `_has_ffmpeg()` definition
- `WinError 10061` (proxy unreachable) — offer clear-and-retry instead of crash

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

## [1.0.0] - 2026-04-09

### Added
- Initial release
- YouTube video/audio download via yt-dlp
- Direct podcast URL download
- Auto-install missing Python dependencies on first run
- Output folder selection
