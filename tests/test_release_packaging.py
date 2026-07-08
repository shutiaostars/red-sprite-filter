import plistlib
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DMG = ROOT / "outputs" / "红色精灵筛选器.dmg"
RELEASE_DMG = ROOT / "outputs" / "red-sprite-filter-1.0.0.dmg"
GITHUB_PUBLISH = ROOT / "outputs" / "github_publish"
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

    def test_app_inside_bundle_uses_native_executable(self):
        plist_path = ROOT / "outputs" / "红色精灵筛选器.app" / "Contents" / "Info.plist"
        with plist_path.open("rb") as handle:
            plist = plistlib.load(handle)

        self.assertEqual(plist["CFBundleExecutable"], "red-sprite-filter")

    def test_github_publish_hashes_match_current_release_dmg(self):
        digest = hashlib.sha256(RELEASE_DMG.read_bytes()).hexdigest()

        self.assertEqual((GITHUB_PUBLISH / "CHECKSUMS.txt").read_text(encoding="utf-8"), f"{digest}  {RELEASE_DMG.name}\n")
        for path in GITHUB_PUBLISH.glob("RELEASE_v1.0.0*.md"):
            self.assertIn(digest, path.read_text(encoding="utf-8"), str(path))


if __name__ == "__main__":
    unittest.main()
