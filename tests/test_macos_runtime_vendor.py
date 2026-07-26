import hashlib
import json
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


if __name__ == "__main__":
    unittest.main()
