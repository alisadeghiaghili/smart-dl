# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SmartDL Windows onefile build.

onefile bundles the runtime, yt-dlp, and all app data into a single
``SmartDL.exe`` — convenient to drop into a folder or share, at the cost of
a slower first start (PyInstaller unpacks to a temp dir each run) and a
larger footprint on AV/SmartScreen heuristics. The onedir build remains the
default release asset; this is an additional, self-contained option.

Build from the repository root:
    pyinstaller --noconfirm packaging/windows/SmartDL-onefile.spec
"""

import sys
from pathlib import Path

# See SmartDL.spec — share the collected inputs so both builds stay in sync.
# SPECPATH is already the spec's own directory (where build_inputs.py lives).
_SPEC_DIR = str(Path(SPECPATH).resolve())  # noqa: F821 — PyInstaller-provided
if _SPEC_DIR not in sys.path:
    sys.path.insert(0, _SPEC_DIR)

import build_inputs  # noqa: E402

ROOT = build_inputs.ROOT
# include_vendor=True bundles ffmpeg/node/aria2 from vendor/ (see fetch_vendor.py)
# so this exe is fully self-contained. The onedir spec does not pass this.
inputs = build_inputs.build_inputs(include_vendor=True)

block_cipher = None

a = Analysis(
    [str(ROOT / "packaging" / "windows" / "entry.py")],
    **inputs,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# exclude_binaries=False folds everything (binaries, zipfiles, data) into the
# single EXE. No COLLECT step follows — that is what makes it one file.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=False,
    name="SmartDL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
