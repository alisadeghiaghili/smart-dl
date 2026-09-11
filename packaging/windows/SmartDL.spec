# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SmartDL Windows onedir build.

onedir (not onefile) keeps SmartScreen/AV heuristics quieter and avoids
the temp-unpack pattern that single-file binaries trigger more often.

Build from the repository root:
    pyinstaller --noconfirm packaging/windows/SmartDL.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve().parent.parent  # noqa: F821 — SPECPATH provided by PyInstaller

block_cipher = None

hiddenimports = []
binaries = []
datas = []

for pkg in ("yt_dlp", "rich", "requests"):
    try:
        pkg_binaries, pkg_datas, pkg_hidden = collect_all(pkg)
        binaries += pkg_binaries
        datas += pkg_datas
        hiddenimports += pkg_hidden
    except Exception:
        hiddenimports += collect_submodules(pkg)

hiddenimports += [
    "smart_dl",
    "smart_dl.cli",
    "smart_dl.main",
    "smart_dl.core.config",
    "smart_dl.core.cookies",
    "smart_dl.core.cookies_file",
    "smart_dl.core.browser_cookies",
    "smart_dl.core.recorder",
    "smart_dl.core.proxy",
    "smart_dl.core.net_utils",
    "smart_dl.core.parallel",
    "smart_dl.core.manager",
    "smart_dl.core.paths",
    "smart_dl.core.retry",
    "smart_dl.core.downloader",
    "smart_dl.core.engine",
    "smart_dl.core.queue",
    "smart_dl.core.history",
    "smart_dl.core.sub_updates",
    "smart_dl.extractors.youtube",
    "smart_dl.extractors.aparat",
    "smart_dl.extractors.podcast",
    "smart_dl.extractors.general",
    "smart_dl.extractors.education",
    "smart_dl.extractors.education.common",
    "smart_dl.extractors.education.maktabkhooneh",
    "smart_dl.extractors.education.faradars",
    "smart_dl.extractors.education.coursera",
    "smart_dl.extractors.courses",
    "smart_dl.extractors.persian",
    "smart_dl.extractors.gallery",
    "smart_dl.extractors.castbox",
    "smart_dl.extractors.torrent",
    "smart_dl.extractors.faradars_next",
    "smart_dl.settings",
    "smart_dl.utils",
    "smart_dl.lang",
    "smart_dl.ui.progress",
    "smart_dl.ui.themes",
    "smart_dl.ui.logo",
]

a = Analysis(
    [str(ROOT / "packaging" / "windows" / "entry.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PySide2", "PySide6"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SmartDL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SmartDL",
)
