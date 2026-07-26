from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "tools" / "macos_runtime.lock.json"
DEFAULT_CACHE = ROOT / ".cache" / "macos-runtime"


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

    with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        request = urllib.request.Request(
            spec["url"],
            headers={"User-Agent": "red-sprite-filter-macos-builder/1.0.6"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        verify_sha256(temporary, spec["sha256"], component)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
