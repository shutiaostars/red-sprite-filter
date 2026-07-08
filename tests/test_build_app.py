import plistlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "work" if (ROOT / "work").exists() else ROOT / "src"
APP = ROOT / "outputs" / "红色精灵筛选器.app"


class RedSpriteBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "tools" / "build_app.py")], check=True)

    def test_app_bundle_structure_exists(self):
        self.assertTrue((APP / "Contents" / "Info.plist").exists())
        self.assertTrue((APP / "Contents" / "MacOS" / "red-sprite-filter").exists())
        self.assertTrue((APP / "Contents" / "Resources" / "AppIcon.icns").exists())
        self.assertTrue((APP / "Contents" / "Resources" / "app" / "red_sprite_app" / "backend.py").exists())
        self.assertTrue((APP / "Contents" / "Resources" / "app" / "red_sprite_filter.py").exists())

    def test_info_plist_has_expected_bundle_keys(self):
        with (APP / "Contents" / "Info.plist").open("rb") as handle:
            plist = plistlib.load(handle)

        self.assertEqual(plist["CFBundleName"], "红色精灵筛选器")
        self.assertEqual(plist["CFBundleExecutable"], "red-sprite-filter")
        self.assertEqual(plist["CFBundleIdentifier"], "local.red-sprite-filter")
        self.assertEqual(plist["CFBundleIconFile"], "AppIcon")

    def test_native_webview_executable_exists(self):
        executable = APP / "Contents" / "MacOS" / "red-sprite-filter"
        self.assertTrue(executable.stat().st_mode & 0o111)
        self.assertGreater(executable.stat().st_size, 10000)

    def test_app_bundle_signature_is_valid_after_resources_are_added(self):
        result = subprocess.run(
            ["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(APP)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("code has no resources", result.stdout)

    def test_app_bundle_does_not_ship_python_cache_files(self):
        caches = list(APP.rglob("__pycache__")) + list(APP.rglob("*.pyc"))

        self.assertEqual(caches, [])

    def test_app_icon_is_non_empty_icns(self):
        icon = APP / "Contents" / "Resources" / "AppIcon.icns"

        self.assertGreater(icon.stat().st_size, 10000)

    def test_native_webview_source_starts_backend_without_browser(self):
        source = SOURCE_ROOT / "red_sprite_app" / "native" / "RedSpriteFilterApp.swift"
        text = source.read_text(encoding="utf-8")

        self.assertIn("WKWebView", text)
        self.assertIn("Process()", text)
        self.assertIn('environment["PATH"]', text)
        self.assertIn("/opt/homebrew/bin", text)
        self.assertIn("--port", text)
        self.assertIn('"0"', text)
        self.assertNotIn("--open", text)
        self.assertIn("terminate()", text)

    def test_release_dmg_script_exists(self):
        script = ROOT / "tools" / "build_release_dmg.py"
        text = script.read_text(encoding="utf-8")

        self.assertIn("hdiutil", text)
        self.assertIn("红色精灵筛选器.dmg", text)


if __name__ == "__main__":
    unittest.main()
