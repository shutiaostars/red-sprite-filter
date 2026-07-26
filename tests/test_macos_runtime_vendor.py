import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import vendor_macos_runtime as vendor


class MacOSRuntimeVendorTests(unittest.TestCase):
    def test_runtime_lock_pins_all_artifacts(self):
        lock = json.loads((TOOLS / "macos_runtime.lock.json").read_text(encoding="utf-8"))

        self.assertEqual(lock["platform"], "macos-arm64")
        self.assertEqual(lock["minimum_macos"], "12.0")
        self.assertEqual(
            set(lock["artifacts"]),
            {"python", "numpy", "pillow", "ffmpeg", "ffprobe", "ffmpeg_license"},
        )
        for name, spec in lock["artifacts"].items():
            with self.subTest(name=name):
                self.assertTrue(spec["url"].startswith("https://"))
                self.assertRegex(spec["sha256"], r"^[0-9a-f]{64}$")
                self.assertNotIn("latest", spec["url"])

    def test_runtime_download_cache_is_ignored(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".cache/macos-runtime/", gitignore)

    def test_verify_sha256_rejects_corrupt_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "artifact.bin"
            artifact.write_bytes(b"corrupt")

            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                vendor.verify_sha256(artifact, "0" * 64, "python")

    def test_verify_sha256_accepts_matching_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "artifact.bin"
            artifact.write_bytes(b"valid")
            digest = hashlib.sha256(b"valid").hexdigest()

            vendor.verify_sha256(artifact, digest, "python")

    def test_vendor_runtime_creates_complete_resource_layout(self):
        with tempfile.TemporaryDirectory() as td:
            resources = Path(td) / "Resources"
            vendor.vendor_runtime(resources)

            expected = [
                resources / "runtime" / "python" / "bin" / "python3",
                resources / "runtime" / "python" / "lib" / "python3.12" / "site-packages" / "numpy",
                resources / "runtime" / "python" / "lib" / "python3.12" / "site-packages" / "PIL",
                resources / "bin" / "ffmpeg",
                resources / "bin" / "ffprobe",
                resources / "licenses" / "THIRD_PARTY_NOTICES.md",
                resources / "licenses" / "CPython-LICENSE.txt",
                resources / "licenses" / "FFmpeg-COPYING.GPLv3.txt",
                resources / "licenses" / "NumPy-LICENSE.txt",
                resources / "licenses" / "Pillow-LICENSE.txt",
            ]
            for path in expected:
                with self.subTest(path=path):
                    self.assertTrue(path.exists(), str(path))

            self.assertTrue(os.access(resources / "bin" / "ffmpeg", os.X_OK))
            self.assertTrue(os.access(resources / "bin" / "ffprobe", os.X_OK))


if __name__ == "__main__":
    unittest.main()
