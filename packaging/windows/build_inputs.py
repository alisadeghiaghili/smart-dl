"""Shared PyInstaller inputs for the SmartDL Windows builds.

Both the onedir (``SmartDL.spec``) and onefile (``SmartDL-onefile.spec``)
specs need the same collected binaries, data files, and hidden imports.
Keeping them here prevents the two from drifting apart.

The onefile build additionally bundles the vendor/ tree (ffmpeg, node, aria2)
when ``include_vendor=True`` is passed to :func:`build_inputs`.
"""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(__file__).resolve().parent.parent.parent

_hiddenimports: list[str] = []
_binaries: list = []
_datas: list = []

for _pkg in ("yt_dlp", "rich", "requests"):
    try:
        _pkg_binaries, _pkg_datas, _pkg_hidden = collect_all(_pkg)
        _binaries += _pkg_binaries
        _datas += _pkg_datas
        _hiddenimports += _pkg_hidden
    except Exception:
        _hiddenimports += collect_submodules(_pkg)

# Pull every smart_dl submodule so lazy imports in CLI/queue do not break frozen EXE.
try:
    _hiddenimports += collect_submodules("smart_dl")
except Exception:
    _hiddenimports += [
        "smart_dl",
        "smart_dl.__main__",
        "smart_dl.cli",
        "smart_dl.main",
        "smart_dl.settings",
        "smart_dl.utils",
        "smart_dl.web",
        "smart_dl.lang",
        "smart_dl.core",
        "smart_dl.core.browser_cookies",
        "smart_dl.core.config",
        "smart_dl.core.cookie_diag",
        "smart_dl.core.cookies",
        "smart_dl.core.cookies_file",
        "smart_dl.core.downloader",
        "smart_dl.core.engine",
        "smart_dl.core.history",
        "smart_dl.core.installer",
        "smart_dl.core.logging",
        "smart_dl.core.manager",
        "smart_dl.core.net_utils",
        "smart_dl.core.network",
        "smart_dl.core.packaging_utils",
        "smart_dl.core.parallel",
        "smart_dl.core.paths",
        "smart_dl.core.portable",
        "smart_dl.core.proxy",
        "smart_dl.core.queue",
        "smart_dl.core.recorder",
        "smart_dl.core.retry",
        "smart_dl.core.sub_updates",
        "smart_dl.core.subscriptions",
        "smart_dl.extractors",
        "smart_dl.extractors.registry",
        "smart_dl.extractors.dispatch",
        "smart_dl.extractors.aparat",
        "smart_dl.extractors.castbox",
        "smart_dl.extractors.courses",
        "smart_dl.extractors.faradars_next",
        "smart_dl.extractors.gallery",
        "smart_dl.extractors.general",
        "smart_dl.extractors.persian",
        "smart_dl.extractors.podcast",
        "smart_dl.extractors.podcast_meta",
        "smart_dl.extractors.subtitles",
        "smart_dl.extractors.torrent",
        "smart_dl.extractors.youtube",
        "smart_dl.extractors.education",
        "smart_dl.extractors.education.common",
        "smart_dl.extractors.education.coursera",
        "smart_dl.extractors.education.faradars",
        "smart_dl.extractors.education.maktabkhooneh",
        "smart_dl.ui",
        "smart_dl.ui.logo",
        "smart_dl.ui.progress",
        "smart_dl.ui.themes",
    ]

# Deduplicate while preserving order.
_seen = set()
_HIDDENIMPORTS: list[str] = []
for _name in _hiddenimports:
    if _name not in _seen:
        _seen.add(_name)
        _HIDDENIMPORTS.append(_name)


def build_inputs(include_vendor: bool = False) -> dict:
    """Return the Analysis kwargs shared by every SmartDL spec.

    Parameters
    ----------
    include_vendor : bool, optional
        When ``True``, also bundle everything under ``vendor/`` (ffmpeg,
        node, aria2) as PyInstaller data so a frozen app finds them on its
        runtime PATH. Only the fully-self-contained onefile build passes
        ``True``; the onedir build keeps the lighter footprint.

    Returns
    -------
    dict
        ``pathex``, ``binaries``, ``datas``, ``hiddenimports``, ``excludes``
        ready to unpack into ``Analysis(...)``.
    """
    datas = list(_datas)
    if include_vendor:
        vendor = ROOT / "packaging" / "windows" / "vendor"
        if vendor.is_dir():
            datas.append((str(vendor), "vendor"))
            print(f"[build_inputs] bundling vendor tools from {vendor}")
        else:
            print(
                f"[build_inputs] WARNING: {vendor} missing — "
                "run fetch_vendor.py for a fully-embedded build."
            )
    return {
        "pathex": [str(ROOT)],
        "binaries": _binaries,
        "datas": datas,
        "hiddenimports": _HIDDENIMPORTS,
        "excludes": ["tkinter", "PyQt5", "PySide2", "PySide6"],
    }


if __name__ == "__main__":
    _inp = build_inputs()
    print(f"hiddenimports: {len(_inp['hiddenimports'])}")
    print(f"binaries:      {len(_inp['binaries'])}")
    print(f"datas:         {len(_inp['datas'])}")
