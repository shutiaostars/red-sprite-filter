# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows one-file executable.

Build from the ``work/`` directory (the build.bat script does this for you):

    pyinstaller windows/red_sprite_filter.spec --noconfirm

Result: dist/red-sprite-filter.exe  (single portable file, no install needed)
"""

from pathlib import Path

SPECPATH = Path(SPECPATH)            # directory containing this .spec (windows/)
ROOT = SPECPATH.resolve().parent     # work/
APP_PKG = ROOT / "red_sprite_app"
STATIC = APP_PKG / "static"
BIN_WIN = APP_PKG / "bin" / "windows"

def _collect_datas():
    """Data files to bundle. ffmpeg/ffprobe are bundled only if present, so a
    missing download does not abort the whole build (the .bat copies them next
    to the exe as a fallback, and the runtime also searches the exe directory)."""
    datas = [
        (str(STATIC), "red_sprite_app/static"),
        (str(ROOT / "red_sprite_filter.py"), "."),
    ]
    for exe in (BIN_WIN / "ffmpeg.exe", BIN_WIN / "ffprobe.exe"):
        if exe.exists():
            datas.append((str(exe), "."))
        else:
            print(f"WARNING: {exe} not found - ffmpeg will NOT be bundled.")
            print("         Run windows/get_ffmpeg.py first, or copy ffmpeg.exe/ffprobe.exe")
            print("         next to the built red-sprite-filter.exe before shipping.")
    return datas


a = Analysis(
    [str(ROOT / "run_desktop.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=_collect_datas(),
    hiddenimports=[
        "red_sprite_app",
        "red_sprite_app.backend",
        "red_sprite_app.models",
        "red_sprite_app.desktop",
        "red_sprite_filter",
        "webview",
        "tkinter",
        "tkinter.filedialog",
        "numpy",
        "PIL",
        "PIL._imaging",
        "PIL._imagingft",
        "PIL._imagingcms",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "torch", "scipy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="red-sprite-filter",
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
