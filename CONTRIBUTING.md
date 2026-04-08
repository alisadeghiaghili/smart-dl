# Contributing

Contributions are welcome! Here’s how to get started.

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test manually with a few YouTube and podcast URLs
5. Commit with a clear message: `git commit -m "Add: your feature description"`
6. Push and open a Pull Request

## Guidelines

- Keep the zero-dependency philosophy — no new required packages unless absolutely necessary
- All user-facing messages should be in English (Rich markup is fine)
- Fatal errors must not be retried — add them to `_FATAL_ERRORS` if needed
- Test on both stable and unstable network conditions if possible
- Keep CLI output clean — suppress noisy warnings, surface actionable ones

## Reporting Issues

Please include:
- The URL you were trying to download (or a similar public URL)
- The error message shown
- Your OS and Python version
- Whether ffmpeg is installed

## Feature Ideas

- Playlist progress tracking
- Download history / deduplication
- Scheduled downloads
- Subtitle download option
- Config file support (save proxy, output dir, settings)
