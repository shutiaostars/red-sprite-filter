from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WindowsPackagingTests(unittest.TestCase):
    def test_windows_build_files_exist(self):
        expected = [
            ROOT / "windows" / "get_ffmpeg.py",
            ROOT / "windows" / "red_sprite_filter.spec",
            ROOT / "windows" / "red_sprite_filter.iss",
            ROOT / "windows" / "build_windows.ps1",
            ROOT / ".github" / "workflows" / "build-windows.yml",
        ]

        for path in expected:
            self.assertTrue(path.exists(), str(path))

    def test_pyinstaller_spec_bundles_app_and_ffmpeg(self):
        spec = (ROOT / "windows" / "red_sprite_filter.spec").read_text(encoding="utf-8")

        self.assertIn("run_desktop.py", spec)
        self.assertIn("red_sprite_app/static", spec)
        self.assertIn("red_sprite_filter.py", spec)
        self.assertIn("ffmpeg.exe", spec)
        self.assertIn("ffprobe.exe", spec)
        self.assertIn('name="red-sprite-filter"', spec)

    def test_inno_setup_installer_creates_shortcuts_and_uninstall(self):
        script = (ROOT / "windows" / "red_sprite_filter.iss").read_text(encoding="utf-8")

        self.assertIn("AppName=Red Sprite Filter", script)
        self.assertIn("OutputBaseFilename=red-sprite-filter-setup", script)
        self.assertIn("{autoprograms}", script)
        self.assertIn("{autodesktop}", script)
        self.assertIn("red-sprite-filter.exe", script)
        self.assertNotIn("ChineseSimplified.isl", script)

    def test_github_actions_builds_windows_installer_artifact(self):
        workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")

        self.assertIn("windows-latest", workflow)
        self.assertIn("windows/build_windows.ps1", workflow)
        self.assertIn("red-sprite-filter-windows-installer", workflow)
        self.assertIn("red-sprite-filter-setup.exe", workflow)

    def test_readme_mentions_windows_installer_download(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")

        self.assertIn("Windows 安装包", readme)
        self.assertIn("red-sprite-filter-setup.exe", readme)
        self.assertIn("Windows installer", english)
        self.assertIn("red-sprite-filter-setup.exe", english)

    def test_pywebview_desktop_enters_event_loop(self):
        desktop = (ROOT / "src" / "red_sprite_app" / "desktop.py").read_text(encoding="utf-8")

        self.assertIn("webview.create_window", desktop)
        self.assertIn("webview.start(", desktop)
        self.assertNotIn("create_window blocks until all windows are closed", desktop)


if __name__ == "__main__":
    unittest.main()
