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


if __name__ == "__main__":
    unittest.main()
