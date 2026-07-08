import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from red_sprite_app.backend import (
    build_choose_path_script,
    build_runtime_path,
    build_scan_command,
    check_dependencies,
)
from red_sprite_app.models import (
    CandidateReview,
    default_output_dir,
    export_confirmed_csv,
    load_candidates_csv,
    write_review_state,
)


class RedSpriteAppModelTests(unittest.TestCase):
    def test_default_output_dir_uses_parent_and_video_stem(self):
        video = Path("/Users/heyi/Desktop/摄影/摄影作品/红色精灵/测试/DSC_0490.MOV")

        self.assertEqual(
            default_output_dir(video),
            Path("/Users/heyi/Desktop/摄影/摄影作品/红色精灵/测试/DSC_0490_红色精灵筛选结果"),
        )

    def test_load_candidates_csv_returns_relative_media_urls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            frame = root / "DSC_0490" / "candidate_001.jpg"
            clip = root / "DSC_0490" / "candidate_001.mp4"
            frame.parent.mkdir()
            frame.write_bytes(b"jpg")
            clip.write_bytes(b"mp4")
            csv_path = root / "candidates.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "video",
                        "event_rank",
                        "frame_index",
                        "timestamp_seconds",
                        "score",
                        "red_pixels",
                        "red_strength",
                        "clip_start_seconds",
                        "clip_end_seconds",
                        "image_path",
                        "clip_path",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "video": "/tmp/DSC_0490.MOV",
                        "event_rank": "1",
                        "frame_index": "123",
                        "timestamp_seconds": "15.349",
                        "score": "9.25",
                        "red_pixels": "48",
                        "red_strength": "1200.0",
                        "clip_start_seconds": "14.349",
                        "clip_end_seconds": "17.349",
                        "image_path": str(frame),
                        "clip_path": str(clip),
                    }
                )

            candidates = load_candidates_csv(csv_path)

            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].timestamp_seconds, 15.349)
            self.assertEqual(candidates[0].state, "unreviewed")
            self.assertEqual(candidates[0].image_relpath, "DSC_0490/candidate_001.jpg")
            self.assertEqual(candidates[0].clip_relpath, "DSC_0490/candidate_001.mp4")

    def test_review_state_and_confirmed_csv_export(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review = [
                CandidateReview(candidate_id="DSC_0490.MOV:1:15.349", state="confirmed"),
                CandidateReview(candidate_id="DSC_0490.MOV:2:22.000", state="false_positive"),
            ]

            review_path = write_review_state(root, review)
            confirmed_path = export_confirmed_csv(root, review)

            payload = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["reviews"][0]["state"], "confirmed")
            self.assertTrue(confirmed_path.exists())
            self.assertIn("DSC_0490.MOV:1:15.349", confirmed_path.read_text(encoding="utf-8"))


class RedSpriteBackendTests(unittest.TestCase):
    def test_build_scan_command_uses_precision_defaults(self):
        command = build_scan_command(
            source=Path("/tmp/DSC_0490.MOV"),
            output=Path("/tmp/out"),
            mode="precision",
            max_candidates=12,
            min_score=0.8,
            min_red_pixels=8,
            pre_seconds=1.0,
            post_seconds=2.0,
        )

        self.assertEqual(command[0], sys.executable)
        self.assertIn("/tmp/DSC_0490.MOV", command)
        self.assertIn("--score-mode", command)
        self.assertIn("precision", command)
        self.assertIn("--max-candidates", command)
        self.assertIn("12", command)
        self.assertIn("--min-score", command)
        self.assertIn("0.8", command)

    def test_dependency_check_reports_required_names(self):
        health = check_dependencies()
        names = {item["name"] for item in health["dependencies"]}

        self.assertIn("python", names)
        self.assertIn("ffmpeg", names)
        self.assertIn("ffprobe", names)
        self.assertIn("numpy", names)
        self.assertIn("Pillow", names)

    def test_runtime_path_includes_common_homebrew_locations(self):
        runtime_path = build_runtime_path("/custom/bin:/usr/bin")
        parts = runtime_path.split(":")

        self.assertIn("/opt/homebrew/bin", parts)
        self.assertIn("/usr/local/bin", parts)
        self.assertIn("/custom/bin", parts)
        self.assertLess(parts.index("/opt/homebrew/bin"), parts.index("/custom/bin"))
        self.assertEqual(len(parts), len(set(parts)))

    def test_choose_path_scripts_use_macos_file_and_folder_dialogs(self):
        video_script = build_choose_path_script("video")
        source_folder_script = build_choose_path_script("source-folder")
        output_folder_script = build_choose_path_script("output-folder")

        self.assertIn("choose file", video_script)
        self.assertIn("选择视频文件", video_script)
        self.assertIn("POSIX path", video_script)
        self.assertIn("choose folder", source_folder_script)
        self.assertIn("选择素材文件夹", source_folder_script)
        self.assertIn("choose folder", output_folder_script)
        self.assertIn("选择输出目录", output_folder_script)


class RedSpriteStaticUiTests(unittest.TestCase):
    def test_mode_buttons_use_chinese_labels_but_keep_internal_ids(self):
        html = Path("red_sprite_app/static/index.html").read_text(encoding="utf-8")
        script = Path("red_sprite_app/static/app.js").read_text(encoding="utf-8")

        self.assertIn('id="precisionMode"', html)
        self.assertIn('id="recallMode"', html)
        self.assertIn(">精准筛选<", html)
        self.assertIn(">高召回筛选<", html)
        self.assertNotIn(">Precision<", html)
        self.assertNotIn(">Recall<", html)
        self.assertIn('mode: "precision"', script)
        self.assertIn('setMode("recall")', script)

    def test_ui_has_native_path_picker_buttons(self):
        html = Path("red_sprite_app/static/index.html").read_text(encoding="utf-8")
        script = Path("red_sprite_app/static/app.js").read_text(encoding="utf-8")

        self.assertIn('id="chooseVideo"', html)
        self.assertIn(">选择视频<", html)
        self.assertIn('id="chooseSourceFolder"', html)
        self.assertIn(">选择文件夹<", html)
        self.assertIn('id="chooseOutputFolder"', html)
        self.assertIn(">选择输出目录<", html)
        self.assertIn('choosePath("video", "sourcePath")', script)
        self.assertIn('choosePath("source-folder", "sourcePath")', script)
        self.assertIn('choosePath("output-folder", "outputPath")', script)

    def test_stylesheet_uses_cyan_instrument_palette(self):
        css = Path("red_sprite_app/static/styles.css").read_text(encoding="utf-8")

        self.assertIn("--bg: #02060b;", css)
        self.assertIn("--cyan: #00e5ff;", css)
        self.assertIn("--instrument: #78f7ff;", css)
        self.assertIn("--sprite: #ff3f6e;", css)
        self.assertNotIn("radial-gradient(circle at 60% 0%", css)


if __name__ == "__main__":
    unittest.main()
