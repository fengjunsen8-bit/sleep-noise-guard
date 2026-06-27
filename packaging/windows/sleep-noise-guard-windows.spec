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
        ("docs/涓枃璇存槑.md", "docs"),
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
    name="鐫＄湢鍣煶瀹堝崼",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
