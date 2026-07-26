from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "tools" / "macos_runtime.lock.json"
DEFAULT_CACHE = ROOT / ".cache" / "macos-runtime"
NOTICES = ROOT / "tools" / "THIRD_PARTY_NOTICES.md"


def load_lock(path: Path = LOCK_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str, component: str) -> None:
    actual = file_sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"{component}: SHA-256 mismatch for {path.name}; "
            f"expected {expected}, got {actual}"
        )


def fetch_artifact(component: str, spec: dict[str, str], cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / spec["filename"]
    if destination.exists():
        try:
            verify_sha256(destination, spec["sha256"], component)
            return destination
        except RuntimeError:
            destination.unlink()

    for attempt in range(1, 4):
        with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            request = urllib.request.Request(
                spec["url"],
                headers={
                    "Accept-Encoding": "identity",
                    "User-Agent": "red-sprite-filter-macos-builder/1.0.6",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                with temporary.open("wb") as output:
                    shutil.copyfileobj(response, output)
            verify_sha256(temporary, spec["sha256"], component)
            os.replace(temporary, destination)
            return destination
        except (OSError, RuntimeError) as error:
            if attempt == 3:
                raise RuntimeError(
                    f"{component}: download failed verification after 3 attempts"
                ) from error
        finally:
            temporary.unlink(missing_ok=True)

    raise AssertionError("unreachable")


def extract_python(archive: Path, destination: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        unpacked = Path(td)
        shutil.unpack_archive(archive, unpacked)
        source = unpacked / "python"
        if not (source / "bin" / "python3").exists():
            raise RuntimeError("python: archive did not contain python/bin/python3")
        shutil.copytree(source, destination)


def extract_zip_member(archive: Path, member: str, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        matches = [name for name in bundle.namelist() if Path(name).name == member]
        if len(matches) != 1:
            raise RuntimeError(f"{member}: expected one executable in archive, got {matches}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with bundle.open(matches[0]) as source, destination.open("wb") as output:
            shutil.copyfileobj(source, output)
    destination.chmod(
        destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def install_wheels(python: Path, wheels: list[Path]) -> None:
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            *map(str, wheels),
        ],
        check=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1"},
    )


def copy_license(source: Path, destination: Path) -> None:
    if not source.exists():
        raise RuntimeError(f"Missing license file: {source}")
    shutil.copy2(source, destination)


def remove_python_caches(runtime: Path) -> None:
    for path in sorted(runtime.rglob("__pycache__"), reverse=True):
        shutil.rmtree(path)
    for path in runtime.rglob("*.pyc"):
        path.unlink()


def vendor_runtime(resources: Path, cache_dir: Path = DEFAULT_CACHE) -> None:
    lock = load_lock()
    specs = lock["artifacts"]
    artifacts = {
        name: fetch_artifact(name, spec, cache_dir)
        for name, spec in specs.items()
    }

    runtime = resources / "runtime" / "python"
    tools = resources / "bin"
    licenses = resources / "licenses"
    for path in (runtime, tools, licenses):
        if path.exists():
            shutil.rmtree(path)

    extract_python(artifacts["python"], runtime)
    python = runtime / "bin" / "python3"
    install_wheels(python, [artifacts["numpy"], artifacts["pillow"]])
    extract_zip_member(artifacts["ffmpeg"], "ffmpeg", tools / "ffmpeg")
    extract_zip_member(artifacts["ffprobe"], "ffprobe", tools / "ffprobe")

    site_packages = runtime / "lib" / "python3.12" / "site-packages"
    licenses.mkdir(parents=True)
    copy_license(NOTICES, licenses / "THIRD_PARTY_NOTICES.md")
    copy_license(
        runtime / "lib" / "python3.12" / "LICENSE.txt",
        licenses / "CPython-LICENSE.txt",
    )
    copy_license(
        artifacts["ffmpeg_license"],
        licenses / "FFmpeg-COPYING.GPLv3.txt",
    )
    copy_license(
        site_packages / "numpy-1.26.4.dist-info" / "LICENSE.txt",
        licenses / "NumPy-LICENSE.txt",
    )
    pillow_license = (
        site_packages / "pillow-11.3.0.dist-info" / "licenses" / "LICENSE"
    )
    copy_license(pillow_license, licenses / "Pillow-LICENSE.txt")
    remove_python_caches(runtime)
