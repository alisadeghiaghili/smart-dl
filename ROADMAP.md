# SmartDL Roadmap

Prioritized gaps vs common downloaders (IDM, JDownloader, 4K Video Downloader, Motrix).
Each item is designed for TDD and a weekly-sized PR.

## P0 — high value / low–medium effort

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R1 | Netscape `cookies.txt` import | Works when browser cookie extract fails (Chrome encryption) | `--cookies-file path` + config |
| R2 | Auto-update yt-dlp on start (opt-in) | YouTube extractors break often | `SMARTDL_UPDATE_YTDLP=1` or `--update-ytdlp` |
| R3 | Speed limit | Fair use on shared networks | `--limit-rate 2M` → yt-dlp `ratelimit` |
| R4 | Clipboard watcher (link grabber) | One of the top IDM/JDownloader features | Optional dependency; poll clipboard for URLs |

## P1 — solid product features

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R5 | Download scheduler | Night downloads on weak links | SQLite job table + `--schedule start` |
| R6 | Channel auto-download (YouTube) | Subscriptions half-done today | Reuse `sub_updates` + yt-dlp flat extract |
| R7 | Telegram notify on complete | Iranian users live on Telegram | Bot token + chat id in config |
| R8 | Import/export config | Move portable setups | JSON dump of config + settings |

## P2 — larger surface

| ID | Feature | Why | Notes |
|----|---------|-----|-------|
| R9 | Browser extension (Firefox) | True one-click grab | Separate mini-repo; talks to local CLI/HTTP |
| R10 | Local HTTP control API | Automation / mobile companion | Tiny FastAPI/stdlib server |
| R11 | aria2 RPC mode | Motrix-class multi-protocol | Optional if aria2c present |
| R12 | Full FA i18n coverage | 100% Persian UI | Sweep remaining hardcoded strings |

## Out of scope (explicit)

- DRM circumvention (Spotify full, Netflix, Coursera protected streams)
- Bulk piracy of paid courses without user credentials
- Signature-free “trusted” EXE claims

## License rationale

**Apache-2.0** — permissive, explicit patent grant, easy for other tools to embed; pairs well with Unlicense yt-dlp without forcing copyleft on wrappers.
