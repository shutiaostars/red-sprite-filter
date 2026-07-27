import plistlib
import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.macos_runtime_probe import run_runtime_probe


ROOT = Path(__file__).resolve().parents[1]
DMG = ROOT / "outputs" / "红色精灵筛选器.dmg"
RELEASE_DMG = ROOT / "outputs" / "red-sprite-filter-1.0.6.dmg"
GITHUB_PUBLISH = ROOT
NOTES = ROOT / "outputs" / "GITHUB_RELEASE_NOTES.md"


class ReleasePackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_release_dmg.py")], check=True)

    def test_dmg_is_created_for_github_release(self):
        self.assertTrue(DMG.exists())
        self.assertGreater(DMG.stat().st_size, 50000)
        subprocess.run(["hdiutil", "imageinfo", str(DMG)], check=True, stdout=subprocess.DEVNULL)

    def test_release_notes_explain_unsigned_distribution(self):
        text = NOTES.read_text(encoding="utf-8")

        self.assertIn("GitHub Releases", text)
        self.assertIn("未签名", text)
        self.assertIn("Apple Developer ID", text)
        self.assertIn("控制台窗口", text)
        self.assertIn("无需安装 Homebrew", text)
        self.assertIn("CPython 3.12.13", text)
        self.assertIn("FFmpeg 8.1.2", text)
        self.assertNotIn("brew install ffmpeg", text)

    def test_app_inside_bundle_uses_native_executable(self):
        plist_path = ROOT / "outputs" / "红色精灵筛选器.app" / "Contents" / "Info.plist"
        with plist_path.open("rb") as handle:
            plist = plistlib.load(handle)

        self.assertEqual(plist["CFBundleExecutable"], "red-sprite-filter")

    def test_github_publish_hashes_match_current_release_dmg(self):
        digest = hashlib.sha256(RELEASE_DMG.read_bytes()).hexdigest()

        checksums = (GITHUB_PUBLISH / "CHECKSUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertIn(f"{digest}  {RELEASE_DMG.name}", checksums)
        for path in GITHUB_PUBLISH.glob("RELEASE_v1.0.6*.md"):
            self.assertIn(digest, path.read_text(encoding="utf-8"), str(path))

    def test_mounted_dmg_uses_self_contained_runtime(self):
        attach = subprocess.run(
            ["hdiutil", "attach", "-readonly", "-nobrowse", "-plist", str(DMG)],
            check=True,
            stdout=subprocess.PIPE,
        )
        payload = plistlib.loads(attach.stdout)
        mount_point = next(
            Path(entity["mount-point"])
            for entity in payload["system-entities"]
            if "mount-point" in entity
        )
        self.addCleanup(
            subprocess.run,
            ["hdiutil", "detach", str(mount_point)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        app = mount_point / "红色精灵筛选器.app"
        resources = app / "Contents" / "Resources"
        with tempfile.TemporaryDirectory() as td:
            result = run_runtime_probe(resources, Path(td))
            self.assertGreater(result["duration"], 1.5)
            self.assertTrue(result["report"].exists())
            self.assertTrue(result["clips"], result)

        with tempfile.TemporaryDirectory() as launcher_home:
            launcher = subprocess.Popen(
                [str(app / "Contents" / "MacOS" / "red-sprite-filter")],
                env={"PATH": "/usr/bin:/bin", "HOME": launcher_home},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.time() + 20
                backend_command = ""
                backend_pid = None
                while time.time() < deadline and launcher.poll() is None:
                    children = subprocess.run(
                        ["pgrep", "-P", str(launcher.pid)],
                        check=False,
                        text=True,
                        stdout=subprocess.PIPE,
                    ).stdout.split()
                    for pid in children:
                        command = subprocess.run(
                            ["ps", "-o", "command=", "-p", pid],
                            check=True,
                            text=True,
                            stdout=subprocess.PIPE,
                        ).stdout
                        if "red_sprite_app.backend" in command:
                            backend_command = command
                            backend_pid = int(pid)
                            break
                    if backend_command:
                        break
                    time.sleep(0.25)
                self.assertIn("runtime/python/bin/python3", backend_command)
                self.assertIn("red_sprite_app.backend", backend_command)
            finally:
                launcher.terminate()
                try:
                    launcher.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    launcher.kill()
                    launcher.wait(timeout=5)
                if backend_pid:
                    try:
                        os.kill(backend_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    else:
                        for _ in range(50):
                            try:
                                os.kill(backend_pid, 0)
                            except ProcessLookupError:
                                break
                            time.sleep(0.1)
                        else:
                            os.kill(backend_pid, signal.SIGKILL)
                if launcher.stderr:
                    launcher.stderr.close()


if __name__ == "__main__":
    unittest.main()
