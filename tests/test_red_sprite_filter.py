import tempfile
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "work" if (ROOT / "work").exists() else ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

import red_sprite_filter as rsf


class RedSpriteFilterTests(unittest.TestCase):
    def test_score_frame_rates_red_sprite_region_above_neutral_and_white_flash(self):
        neutral = np.zeros((80, 120, 3), dtype=np.uint8)
        red = neutral.copy()
        red[8:30, 50:56] = [180, 28, 85]
        white = neutral.copy()
        white[8:30, 50:56] = [255, 255, 255]

        neutral_score = rsf.score_frame(neutral, rsf.DetectionConfig())
        red_score = rsf.score_frame(red, rsf.DetectionConfig())
        white_score = rsf.score_frame(white, rsf.DetectionConfig())

        self.assertGreater(red_score.score, neutral_score.score)
        self.assertGreater(red_score.red_pixels, 0)
        self.assertEqual(white_score.red_pixels, 0)

    def test_score_frame_detects_faint_magenta_vertical_sprite_column(self):
        neutral = np.full((80, 120, 3), [42, 38, 58], dtype=np.uint8)
        sprite = neutral.copy()
        sprite[12:46, 61:64] = [108, 62, 118]

        neutral_score = rsf.score_frame(neutral, rsf.DetectionConfig())
        sprite_score = rsf.score_frame(sprite, rsf.DetectionConfig())

        self.assertGreater(sprite_score.score, neutral_score.score + 0.2)
        self.assertGreater(sprite_score.red_pixels, 0)

    def test_score_temporal_frame_rewards_new_faint_vertical_column(self):
        previous = np.full((80, 120, 3), [42, 38, 58], dtype=np.uint8)
        current = previous.copy()
        current[12:46, 61:64] = [96, 58, 118]

        temporal_score = rsf.score_temporal_frame(current, previous, rsf.DetectionConfig())

        self.assertGreater(temporal_score.score, 0.2)
        self.assertGreater(temporal_score.red_pixels, 0)

    def test_rank_indices_by_positive_similarity_prefers_matching_feature_vector(self):
        vectors = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.9, 0.1, 0.0]),
            np.array([0.0, 1.0, 0.0]),
        ]

        ranked = rsf.rank_indices_by_positive_similarity(vectors, [0])

        self.assertEqual(ranked[:2], [0, 1])

    def test_literature_sprite_score_prefers_upper_local_vertical_red_structure(self):
        sky = np.full((100, 160, 3), [42, 38, 58], dtype=np.uint8)
        sprite = sky.copy()
        sprite[28:50, 35:42] = [150, 55, 95]
        sprite[48:66, 37:39] = [120, 45, 110]
        city_flash = sky.copy()
        city_flash[84:96, 20:145] = [180, 90, 95]

        sprite_score = rsf.literature_sprite_score(sprite, rsf.DetectionConfig())
        city_score = rsf.literature_sprite_score(city_flash, rsf.DetectionConfig())

        self.assertGreater(sprite_score.score, 1.0)
        self.assertGreater(sprite_score.score, city_score.score * 3)

    def test_literature_sprite_score_penalizes_broad_horizon_glow(self):
        sky = np.full((100, 160, 3), [42, 38, 58], dtype=np.uint8)
        local_sprite = sky.copy()
        local_sprite[30:48, 28:40] = [150, 55, 95]
        broad_glow = sky.copy()
        broad_glow[68:83, 0:150] = [145, 58, 95]

        local_score = rsf.literature_sprite_score(local_sprite, rsf.DetectionConfig())
        broad_score = rsf.literature_sprite_score(broad_glow, rsf.DetectionConfig())

        self.assertGreater(local_score.score, broad_score.score * 2)

    def test_precision_sprite_score_rejects_horizon_glow_and_keeps_upper_sprite(self):
        sky = np.full((120, 180, 3), [42, 38, 58], dtype=np.uint8)
        sprite = sky.copy()
        sprite[32:54, 38:48] = [158, 48, 96]
        sprite[52:72, 42:45] = [128, 42, 105]
        horizon_glow = sky.copy()
        horizon_glow[88:104, 0:170] = [165, 68, 95]

        sprite_score = rsf.precision_sprite_score(sprite, None, rsf.DetectionConfig())
        glow_score = rsf.precision_sprite_score(horizon_glow, None, rsf.DetectionConfig())

        self.assertGreater(sprite_score.score, 2.0)
        self.assertEqual(glow_score.red_pixels, 0)
        self.assertGreater(sprite_score.score, glow_score.score * 5)

    def test_pick_events_clusters_adjacent_peaks_and_keeps_best_frame(self):
        scores = [
            rsf.FrameScore(0, 0.00, 0.0, 0, 0.0),
            rsf.FrameScore(1, 0.10, 5.0, 20, 100.0),
            rsf.FrameScore(2, 0.18, 8.0, 25, 150.0),
            rsf.FrameScore(8, 1.10, 6.0, 22, 120.0),
        ]

        events = rsf.pick_events(
            scores,
            max_events=10,
            cluster_seconds=0.25,
            min_score=1.0,
            percentile=50,
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].frame_index, 2)
        self.assertEqual(events[1].frame_index, 8)

    def test_pick_events_limits_to_highest_scoring_clusters(self):
        scores = [
            rsf.FrameScore(1, 0.10, 2.0, 20, 80.0),
            rsf.FrameScore(8, 1.10, 9.0, 22, 180.0),
            rsf.FrameScore(16, 2.10, 5.0, 21, 120.0),
        ]

        events = rsf.pick_events(
            scores,
            max_events=2,
            cluster_seconds=0.25,
            min_score=1.0,
            percentile=0,
        )

        self.assertEqual([event.frame_index for event in events], [8, 16])

    def test_compute_clip_window_clamps_to_video_duration(self):
        self.assertEqual(rsf.compute_clip_window(0.4, 1.0, 2.0, 10.0), (0.0, 2.4))
        self.assertEqual(rsf.compute_clip_window(9.5, 1.0, 2.0, 10.0), (8.5, 10.0))

    def test_discover_videos_recurses_and_ignores_unsupported_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.MOV").write_text("video")
            (root / "notes.txt").write_text("ignore")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.mp4").write_text("video")

            found = rsf.discover_videos([str(root)])

        self.assertEqual([p.name for p in found], ["a.MOV", "b.mp4"])

    def test_generate_html_report_contains_image_and_clip_references(self):
        event = rsf.CandidateEvent(
            video=Path("/videos/storm.mov"),
            event_rank=1,
            frame_index=12,
            timestamp=3.5,
            score=9.0,
            red_pixels=30,
            red_strength=400.0,
            clip_start=2.5,
            clip_end=5.5,
            image_path=Path("storm/01.jpg"),
            clip_path=Path("storm/01.mp4"),
        )

        html = rsf.render_html_report([event], {"scan_width": 640}, Path("/tmp/out"))

        self.assertIn("storm.mov", html)
        self.assertIn("storm/01.jpg", html)
        self.assertIn("storm/01.mp4", html)
        self.assertIn("3.500s", html)

    def test_parse_args_includes_clip_padding_options(self):
        args = rsf.parse_args(
            [
                "video.mov",
                "--pre-seconds",
                "1.5",
                "--post-seconds",
                "3",
                "--clip-format",
                "mov",
            ]
        )

        self.assertEqual(args.inputs, ["video.mov"])
        self.assertEqual(args.pre_seconds, 1.5)
        self.assertEqual(args.post_seconds, 3.0)
        self.assertEqual(args.clip_format, "mov")
        self.assertEqual(args.score_mode, "precision")

    def test_write_run_metadata_outputs_settings_json(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)

            rsf.write_run_metadata(out, {"score_mode": "precision", "max_candidates": 24})

            settings = out / "settings.json"
            self.assertTrue(settings.exists())
            self.assertIn('"score_mode": "precision"', settings.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
