import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "work" if (ROOT / "work").exists() else ROOT / "src"
APP = ROOT / "outputs" / "红色精灵筛选器.app"
RESOURCES = APP / "Contents" / "Resources"
BUNDLED_PYTHON = RESOURCES / "runtime" / "python" / "bin" / "python3"
BUNDLED_FFMPEG = RESOURCES / "bin" / "ffmpeg"
BUNDLED_FFPROBE = RESOURCES / "bin" / "ffprobe"


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
        self.assertTrue(BUNDLED_PYTHON.exists())
        self.assertTrue(BUNDLED_FFMPEG.exists())
        self.assertTrue(BUNDLED_FFPROBE.exists())
        self.assertTrue((RESOURCES / "runtime" / "python" / "lib" / "python3.12" / "site-packages" / "numpy").exists())
        self.assertTrue((RESOURCES / "runtime" / "python" / "lib" / "python3.12" / "site-packages" / "PIL").exists())

    def test_info_plist_has_expected_bundle_keys(self):
        with (APP / "Contents" / "Info.plist").open("rb") as handle:
            plist = plistlib.load(handle)

        self.assertEqual(plist["CFBundleName"], "红色精灵筛选器")
        self.assertEqual(plist["CFBundleExecutable"], "red-sprite-filter")
        self.assertEqual(plist["CFBundleIdentifier"], "local.red-sprite-filter")
        self.assertEqual(plist["CFBundleIconFile"], "AppIcon")
        self.assertEqual(plist["CFBundleShortVersionString"], "1.0.6")

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
        self.assertIn('appendingPathComponent("runtime/python/bin/python3")', text)
        self.assertIn('appendingPathComponent("bin")', text)
        self.assertIn('environment["PYTHONPATH"]', text)
        self.assertIn('environment["PATH"]', text)
        self.assertIn('environment["PYTHONDONTWRITEBYTECODE"]', text)
        self.assertNotIn("/usr/bin/python3", text)
        self.assertNotIn("/opt/homebrew", text)
        self.assertNotIn("/usr/local", text)
        self.assertIn("--port", text)
        self.assertIn('"0"', text)
        self.assertNotIn("--open", text)
        self.assertIn("terminate()", text)

    def test_bundled_dependencies_import_with_bundled_python(self):
        app_root = RESOURCES / "app"
        result = subprocess.run(
            [
                str(BUNDLED_PYTHON),
                "-c",
                "import numpy, PIL; print(numpy.__version__); print(PIL.__version__)",
            ],
            env={
                "PATH": f"{RESOURCES / 'bin'}:/usr/bin:/bin",
                "PYTHONPATH": str(app_root),
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "HOME": tempfile.mkdtemp(),
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1.26.4", result.stdout)
        self.assertIn("11.3.0", result.stdout)

    def test_bundled_numpy_wheel_supports_macos_12_release_target(self):
        site_packages = RESOURCES / "runtime" / "python" / "lib" / "python3.12" / "site-packages"
        wheel_files = list(site_packages.glob("numpy-*.dist-info/WHEEL"))
        self.assertTrue(wheel_files)
        wheel_text = wheel_files[0].read_text(encoding="utf-8")

        self.assertIn("macosx_11_0_arm64", wheel_text)
        self.assertNotIn("macosx_14_0_arm64", wheel_text)

    def test_release_dmg_script_exists(self):
        script = ROOT / "tools" / "build_release_dmg.py"
        text = script.read_text(encoding="utf-8")

        self.assertIn("hdiutil", text)
        self.assertIn("红色精灵筛选器.dmg", text)


if __name__ == "__main__":
    unittest.main()
