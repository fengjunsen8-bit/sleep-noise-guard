# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd()

a = Analysis(
    ["sleep_noise_guard/windows_desktop.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ("sounds", "sounds"),
        ("README.md", "."),
        ("docs/中文说明.md", "docs"),
    ],
    hiddenimports=["numpy", "sounddevice"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="睡眠噪音守卫",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
