# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SmartDL Windows onedir build.

onedir (not onefile) keeps SmartScreen/AV heuristics quieter and avoids
the temp-unpack pattern that single-file binaries trigger more often.

Build from the repository root:
    pyinstaller --noconfirm packaging/windows/SmartDL.spec
"""

import sys
from pathlib import Path

# Make the spec's own directory importable so we can share build inputs with
# the onefile spec without a package __init__.py. SPECPATH is already the
# spec's own directory (where build_inputs.py lives).
_SPEC_DIR = str(Path(SPECPATH).resolve())  # noqa: F821 — PyInstaller-provided
if _SPEC_DIR not in sys.path:
    sys.path.insert(0, _SPEC_DIR)

import build_inputs  # noqa: E402

ROOT = build_inputs.ROOT
inputs = build_inputs.build_inputs()

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
