# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows desktop executable.

Build from the repository root on Windows:

    pyinstaller windows/red_sprite_filter.spec --noconfirm --clean

Result:

    dist/red-sprite-filter.exe
"""

from pathlib import Path


SPECPATH = Path(SPECPATH)
ROOT = SPECPATH.resolve().parent
SRC = ROOT / "src"
APP_PKG = SRC / "red_sprite_app"
STATIC = APP_PKG / "static"
BIN_WIN = APP_PKG / "bin" / "windows"


def _collect_datas():
    datas = [
        (str(STATIC), "red_sprite_app/static"),
        (str(SRC / "red_sprite_filter.py"), "."),
    ]
    for exe in (BIN_WIN / "ffmpeg.exe", BIN_WIN / "ffprobe.exe"):
        if exe.exists():
            datas.append((str(exe), "."))
        else:
            print(f"WARNING: {exe} not found - ffmpeg will not be bundled.")
    return datas


a = Analysis(
    [str(SRC / "run_desktop.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=_collect_datas(),
    hiddenimports=[
        "red_sprite_app",
        "red_sprite_app.backend",
        "red_sprite_app.desktop",
        "red_sprite_app.models",
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
