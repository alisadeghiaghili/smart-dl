# SmartDL Roadmap

Prioritized gaps vs common downloaders (IDM, JDownloader, 4K Video Downloader, Motrix).
Each item is designed for TDD and a weekly-sized PR.

## Done (recent)

| ID | Feature | Status |
|----|---------|--------|
| R1 | Netscape `cookies.txt` import | Done — `--cookies-file` + config |
| R6 | Channel auto-download (YouTube) | Partial — `sub_updates` + per-sub `auto_download` / `SMARTDL_SUBS_AUTODL=1` |
| R12 | Full FA i18n coverage | Partial — interactive keys complete; CLI/manager still mixed |

## P0 — high value / low–medium effort

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R2 | Auto-update yt-dlp on start (opt-in) | YouTube extractors break often | `SMARTDL_UPDATE_YTDLP=1` or `--update-ytdlp` |
| R3 | Speed limit | Fair use on shared networks | **Done** — `--limit-rate 2M` → yt-dlp `ratelimit` |
| R4 | Clipboard watcher (link grabber) | One of the top IDM/JDownloader features | Optional dependency; poll clipboard for URLs |

## P1 — solid product features

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R5 | Download scheduler | Night downloads on weak links | SQLite job table + `--schedule start` |
| R7 | Telegram notify on complete | Iranian users live on Telegram | Bot token + chat id in config |
| R8 | Import/export config | Move portable setups | JSON dump of config + settings |

## P2 — larger surface

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R9 | Browser extension (Firefox) | True one-click grab | Separate mini-repo; talks to local CLI/HTTP |
| R10 | Local HTTP control API | Automation / mobile companion | Tiny FastAPI/stdlib server |
| R11 | aria2 RPC mode | Motrix-class multi-protocol | Optional if aria2c present |

## Out of scope (explicit)

- DRM circumvention (Spotify full, Netflix, Coursera protected streams)
- Bulk piracy of paid courses without user credentials
- Signature-free “trusted” EXE claims

## License rationale

**Apache-2.0** — permissive, explicit patent grant, easy for other tools to embed; pairs well with Unlicense yt-dlp without forcing copyleft on wrappers.
