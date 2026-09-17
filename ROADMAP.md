# SmartDL Roadmap

Prioritized gaps vs common downloaders (IDM, JDownloader, 4K Video Downloader, Motrix).
Each item is designed for TDD and a weekly-sized PR.

## Done (recent)

| ID | Feature | Status |
|----|---------|--------|
| R1 | Netscape `cookies.txt` import | Done — `--cookies-file` + config |
| R2 | Auto-update yt-dlp | Done — `--update-ytdlp` / `SMARTDL_UPDATE_YTDLP=1` |
| R3 | Speed limit | Done — `--limit-rate` → yt-dlp `ratelimit` |
| R4 | Clipboard grabber | Done — `--watch-clipboard` |
| R5 | Download scheduler | Done — `--schedule` / `--at` |
| R6 | Channel auto-download | Partial — `--subs-check`, per-sub `auto_download`, `SMARTDL_SUBS_AUTODL=1` |
| R7 | Telegram notify | Done — config token/chat + `record_download` hook |
| R8 | Config import/export | Done — `--export-config` / `--import-config` (secrets scrubbed) |
| C-Auth | Cookie browser defaults | Done — `--set-cookie-browser` + diagnose |
| R12 | Full FA i18n coverage | Partial — interactive keys complete; CLI still mixed |

## Execution plan (ordered PRs)

Rule: **one human-week max per PR**. Every PR ships tests + docs + no AI co-author trail.
Definition of Done (DoD) for every feature PR:

1. Unit tests for pure logic (parsing, state, config keys)
2. Integration/smoke path that can run offline (mock network)
3. CLI flag or menu path documented in README + CHANGELOG
4. `mypy` + `ruff` + `pytest` green in CI
5. Honest capability matrix row if user-facing behavior is partial

---

### Wave 1 — week 1–2 (highest competitive value)

| Order | ID | PR title (prefix) | Scope (in) | Scope (out) | DoD |
|-------|----|-------------------|------------|-------------|-----|
| 1 | **R2** | `feat: opt-in yt-dlp auto-update` | `--update-ytdlp`, env `SMARTDL_UPDATE_YTDLP=1`, `commands/ytdlp_update.py`, version print before/after | Auto-update on every start without flag; network on import | Tests with fake installer callable; README; CHANGELOG |
| 2 | **C-Auth** | `feat: cookie auth defaults` | First-run/`--cookies` helper; `--set-cookie-browser`; README cookies.txt matrix; diagnose already works | Chrome/Edge decrypt workarounds | `set_cookie_browser` + wiring tests; docs for Firefox + cookies.txt |
| 3 | **R8** | `feat: config import-export` | `--export-config path.json`, `--import-config path.json`; whitelist keys (proxy, cookie_browser, cookies_file, smart_mode, lang, theme, limit defaults); **never export secrets** | Exporting cookie values / tokens | Round-trip tests; refuse unknown keys |

**Wave 1 exit:** user can update yt-dlp, set Firefox cookies, move portable config between machines.

---

### Wave 2 — week 3–4 (automation; beats feature-list noise)

| Order | ID | PR title | Scope (in) | Scope (out) | DoD |
|-------|----|----------|------------|-------------|-----|
| 4 | **R4** | `feat: clipboard link grabber` | `smart-dl --watch-clipboard`; optional extra `pyperclip`; queue URLs on change; `--watch-interval`; dedupe vs queue; stop on Ctrl+C | Browser extension; global hotkeys | Pure `is_grabbable_url` tests; mock clipboard poller; README |
| 5 | **R7** | `feat: telegram notify on download complete` | config keys `telegram_bot_token`, `telegram_chat_id`; fire on `record_download` success/failure when enabled; `--notify-test` | Multi-chat; HTML templates; rate-limit server | Unit test HTTP client with fake `post`; token never logged |

**Wave 2 exit:** passive grab + phone notify — differentiated for Iranian users.

---

### Wave 3 — week 5–6 (ops)

| Order | ID | PR title | Scope (in) | Scope (out) | DoD |
|-------|----|----------|------------|-------------|-----|
| 6 | **R5** | `feat: download scheduler` | SQLite `schedule` table (`id`, `url`, `run_at`, `status`); `--schedule add URL --at 02:30`; `--schedule start` loop; `--schedule list/clear`; reuse queue processor | OS service installer; cron UI | Time injectable clock; process_due tests offline |
| 7 | **R6-finish** | `feat: subscription daemon helpers` | `smart-dl subs check --once`; document Windows Task Scheduler snippet; honor `auto_download` | Built-in always-on daemon | Doc + smoke |

**Wave 3 exit:** night downloads + unattended channel follow.

---

### Wave 4 — week 7–9 (platform surface)

| Order | ID | PR title | Scope (in) | Scope (out) | DoD |
|-------|----|----------|------------|-------------|-----|
| 8 | **R12-finish** | `i18n: complete fa/cli sweep` | Sweep `cli.py`/`commands/*` strings into `lang`; keys parity test EN↔FA | Machine translation polish of README_fa | Test: key set equality |
| 9 | **R11** | `feat: optional aria2 rpc` | If `aria2.rpc` URL in config, send URIs to aria2 JSON-RPC; fallback yt-dlp | Full Motrix UI; multi-protocol file types | RPC client unit test with fake transport |
| 10 | **R10** | `feat: local control api` | stdlib `http.server` (no FastAPI dep) on `127.0.0.1:8765`; `POST /queue`, `GET /history`, `GET /health`; token from config; **bind localhost only** | AuthZ multi-user; TLS | Handler tests via `urllib`; security note in README |

**Wave 4 exit:** remote/mobile control path R9 can talk to.

---

### Wave 5 — week 10+ (optional / separate repo)

| Order | ID | PR title | Scope |
|-------|----|----------|-------|
| 11 | **R9** | separate repo `smartdl-firefox-extension` | MV3 extension; POST URL to `R10` API; no cookie scraping in extension |
| 12 | **Quality debt** | `test: integration download fixtures` | Offline HTML/RSS fixtures for education/podcast/castbox; raise coverage floor 35→50 |
| 13 | **Web UI** | decision PR | Either deprecate `web.py` in README **or** one PR to wire it to `commands` + tests. Do not leave 0% orphan module claimed as product. |

---

## Dependency graph

```text
R2 ──────────────┐
C-Auth ──────────┼──► R4 (clipboard → queue) ──► R7 (notify after record_download)
R8 (portable cfg)┘         │
                           ▼
                    R5 scheduler / R6 daemon
                           │
                           ▼
                 R10 HTTP API ──► R9 extension
                           │
                    R11 aria2 RPC (independent, can parallel)
R12 i18n (independent, anytime after Wave 1)
```

## Effort estimates (Ali focused, not calendar wall-clock)

| PR | Design | Code+tests | Docs | Risk |
|----|--------|------------|------|------|
| R2 | 0.5d | 1d | 0.5d | Low |
| C-Auth | 0.5d | 1d | 1d | Low |
| R8 | 0.5d | 1d | 0.5d | Medium (secret scrub) |
| R4 | 1d | 2d | 0.5d | Medium (clipboard OS) |
| R7 | 0.5d | 1d | 0.5d | Low |
| R5 | 1d | 2d | 0.5d | Medium (clock/loop) |
| R12 | 1d | 2d | 0.5d | Low |
| R11 | 1d | 1.5d | 0.5d | Medium |
| R10 | 1d | 2d | 1d | Medium (security) |
| R9 | 2d | 3d+ | 1d | High (new repo) |

## Explicit non-goals (still)

- DRM circumvention (Spotify/Netflix/Coursera protected streams)
- Bulk piracy of paid courses without user credentials
- Code-signed “trusted” EXE claims without a real cert

## First implementation slice (recommended start)

1. **R2 yt-dlp auto-update** (smallest, high ROI)
2. **C-Auth cookie defaults + docs**
3. **R8 config export/import**

Then stop and re-measure: does `--check-updates` + grabber actually get used?

## License rationale

**Apache-2.0** — permissive, explicit patent grant, easy for other tools to embed; pairs well with Unlicense yt-dlp without forcing copyleft on wrappers.
