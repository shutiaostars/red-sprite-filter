"""Download Windows ffmpeg/ffprobe binaries for the packaged app."""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path


FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    "latest/ffmpeg-master-latest-win64-gpl.zip"
)
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "src" / "red_sprite_app" / "bin" / "windows"
NEEDED = {"ffmpeg.exe", "ffprobe.exe"}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Windows ffmpeg from:\n  {FFMPEG_ZIP_URL}")
    req = urllib.request.Request(FFMPEG_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        data = urllib.request.urlopen(req, timeout=180).read()
    except Exception as exc:
        print(f"ERROR: download failed: {exc}", file=sys.stderr)
        return 1

    extracted = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            base = name.rsplit("/", 1)[-1]
            if base in NEEDED:
                target = DEST / base
                target.write_bytes(zf.read(name))
                print(f"  -> {target}")
                extracted += 1

    if extracted != len(NEEDED):
        print("ERROR: archive did not contain both ffmpeg.exe and ffprobe.exe", file=sys.stderr)
        return 1

    print(f"Done. Binaries are in: {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
