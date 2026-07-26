from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_runtime_probe(resources: Path, root: Path) -> dict[str, object]:
    python = resources / "runtime" / "python" / "bin" / "python3"
    ffmpeg = resources / "bin" / "ffmpeg"
    ffprobe = resources / "bin" / "ffprobe"
    app = resources / "app"
    video = root / "synthetic.mov"
    output = root / "results"
    home = root / "home"
    temp = root / "tmp"
    home.mkdir()
    temp.mkdir()
    env = {
        "PATH": f"{resources / 'bin'}:/usr/bin:/bin",
        "PYTHONPATH": str(app),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "HOME": str(home),
        "TMPDIR": str(temp),
    }

    health = subprocess.run(
        [
            str(python),
            "-c",
            "import json; from red_sprite_app.backend import check_dependencies; "
            "print(json.dumps(check_dependencies()))",
        ],
        check=True,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
    )
    payload = json.loads(health.stdout)
    if not payload["ok"]:
        raise AssertionError(payload)

    subprocess.run(
        [
            str(ffmpeg),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x180:r=10:d=2",
            "-vf",
            "drawbox=x=154:y=18:w=12:h=90:color=0xd02050:t=fill:"
            "enable='between(t,0.8,1.0)'",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
        env=env,
    )
    probe = subprocess.run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(video),
        ],
        check=True,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
    )
    subprocess.run(
        [
            str(python),
            str(app / "red_sprite_filter.py"),
            str(video),
            "--out",
            str(output),
            "--scan-width",
            "320",
            "--sample-fps",
            "10",
            "--max-candidates",
            "4",
            "--min-score",
            "0.001",
            "--min-red-pixels",
            "1",
        ],
        check=True,
        env=env,
    )
    required = [
        output / "settings.json",
        output / "candidates.csv",
        output / "report.html",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise AssertionError(f"Missing output files: {missing}")
    clips = list(output.glob("**/*.mp4")) + list(output.glob("**/*.mov"))
    if not clips:
        raise AssertionError(f"No event clips in {output}")
    return {
        "duration": float(probe.stdout),
        "report": output / "report.html",
        "clips": clips,
        "health": payload,
    }
