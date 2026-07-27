from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]

PAPER_URLS = [
    "https://doi.org/10.1029/95GL00583",
    "https://doi.org/10.1029/95GL03587",
    "https://doi.org/10.1029/95GL02827",
    "https://doi.org/10.1038/416152a",
    "https://doi.org/10.1016/S1364-6826(02)00323-1",
    "https://doi.org/10.1007/s10712-013-9224-4",
]

OFFICIAL_URLS = [
    "https://www.nssl.noaa.gov/education/svrwx101/lightning/types/",
    "https://science.nasa.gov/citizen-science/spritacular/",
    "https://svs.gsfc.nasa.gov/11059",
    "https://svs.gsfc.nasa.gov/31111/",
]


class ReadmeReferenceTests(unittest.TestCase):
    def test_chinese_readme_embeds_ui_screenshots_and_release_test_results(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        screenshots = [
            "docs/images/ui-overview.png",
            "docs/images/candidate-review.png",
        ]

        self.assertIn("## 界面、功能与实测成果", readme)
        self.assertIn("63 项全部通过", readme)
        self.assertIn("不等同于算法的 precision / recall", readme)
        self.assertIn("快速连续事件仍可能被相邻帧聚类合并", readme)
        self.assertNotIn("连续出现的红色精灵不再只保留最强一组", readme)
        for relative_path in screenshots:
            with self.subTest(relative_path=relative_path):
                self.assertIn(f"]({relative_path})", readme)
                image = ROOT / relative_path
                self.assertTrue(image.exists())
                self.assertGreater(image.stat().st_size, 100_000)

    def test_chinese_readme_documents_scientific_basis_and_references(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## 科学判断依据与参考文献", readme)
        self.assertIn("规则型候选筛选工具", readme)
        for url in PAPER_URLS + OFFICIAL_URLS:
            self.assertIn(url, readme)

    def test_english_readme_documents_scientific_basis_and_references(self):
        readme = (ROOT / "README.en.md").read_text(encoding="utf-8")

        self.assertIn("## Scientific basis and references", readme)
        self.assertIn("rule-based candidate screening tool", readme)
        for url in PAPER_URLS + OFFICIAL_URLS:
            self.assertIn(url, readme)


class ReadmeRoadmapTests(unittest.TestCase):
    def test_localized_readmes_separate_completed_work_from_next_steps(self):
        expectations = {
            "README.md": ("## 已完成的近期改进", "## 下一步计划", "Windows 安装包已内置"),
            "README.en.md": ("## Recently completed", "## Next steps", "The Windows installer now bundles"),
            "README.ja.md": ("## 最近完了した改善", "## 次の予定", "Windows インストーラーには"),
            "README.es.md": ("## Mejoras completadas recientemente", "## Próximos pasos", "El instalador de Windows ya incluye"),
            "README.de.md": ("## Kürzlich abgeschlossen", "## Nächste Schritte", "Der Windows-Installer enthält jetzt"),
        }

        for filename, required_text in expectations.items():
            readme = (ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                for text in required_text:
                    self.assertIn(text, readme)

    def test_roadmap_no_longer_lists_cross_platform_ffmpeg_bundling_as_unfinished(self):
        obsolete_lines = {
            "README.md": "- 内置 ffmpeg，进一步降低安装门槛",
            "README.en.md": "- Bundle ffmpeg to lower the setup barrier",
            "README.ja.md": "- ffmpeg を内蔵し、導入のハードルを下げる",
            "README.es.md": "- Incluir ffmpeg para reducir la barrera de instalación",
            "README.de.md": "- ffmpeg einbetten, um die Einstiegshürde zu senken",
        }

        for filename, obsolete_line in obsolete_lines.items():
            readme = (ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                self.assertNotIn(obsolete_line, readme)

    def test_localized_readmes_describe_self_contained_macos_package(self):
        expectations = {
            "README.md": ("macOS 安装包已内置", "无需安装 Homebrew"),
            "README.en.md": ("The macOS package bundles", "Homebrew is not required"),
            "README.ja.md": ("macOS パッケージには", "Homebrew は不要"),
            "README.es.md": ("El paquete de macOS incluye", "Homebrew no es necesario"),
            "README.de.md": ("Das macOS-Paket enthält", "Homebrew ist nicht erforderlich"),
        }
        for filename, fragments in expectations.items():
            readme = (ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                for fragment in fragments:
                    self.assertIn(fragment, readme)


if __name__ == "__main__":
    unittest.main()
