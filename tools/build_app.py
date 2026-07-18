from __future__ import annotations

import plistlib
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "work" if (ROOT / "work").exists() else ROOT / "src"
OUTPUTS = ROOT / "outputs"
APP = OUTPUTS / "红色精灵筛选器.app"
CONTENTS = APP / "Contents"
MACOS = CONTENTS / "MacOS"
RESOURCES = CONTENTS / "Resources"
APP_RESOURCES = RESOURCES / "app"
PYTHON_LIB = RESOURCES / "python_lib"
EXECUTABLE = "red-sprite-filter"
ICON_SOURCE = SOURCE_ROOT / "red_sprite_app" / "assets" / "AppIcon-source.png"
ICON_OUTPUT = RESOURCES / "AppIcon.icns"
SYSTEM_PYTHON = Path("/usr/bin/python3")
VENDORED_PYTHON_REQUIREMENTS = ["numpy==1.26.4", "Pillow>=10.0,<12.0"]
VERSION = "1.0.1"


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def write_plist() -> None:
    payload = {
        "CFBundleName": "红色精灵筛选器",
        "CFBundleDisplayName": "红色精灵筛选器",
        "CFBundleIdentifier": "local.red-sprite-filter",
        "CFBundleVersion": VERSION,
        "CFBundleShortVersionString": VERSION,
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": EXECUTABLE,
        "CFBundleIconFile": "AppIcon",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    }
    with (CONTENTS / "Info.plist").open("wb") as handle:
        plistlib.dump(payload, handle)


def write_icon() -> None:
    if not ICON_SOURCE.exists():
        raise RuntimeError(f"Missing icon source: {ICON_SOURCE}")

    sizes = [
        ("icon_16x16.png", 16),
        ("icon_16x16@2x.png", 32),
        ("icon_32x32.png", 32),
        ("icon_32x32@2x.png", 64),
        ("icon_128x128.png", 128),
        ("icon_128x128@2x.png", 256),
        ("icon_256x256.png", 256),
        ("icon_256x256@2x.png", 512),
        ("icon_512x512.png", 512),
        ("icon_512x512@2x.png", 1024),
    ]
    with tempfile.TemporaryDirectory() as td:
        iconset = Path(td) / "AppIcon.iconset"
        iconset.mkdir()
        for name, size in sizes:
            out = iconset / name
            subprocess.run(["sips", "-z", str(size), str(size), str(ICON_SOURCE), "--out", str(out)], check=True)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(ICON_OUTPUT)], check=True)


def vendor_python_dependencies() -> None:
    if not SYSTEM_PYTHON.exists():
        raise RuntimeError(f"Missing macOS system Python: {SYSTEM_PYTHON}")
    if PYTHON_LIB.exists():
        shutil.rmtree(PYTHON_LIB)
    PYTHON_LIB.mkdir(parents=True)
    subprocess.run(
        [
            str(SYSTEM_PYTHON),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--ignore-installed",
            "--no-deps",
            "--upgrade",
            "--target",
            str(PYTHON_LIB),
            *VENDORED_PYTHON_REQUIREMENTS,
        ],
        check=True,
    )
    subprocess.run(
        [
            str(SYSTEM_PYTHON),
            "-c",
            "import numpy, PIL; print(numpy.__version__)",
        ],
        check=True,
        env={"PYTHONPATH": str(PYTHON_LIB)},
    )
    for cache_dir in PYTHON_LIB.rglob("__pycache__"):
        shutil.rmtree(cache_dir)
    for cache_file in PYTHON_LIB.rglob("*.pyc"):
        cache_file.unlink()


def strip_extended_attributes(path: Path) -> None:
    subprocess.run(["xattr", "-cr", str(path)], check=True)


def sign_app() -> None:
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(APP)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(APP)], check=True)


def build() -> Path:
    if APP.exists():
        shutil.rmtree(APP)
    MACOS.mkdir(parents=True)
    APP_RESOURCES.mkdir(parents=True)
    write_plist()
    write_icon()
    vendor_python_dependencies()

    copytree(SOURCE_ROOT / "red_sprite_app", APP_RESOURCES / "red_sprite_app")
    shutil.copy2(SOURCE_ROOT / "red_sprite_filter.py", APP_RESOURCES / "red_sprite_filter.py")
    executable = MACOS / EXECUTABLE
    subprocess.run(
        [
            "swiftc",
            str(SOURCE_ROOT / "red_sprite_app" / "native" / "RedSpriteFilterApp.swift"),
            "-framework",
            "Cocoa",
            "-framework",
            "WebKit",
            "-o",
            str(executable),
        ],
        check=True,
    )
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    required = [
        CONTENTS / "Info.plist",
        executable,
        ICON_OUTPUT,
        PYTHON_LIB / "numpy",
        PYTHON_LIB / "PIL",
        APP_RESOURCES / "red_sprite_app" / "backend.py",
        APP_RESOURCES / "red_sprite_app" / "static" / "index.html",
        APP_RESOURCES / "red_sprite_filter.py",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Missing app bundle files: " + ", ".join(str(path) for path in missing))
    strip_extended_attributes(APP)
    sign_app()
    return APP


if __name__ == "__main__":
    print(build())
