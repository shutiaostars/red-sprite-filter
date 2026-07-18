#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import glob
import html
import json
import math
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mts", ".m2ts", ".mkv", ".avi"}
PROGRESS_PREFIX = "PROGRESS_JSON "


@dataclass(frozen=True)
class DetectionConfig:
    roi_top_fraction: float = 0.78
    roi_y_start_fraction: float = 0.0
    min_red: float = 42.0
    min_red_excess: float = 10.0
    green_blue_suppression: float = 1.02
    red_green_ratio: float = 1.18
    red_blue_ratio: float = 0.92
    max_brightness: float = 245.0
    pixel_weight: float = 6.0
    vertical_bonus_weight: float = 0.16


@dataclass(frozen=True)
class FrameScore:
    frame_index: int
    timestamp: float
    score: float
    red_pixels: int
    red_strength: float


@dataclass(frozen=True)
class CandidateEvent:
    video: Path
    event_rank: int
    frame_index: int
    timestamp: float
    score: float
    red_pixels: int
    red_strength: float
    clip_start: float
    clip_end: float
    image_path: Path
    clip_path: Path


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    duration: float


class ProgressReporter:
    def __init__(
        self,
        enabled: bool,
        total_work_frames: int,
        stream=None,
        clock=None,
        min_interval: float = 0.5,
    ) -> None:
        self.enabled = enabled
        self.total_work_frames = max(1, int(total_work_frames))
        self.stream = stream or sys.stdout
        self.clock = clock or time.monotonic
        self.min_interval = min_interval
        self.started_at = float(self.clock())
        self.last_emit_at = self.started_at

    def emit(
        self,
        *,
        current_video: Path | str,
        video_index: int,
        total_videos: int,
        processed_frames: int,
        total_frames: int,
        completed_work_frames: int,
        force: bool = False,
    ) -> None:
        if not self.enabled:
            return

        now = float(self.clock())
        if not force and now - self.last_emit_at < self.min_interval:
            return
        self.last_emit_at = now

        total_frames = max(1, int(total_frames))
        processed_frames = max(0, min(int(processed_frames), total_frames))
        total_processed = max(0, min(self.total_work_frames, int(completed_work_frames) + processed_frames))
        progress_percent = round((total_processed / self.total_work_frames) * 100.0, 2)
        elapsed_seconds = max(0.0, now - self.started_at)
        eta_seconds = None
        if total_processed > 0 and elapsed_seconds > 0:
            frames_per_second = total_processed / elapsed_seconds
            eta_seconds = max(0.0, (self.total_work_frames - total_processed) / frames_per_second)

        video_name = Path(current_video).name if str(current_video) else ""
        payload = {
            "progress_percent": progress_percent,
            "elapsed_seconds": round(elapsed_seconds, 6),
            "eta_seconds": round(eta_seconds, 6) if eta_seconds is not None else None,
            "current_video": video_name,
            "video_index": int(video_index),
            "total_videos": int(total_videos),
            "processed_frames": processed_frames,
            "total_frames": total_frames,
        }
        print(PROGRESS_PREFIX + json.dumps(payload, ensure_ascii=False), file=self.stream, flush=True)


def estimated_scan_frames(info: VideoInfo, sample_fps: float) -> int:
    effective_fps = sample_fps if sample_fps > 0 else info.fps
    if effective_fps <= 0 or info.duration <= 0:
        return 1
    return max(1, int(math.ceil(info.duration * effective_fps)))


def safe_stem(path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", path.stem).strip("_") or "video"


def discover_videos(inputs: list[str]) -> list[Path]:
    videos: list[Path] = []
    for raw_input in inputs:
        path = Path(raw_input).expanduser()
        if path.is_dir():
            videos.extend(
                child
                for child in sorted(path.rglob("*"))
                if child.is_file() and child.suffix.lower() in VIDEO_EXTENSIONS
            )
        elif path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(path)
        elif glob.has_magic(str(path)):
            videos.extend(
                child
                for child in sorted(Path(match) for match in glob.glob(str(path), recursive=True))
                if child.is_file() and child.suffix.lower() in VIDEO_EXTENSIONS
            )

    unique: list[Path] = []
    seen: set[Path] = set()
    for video in videos:
        resolved = video.resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def score_frame(frame: np.ndarray, config: DetectionConfig) -> FrameScore:
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must be an RGB array with shape (height, width, 3)")

    height = frame.shape[0]
    start_y = max(0, min(height, int(height * config.roi_y_start_fraction)))
    end_y = max(start_y + 1, min(height, int(height * config.roi_top_fraction)))
    roi = frame[start_y:end_y].astype(np.float32)

    red = roi[:, :, 0]
    green = roi[:, :, 1]
    blue = roi[:, :, 2]
    max_green_blue = np.maximum(green, blue)
    brightness = np.maximum.reduce([red, green, blue])
    red_excess = red - (config.green_blue_suppression * max_green_blue)

    red_like = (
        (red >= config.min_red)
        & (red_excess >= config.min_red_excess)
        & (red >= config.red_green_ratio * green)
        & (red >= config.red_blue_ratio * blue)
        & (brightness <= config.max_brightness)
    )
    magenta_column_like = (
        (red >= config.min_red)
        & ((red - green) >= max(4.0, config.min_red_excess * 0.45))
        & (red >= 0.62 * blue)
        & (blue >= 0.65 * red)
        & (brightness <= config.max_brightness)
    )
    magenta_column_mask = vertical_column_mask(magenta_column_like)
    sprite_like = red_like | magenta_column_mask

    red_pixels = int(sprite_like.sum())
    magenta_excess = np.maximum(red - green, red - (0.62 * blue))
    red_strength = float((np.clip(np.maximum(red_excess, magenta_excess), 0, None) * sprite_like).sum())
    area = max(1, roi.shape[0] * roi.shape[1])
    score = (red_strength / area) + (red_pixels / area) * config.pixel_weight
    score += config.vertical_bonus_weight * vertical_structure_score(magenta_column_mask | red_like)

    return FrameScore(0, 0.0, float(score), red_pixels, red_strength)


def score_temporal_frame(
    frame: np.ndarray,
    previous_frame: np.ndarray,
    config: DetectionConfig,
) -> FrameScore:
    if frame.shape != previous_frame.shape:
        raise ValueError("frame and previous_frame must have the same shape")

    height = frame.shape[0]
    start_y = max(0, min(height, int(height * config.roi_y_start_fraction)))
    end_y = max(start_y + 1, min(height, int(height * config.roi_top_fraction)))
    roi = frame[start_y:end_y].astype(np.float32)
    prev = previous_frame[start_y:end_y].astype(np.float32)

    red = roi[:, :, 0]
    green = roi[:, :, 1]
    blue = roi[:, :, 2]
    delta_red = red - prev[:, :, 0]
    delta_green = green - prev[:, :, 1]
    delta_blue = blue - prev[:, :, 2]
    brightness = np.maximum.reduce([red, green, blue])
    transient_red = delta_red - 0.35 * np.maximum(delta_green, delta_blue)

    mask = (
        (delta_red >= 2.0)
        & (transient_red >= 1.5)
        & ((red - green) >= -4.0)
        & (red >= 0.55 * blue)
        & (blue >= 0.55 * red)
        & (brightness <= config.max_brightness)
    )

    column_mask = vertical_column_mask(mask)
    red_pixels = int(column_mask.sum())
    red_strength = float((np.clip(transient_red, 0, None) * column_mask).sum())
    area = max(1, roi.shape[0] * roi.shape[1])
    score = (red_strength / area) + (red_pixels / area) * config.pixel_weight
    score += config.vertical_bonus_weight * 1.8 * vertical_structure_score(column_mask)
    return FrameScore(0, 0.0, float(score), red_pixels, red_strength)


def literature_sprite_score(frame: np.ndarray, config: DetectionConfig) -> FrameScore:
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must be an RGB array with shape (height, width, 3)")

    arr = frame.astype(np.float32)
    height, width = arr.shape[:2]
    target_y0 = int(height * 0.06)
    target_y1 = int(height * 0.70)
    horizon_y0 = int(height * 0.72)
    useful_x1 = int(width * 0.82)

    sky = arr[target_y0:target_y1, :useful_x1]
    horizon = arr[horizon_y0:, :]
    red = sky[:, :, 0]
    green = sky[:, :, 1]
    blue = sky[:, :, 2]
    brightness = np.maximum.reduce([red, green, blue])
    red_green_excess = red - green
    local_red_floor = float(np.median(red_green_excess) + 8.0)

    red_sprite_mask = (
        (red >= max(48.0, config.min_red))
        & (red_green_excess >= max(8.0, local_red_floor))
        & ((red - blue) >= -20.0)
        & (green <= 160.0)
        & (blue <= 190.0)
        & (brightness <= 235.0)
    )

    red_pixels = int(red_sprite_mask.sum())
    if red_pixels == 0:
        return FrameScore(0, 0.0, 0.0, 0, 0.0)

    component_score = sprite_component_score(red_sprite_mask, red_sprite_mask.shape)
    red_strength = float((np.clip(red - green, 0, None) * red_sprite_mask).sum())

    horizon_brightness = np.maximum.reduce(
        [horizon[:, :, 0], horizon[:, :, 1], horizon[:, :, 2]]
    )
    bright_horizon_ratio = float((horizon_brightness > 210).mean()) if horizon.size else 0.0
    sky_white_ratio = float(((brightness > 220) & (np.abs(red - green) < 24) & (np.abs(red - blue) < 28)).mean())
    broad_red_ratio = red_pixels / max(1, sky.shape[0] * sky.shape[1])

    # Literature-derived cues: sprites are localized, red, above storms, and often
    # vertically structured. Penalize city/vehicle lights and ordinary broad flashes.
    penalty = 1.0
    penalty *= max(0.15, 1.0 - bright_horizon_ratio * 4.0)
    penalty *= max(0.15, 1.0 - sky_white_ratio * 8.0)
    penalty *= max(0.2, 1.0 - max(0.0, broad_red_ratio - 0.08) * 5.0)

    score = (component_score + red_strength / max(1, sky.shape[0] * sky.shape[1]) * 0.5) * penalty
    return FrameScore(0, 0.0, float(score), red_pixels, red_strength)


def precision_sprite_score(
    frame: np.ndarray,
    previous_frame: np.ndarray | None,
    config: DetectionConfig,
) -> FrameScore:
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must be an RGB array with shape (height, width, 3)")

    arr = frame.astype(np.float32)
    height, width = arr.shape[:2]
    y0 = int(height * 0.06)
    y1 = int(height * 0.66)
    x1 = int(width * 0.80)
    roi = arr[y0:y1, :x1]
    red = roi[:, :, 0]
    green = roi[:, :, 1]
    blue = roi[:, :, 2]
    brightness = np.maximum.reduce([red, green, blue])
    red_excess = red - green
    local_floor = float(np.percentile(red_excess, 93) + 6.0)

    mask = (
        (red >= 58.0)
        & (red_excess >= max(14.0, local_floor))
        & ((red - blue) >= -22.0)
        & (green <= 145.0)
        & (blue <= 190.0)
        & (brightness <= 235.0)
    )

    if previous_frame is not None and previous_frame.shape == frame.shape:
        prev = previous_frame.astype(np.float32)[y0:y1, :x1]
        delta_red = red - prev[:, :, 0]
        delta_green = green - prev[:, :, 1]
        delta_blue = blue - prev[:, :, 2]
        transient_red = delta_red - 0.35 * np.maximum(delta_green, delta_blue)
        mask &= (delta_red >= -1.0) | (transient_red >= 1.0)

    components = sprite_components(mask)
    components = [
        component
        for component in components
        if component["area"] >= 12
        and component["y0"] <= mask.shape[0] * 0.78
        and component["w"] <= mask.shape[1] * 0.16
        and component["h"] >= 5
    ]
    if not components:
        return FrameScore(0, 0.0, 0.0, 0, 0.0)

    score = 0.0
    red_pixels = 0
    red_strength = 0.0
    for component in sorted(
        components,
        key=lambda item: item["area"] * min(4.0, item["aspect"]),
        reverse=True,
    )[:5]:
        ys = component["ys"]
        xs = component["xs"]
        area = int(component["area"])
        red_pixels += area
        component_strength = float(np.clip(red_excess[ys, xs], 0, None).sum())
        red_strength += component_strength
        upper_weight = 1.0 - float(component["y0"]) / max(1.0, mask.shape[0])
        vertical_weight = min(4.0, max(1.0, float(component["aspect"])))
        compactness = area / max(1.0, component["w"] * component["h"])
        score += np.log1p(area) * vertical_weight * upper_weight * (0.8 + compactness)

    # Penalize ordinary lightning and city/vehicle-light signatures.
    horizon = arr[int(height * 0.72) :, :]
    horizon_brightness = np.maximum.reduce(
        [horizon[:, :, 0], horizon[:, :, 1], horizon[:, :, 2]]
    )
    horizon_red = (
        (horizon[:, :, 0] > 120)
        & ((horizon[:, :, 0] - horizon[:, :, 1]) > 20)
        & (horizon_brightness < 245)
    )
    white_flash = (
        (brightness > 218)
        & (np.abs(red - green) < 28)
        & (np.abs(red - blue) < 32)
    )
    penalty = 1.0
    penalty *= max(0.2, 1.0 - float(horizon_red.mean()) * 10.0)
    penalty *= max(0.2, 1.0 - float(white_flash.mean()) * 12.0)
    return FrameScore(0, 0.0, float(score * penalty), red_pixels, red_strength)


def sprite_components(mask: np.ndarray) -> list[dict[str, object]]:
    height, width = mask.shape
    visited = np.zeros(mask.shape, dtype=bool)
    components: list[dict[str, object]] = []
    for y in range(height):
        for x in np.where(mask[y] & ~visited[y])[0]:
            if visited[y, x] or not mask[y, x]:
                continue
            stack = [(y, int(x))]
            visited[y, x] = True
            points: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                points.append((cy, cx))
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if (
                            0 <= ny < height
                            and 0 <= nx < width
                            and not visited[ny, nx]
                            and mask[ny, nx]
                        ):
                            visited[ny, nx] = True
                            stack.append((ny, nx))
            ys = np.array([point[0] for point in points], dtype=np.int32)
            xs = np.array([point[1] for point in points], dtype=np.int32)
            box_h = int(ys.max() - ys.min() + 1)
            box_w = int(xs.max() - xs.min() + 1)
            components.append(
                {
                    "area": len(points),
                    "x0": int(xs.min()),
                    "x1": int(xs.max()),
                    "y0": int(ys.min()),
                    "y1": int(ys.max()),
                    "w": box_w,
                    "h": box_h,
                    "aspect": box_h / max(1, box_w),
                    "ys": ys,
                    "xs": xs,
                }
            )
    return components


def sprite_component_score(mask: np.ndarray, shape: tuple[int, int]) -> float:
    height, width = shape
    visited = np.zeros(mask.shape, dtype=bool)
    best_components: list[float] = []

    for y in range(height):
        xs = np.where(mask[y] & ~visited[y])[0]
        for start_x in xs:
            if visited[y, start_x] or not mask[y, start_x]:
                continue

            stack = [(y, int(start_x))]
            visited[y, start_x] = True
            points: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                points.append((cy, cx))
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if (
                            0 <= ny < height
                            and 0 <= nx < width
                            and not visited[ny, nx]
                            and mask[ny, nx]
                        ):
                            visited[ny, nx] = True
                            stack.append((ny, nx))

            area = len(points)
            if area < 8:
                continue
            ys = np.array([point[0] for point in points])
            xs2 = np.array([point[1] for point in points])
            box_h = int(ys.max() - ys.min() + 1)
            box_w = int(xs2.max() - xs2.min() + 1)
            if box_h < 5:
                continue
            aspect = box_h / max(1, box_w)
            if box_w > width * 0.22 and aspect < 0.8:
                continue

            upper_weight = 1.0 - float(ys.min()) / max(1, height)
            vertical_weight = min(3.5, max(0.6, aspect))
            compactness = area / max(1, box_h * box_w)
            best_components.append(np.log1p(area) * vertical_weight * upper_weight * (0.65 + compactness))

    return float(sum(sorted(best_components, reverse=True)[:4]))


def vertical_column_mask(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    result = np.zeros(mask.shape, dtype=bool)
    if not mask.any():
        return result

    runs = np.zeros(width, dtype=np.int32)
    max_runs = np.zeros(width, dtype=np.int32)
    for row in mask:
        runs = (runs + 1) * row
        max_runs = np.maximum(max_runs, runs)

    active = max_runs >= 6
    max_width = max(12, int(width * 0.08))
    x = 0
    while x < width:
        if not active[x]:
            x += 1
            continue
        start = x
        while x < width and active[x]:
            x += 1
        end = x
        box_w = end - start
        if box_w > max_width:
            continue
        box_h = int(max_runs[start:end].max())
        aspect = box_h / max(1, box_w)
        if aspect < 1.8:
            continue
        result[:, start:end] = mask[:, start:end]

    return result


def vertical_structure_score(mask: np.ndarray) -> float:
    height, width = mask.shape
    if not mask.any():
        return 0.0

    runs = np.zeros(width, dtype=np.int32)
    max_runs = np.zeros(width, dtype=np.int32)
    for row in mask:
        runs = (runs + 1) * row
        max_runs = np.maximum(max_runs, runs)

    active = max_runs >= 6
    if not active.any():
        return 0.0

    best = 0.0
    max_width = max(12, int(width * 0.08))
    x = 0
    while x < width:
        if not active[x]:
            x += 1
            continue
        start = x
        while x < width and active[x]:
            x += 1
        end = x
        box_w = end - start
        if box_w > max_width:
            continue
        box_h = int(max_runs[start:end].max())
        area = int(max_runs[start:end].sum())
        aspect = box_h / max(1, box_w)
        if aspect >= 1.8 and area >= 4:
            best = max(best, min(4.0, aspect) * np.log1p(area))

    return float(best)


def pick_events(
    scores: list[FrameScore],
    max_events: int,
    cluster_seconds: float,
    min_score: float,
    percentile: float,
    min_red_pixels: int = 1,
) -> list[FrameScore]:
    if not scores or max_events <= 0:
        return []

    values = np.array([score.score for score in scores if score.score > 0], dtype=np.float64)
    if len(values) == 0:
        return []

    threshold = max(min_score, float(np.percentile(values, percentile)))
    peaks = [
        score
        for score in scores
        if score.score >= threshold and score.red_pixels >= min_red_pixels
    ]

    clusters: list[list[FrameScore]] = []
    for score in sorted(peaks, key=lambda item: item.timestamp):
        if not clusters or score.timestamp - clusters[-1][-1].timestamp > cluster_seconds:
            clusters.append([score])
        else:
            clusters[-1].append(score)

    best = [max(cluster, key=lambda item: item.score) for cluster in clusters]
    strongest = sorted(best, key=lambda item: item.score, reverse=True)[:max_events]
    return sorted(strongest, key=lambda item: item.timestamp)


def compute_clip_window(
    timestamp: float,
    pre_seconds: float,
    post_seconds: float,
    duration: float,
) -> tuple[float, float]:
    start = max(0.0, timestamp - pre_seconds)
    end = min(duration, timestamp + post_seconds)
    return (round(start, 6), round(end, 6))


def event_to_row(event: CandidateEvent) -> dict[str, str | int | float]:
    return {
        "video": str(event.video),
        "event_rank": event.event_rank,
        "timestamp_seconds": f"{event.timestamp:.6f}",
        "frame_index": event.frame_index,
        "score": f"{event.score:.6f}",
        "red_pixels": event.red_pixels,
        "red_strength": f"{event.red_strength:.2f}",
        "clip_start_seconds": f"{event.clip_start:.6f}",
        "clip_end_seconds": f"{event.clip_end:.6f}",
        "image_path": str(event.image_path),
        "clip_path": str(event.clip_path),
    }


def write_csv(events: list[CandidateEvent], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "video",
        "event_rank",
        "timestamp_seconds",
        "frame_index",
        "score",
        "red_pixels",
        "red_strength",
        "clip_start_seconds",
        "clip_end_seconds",
        "image_path",
        "clip_path",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event_to_row(event))


def _relative_ref(path: Path, out_dir: Path) -> str:
    try:
        return path.resolve().relative_to(out_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def render_html_report(
    events: list[CandidateEvent],
    settings: dict[str, object],
    out_dir: Path,
) -> str:
    settings_items = "\n".join(
        f"<li><code>{html.escape(str(key))}</code>: {html.escape(str(value))}</li>"
        for key, value in sorted(settings.items())
    )

    if events:
        cards = []
        for event in events:
            image_ref = html.escape(_relative_ref(event.image_path, out_dir))
            clip_ref = html.escape(_relative_ref(event.clip_path, out_dir))
            video_name = html.escape(event.video.name)
            cards.append(
                f"""
                <article class="event">
                  <div class="media">
                    <img src="{image_ref}" alt="{video_name} candidate frame">
                    <video src="{clip_ref}" controls preload="metadata"></video>
                  </div>
                  <div class="meta">
                    <h2>{video_name}</h2>
                    <p><strong>Time:</strong> {event.timestamp:.3f}s</p>
                    <p><strong>Clip:</strong> {event.clip_start:.3f}s - {event.clip_end:.3f}s</p>
                    <p><strong>Score:</strong> {event.score:.4f}</p>
                    <p><strong>Red pixels:</strong> {event.red_pixels}</p>
                  </div>
                </article>
                """
            )
        body = "\n".join(cards)
    else:
        body = "<p>No candidate red sprite events were detected with these settings.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Red Sprite Candidate Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #171717; background: #f7f7f5; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    .event {{ display: grid; grid-template-columns: minmax(280px, 1fr) minmax(220px, 320px); gap: 18px; padding: 16px 0; border-top: 1px solid #d8d8d2; }}
    .media {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }}
    img, video {{ width: 100%; background: #111; border-radius: 6px; }}
    .meta h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .meta p {{ margin: 6px 0; }}
    code {{ background: #ecece6; padding: 1px 4px; border-radius: 4px; }}
    @media (max-width: 760px) {{
      body {{ margin: 14px; }}
      .event, .media {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Red Sprite Candidate Report</h1>
    <p>{len(events)} candidate event(s)</p>
    <details>
      <summary>Run settings</summary>
      <ul>{settings_items}</ul>
    </details>
  </header>
  <main>
    {body}
  </main>
</body>
</html>
"""


def write_html_report(events: list[CandidateEvent], settings: dict[str, object], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html_report(events, settings, out_path.parent), encoding="utf-8")


def write_run_metadata(out_dir: Path, settings: dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "settings.json").write_text(
        json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def candidate_image_feature_vector(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB")).astype(np.float32)
    height, width = arr.shape[:2]
    sky = arr[: int(height * 0.83), : int(width * 0.86)]
    lower = arr[int(height * 0.83) :, :]
    right = arr[:, int(width * 0.86) :]

    def mask_stats(region: np.ndarray) -> tuple[float, float, float, float]:
        if region.size == 0:
            return (0.0, 0.0, 0.0, 0.0)
        red = region[:, :, 0]
        green = region[:, :, 1]
        blue = region[:, :, 2]
        brightness = np.maximum.reduce([red, green, blue])
        redish = (
            (red >= 38)
            & ((red - green) >= -2)
            & (red >= 0.58 * blue)
            & (blue >= 0.45 * red)
            & (brightness < 245)
        )
        ratio = float(redish.mean())
        red_excess = float(np.clip(red - green, 0, None).mean() / 255.0)
        magenta_balance = float(np.clip(np.minimum(red, blue) - green, 0, None).mean() / 255.0)
        brightness_mean = float(brightness.mean() / 255.0)
        return (ratio, red_excess, magenta_balance, brightness_mean)

    sky_ratio, sky_excess, sky_magenta, sky_brightness = mask_stats(sky)
    lower_ratio, _, _, _ = mask_stats(lower)
    right_ratio, _, _, _ = mask_stats(right)

    red = sky[:, :, 0]
    green = sky[:, :, 1]
    blue = sky[:, :, 2]
    column_mask = vertical_column_mask(
        (red >= 38)
        & ((red - green) >= -2)
        & (red >= 0.58 * blue)
        & (blue >= 0.45 * red)
        & (np.maximum.reduce([red, green, blue]) < 245)
    )
    vertical_score = vertical_structure_score(column_mask) / 30.0

    return np.array(
        [
            sky_ratio,
            sky_excess,
            sky_magenta,
            sky_brightness,
            vertical_score,
            max(0.0, sky_ratio - lower_ratio),
            max(0.0, sky_ratio - right_ratio),
            1.0 - min(1.0, right_ratio * 2.5),
        ],
        dtype=np.float64,
    )


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def rank_indices_by_positive_similarity(
    vectors: list[np.ndarray],
    positive_indices: list[int],
) -> list[int]:
    if not vectors:
        return []
    if not positive_indices:
        return list(range(len(vectors)))

    prototype = np.mean([vectors[index] for index in positive_indices], axis=0)
    scored = [(cosine_similarity(vector, prototype), index) for index, vector in enumerate(vectors)]
    return [index for _, index in sorted(scored, key=lambda item: item[0], reverse=True)]


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def ffprobe_info(video: Path) -> VideoInfo:
    proc = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration",
            "-of",
            "json",
            str(video),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video}: {proc.stderr.strip()}")

    data = json.loads(proc.stdout)
    stream = data["streams"][0]
    numerator, denominator = [float(part) for part in stream["r_frame_rate"].split("/")]
    fps = numerator / denominator if denominator else 0.0
    return VideoInfo(
        width=int(stream["width"]),
        height=int(stream["height"]),
        fps=fps,
        duration=float(stream.get("duration") or 0.0),
    )


def scan_video(
    video: Path,
    info: VideoInfo,
    config: DetectionConfig,
    scan_width: int,
    sample_fps: float,
    score_mode: str,
    progress_reporter: ProgressReporter | None = None,
    video_index: int = 1,
    total_videos: int = 1,
    completed_work_frames: int = 0,
    total_scan_frames: int | None = None,
) -> list[FrameScore]:
    width = min(scan_width, info.width)
    height = max(2, int(round(info.height * width / info.width)))
    if height % 2:
        height += 1
    total_scan_frames = total_scan_frames or estimated_scan_frames(info, sample_fps)

    filters = []
    effective_fps = info.fps
    if sample_fps > 0:
        filters.append(f"fps={sample_fps}")
        effective_fps = sample_fps
    filters.append(f"scale={width}:{height}:flags=fast_bilinear")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-vf",
        ",".join(filters),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.stdout is None:
        raise RuntimeError("ffmpeg stdout was not available")

    frame_size = width * height * 3
    scores: list[FrameScore] = []
    frame_index = 0
    previous_frame: np.ndarray | None = None
    if progress_reporter:
        progress_reporter.emit(
            current_video=video,
            video_index=video_index,
            total_videos=total_videos,
            processed_frames=0,
            total_frames=total_scan_frames,
            completed_work_frames=completed_work_frames,
            force=True,
        )
    while True:
        buf = proc.stdout.read(frame_size)
        if not buf:
            break
        if len(buf) != frame_size:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))
        if score_mode == "precision":
            scored = precision_sprite_score(frame, previous_frame, config)
        else:
            scored = score_frame(frame, config)
            literature_scored = literature_sprite_score(frame, config)
            if literature_scored.score > scored.score:
                scored = literature_scored
            if previous_frame is not None:
                temporal_scored = score_temporal_frame(frame, previous_frame, config)
                if temporal_scored.score > scored.score:
                    scored = temporal_scored
        previous_frame = frame.copy()
        scores.append(
            FrameScore(
                frame_index=frame_index,
                timestamp=frame_index / effective_fps if effective_fps > 0 else 0.0,
                score=scored.score,
                red_pixels=scored.red_pixels,
                red_strength=scored.red_strength,
            )
        )
        frame_index += 1
        if progress_reporter:
            progress_reporter.emit(
                current_video=video,
                video_index=video_index,
                total_videos=total_videos,
                processed_frames=frame_index,
                total_frames=total_scan_frames,
                completed_work_frames=completed_work_frames,
            )

    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"ffmpeg scan failed for {video}: {stderr.strip()}")
    if progress_reporter:
        progress_reporter.emit(
            current_video=video,
            video_index=video_index,
            total_videos=total_videos,
            processed_frames=total_scan_frames,
            total_frames=total_scan_frames,
            completed_work_frames=completed_work_frames,
            force=True,
        )
    return scores


def extract_frame(video: Path, timestamp: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{timestamp:.6f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out_path),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"frame extraction failed for {video}: {proc.stderr.strip()}")


def extract_clip(video: Path, start: float, end: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.01, end - start)
    proc = run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{start:.6f}",
            "-i",
            str(video),
            "-t",
            f"{duration:.6f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-an",
            str(out_path),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"clip extraction failed for {video}: {proc.stderr.strip()}")


def make_contact_sheet(events: list[CandidateEvent], out_path: Path, thumb_width: int = 360) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not events:
        image = Image.new("RGB", (900, 220), "white")
        draw = ImageDraw.Draw(image)
        draw.text((28, 92), "No candidate red sprite events detected.", fill=(20, 20, 20))
        image.save(out_path, quality=92)
        return

    thumbs: list[Image.Image] = []
    labels: list[str] = []
    for event in events:
        image = Image.open(event.image_path).convert("RGB")
        ratio = thumb_width / image.width
        thumb_height = max(1, int(image.height * ratio))
        thumbs.append(image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS))
        labels.append(f"{event.video.name}  {event.timestamp:.3f}s  score {event.score:.3f}")

    columns = min(3, len(thumbs))
    gap = 14
    label_height = 42
    cell_height = max(thumb.height for thumb in thumbs) + label_height
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new(
        "RGB",
        (columns * thumb_width + (columns + 1) * gap, rows * cell_height + (rows + 1) * gap),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, (thumb, label) in enumerate(zip(thumbs, labels)):
        row, column = divmod(index, columns)
        x = gap + column * (thumb_width + gap)
        y = gap + row * (cell_height + gap)
        sheet.paste(thumb, (x, y))
        draw.text((x, y + thumb.height + 6), label[:72], fill=(20, 20, 20), font=font)

    sheet.save(out_path, quality=92)


def build_settings(args: argparse.Namespace) -> dict[str, object]:
    keys = [
        "scan_width",
        "sample_fps",
        "max_candidates",
        "cluster_seconds",
        "percentile",
        "min_score",
        "min_red_pixels",
        "roi_top_fraction",
        "roi_y_start_fraction",
        "min_red",
        "min_red_excess",
        "red_green_ratio",
        "red_blue_ratio",
        "pre_seconds",
        "post_seconds",
        "clip_format",
        "score_mode",
    ]
    return {key: getattr(args, key) for key in keys}


def config_from_args(args: argparse.Namespace) -> DetectionConfig:
    return DetectionConfig(
        roi_top_fraction=args.roi_top_fraction,
        roi_y_start_fraction=args.roi_y_start_fraction,
        min_red=args.min_red,
        min_red_excess=args.min_red_excess,
        green_blue_suppression=args.green_blue_suppression,
        red_green_ratio=args.red_green_ratio,
        red_blue_ratio=args.red_blue_ratio,
        max_brightness=args.max_brightness,
        pixel_weight=args.pixel_weight,
    )


def process_video(
    video: Path,
    out_dir: Path,
    args: argparse.Namespace,
    info: VideoInfo | None = None,
    progress_reporter: ProgressReporter | None = None,
    video_index: int = 1,
    total_videos: int = 1,
    completed_work_frames: int = 0,
) -> list[CandidateEvent]:
    info = info or ffprobe_info(video)
    config = config_from_args(args)
    total_scan_frames = estimated_scan_frames(info, args.sample_fps)
    scores = scan_video(
        video,
        info,
        config,
        args.scan_width,
        args.sample_fps,
        args.score_mode,
        progress_reporter=progress_reporter,
        video_index=video_index,
        total_videos=total_videos,
        completed_work_frames=completed_work_frames,
        total_scan_frames=total_scan_frames,
    )
    picked = pick_events(
        scores,
        max_events=args.max_candidates,
        cluster_seconds=args.cluster_seconds,
        min_score=args.min_score,
        percentile=args.percentile,
        min_red_pixels=args.min_red_pixels,
    )

    video_dir = out_dir / safe_stem(video)
    events: list[CandidateEvent] = []
    for rank, score in enumerate(picked, start=1):
        clip_start, clip_end = compute_clip_window(
            score.timestamp,
            args.pre_seconds,
            args.post_seconds,
            info.duration,
        )
        base_name = f"{rank:02d}_{score.timestamp:010.3f}s_score-{score.score:.4f}"
        image_path = video_dir / f"{base_name}.jpg"
        clip_path = video_dir / f"{base_name}.{args.clip_format}"
        extract_frame(video, score.timestamp, image_path)
        extract_clip(video, clip_start, clip_end, clip_path)
        events.append(
            CandidateEvent(
                video=video,
                event_rank=rank,
                frame_index=score.frame_index,
                timestamp=score.timestamp,
                score=score.score,
                red_pixels=score.red_pixels,
                red_strength=score.red_strength,
                clip_start=clip_start,
                clip_end=clip_end,
                image_path=image_path,
                clip_path=clip_path,
            )
        )
    return events


def run_batch(args: argparse.Namespace) -> int:
    videos = discover_videos(args.inputs)
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_run_metadata(out_dir, build_settings(args))

    if not videos:
        write_csv([], out_dir / "candidates.csv")
        write_html_report([], build_settings(args), out_dir / "report.html")
        make_contact_sheet([], out_dir / "contact_sheet.jpg")
        print("No video files found.", file=sys.stderr)
        return 2

    all_events: list[CandidateEvent] = []
    failures: list[str] = []
    video_infos: list[tuple[Path, VideoInfo]] = []
    for video in videos:
        try:
            video_infos.append((video, ffprobe_info(video)))
        except Exception as exc:
            failures.append(f"{video}: {exc}")
            print(f"  failed: {exc}", file=sys.stderr)

    total_work_frames = sum(
        estimated_scan_frames(info, args.sample_fps) for _, info in video_infos
    ) or 1
    progress_reporter = ProgressReporter(args.progress_json, total_work_frames)
    completed_work_frames = 0
    total_videos = len(video_infos)
    for video_index, (video, info) in enumerate(video_infos, start=1):
        video_frames = estimated_scan_frames(info, args.sample_fps)
        print(f"Scanning {video}")
        try:
            events = process_video(
                video,
                out_dir,
                args,
                info=info,
                progress_reporter=progress_reporter,
                video_index=video_index,
                total_videos=total_videos,
                completed_work_frames=completed_work_frames,
            )
        except Exception as exc:
            failures.append(f"{video}: {exc}")
            print(f"  failed: {exc}", file=sys.stderr)
            completed_work_frames += video_frames
            continue
        all_events.extend(events)
        completed_work_frames += video_frames
        print(f"  exported {len(events)} event(s)")

    write_csv(all_events, out_dir / "candidates.csv")
    write_html_report(all_events, build_settings(args), out_dir / "report.html")
    make_contact_sheet(all_events, out_dir / "contact_sheet.jpg")

    if failures:
        (out_dir / "failures.txt").write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"Completed with {len(failures)} failed video(s). Results: {out_dir}", file=sys.stderr)
        return 1

    print(f"Done. Results: {out_dir}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan thunderstorm videos and export likely red sprite frames and clips."
    )
    parser.add_argument("inputs", nargs="+", help="Video files, folders, or globs.")
    parser.add_argument("--out", default="red_sprite_candidates", help="Output folder.")
    parser.add_argument("--scan-width", type=int, default=640, help="Width used for fast scanning.")
    parser.add_argument("--sample-fps", type=float, default=0.0, help="Scan FPS. 0 scans all frames.")
    parser.add_argument("--max-candidates", type=int, default=24, help="Max events per video.")
    parser.add_argument("--cluster-seconds", type=float, default=0.25, help="Merge adjacent hits.")
    parser.add_argument("--percentile", type=float, default=98.5, help="Dynamic score percentile.")
    parser.add_argument("--min-score", type=float, default=0.012, help="Absolute score floor.")
    parser.add_argument("--min-red-pixels", type=int, default=8, help="Minimum red pixels in scan frame.")
    parser.add_argument("--roi-top-fraction", type=float, default=0.78, help="Top image fraction to scan.")
    parser.add_argument("--roi-y-start-fraction", type=float, default=0.0, help="Skip top fraction if needed.")
    parser.add_argument("--min-red", type=float, default=42.0, help="Minimum red channel value.")
    parser.add_argument("--min-red-excess", type=float, default=10.0, help="Red minus suppressed G/B floor.")
    parser.add_argument("--green-blue-suppression", type=float, default=1.02, help="G/B suppression factor.")
    parser.add_argument("--red-green-ratio", type=float, default=1.18, help="R/G ratio floor.")
    parser.add_argument("--red-blue-ratio", type=float, default=0.92, help="R/B ratio floor.")
    parser.add_argument("--max-brightness", type=float, default=245.0, help="Reject near-white flashes.")
    parser.add_argument("--pixel-weight", type=float, default=6.0, help="Area contribution to score.")
    parser.add_argument("--pre-seconds", type=float, default=1.0, help="Seconds before event in clips.")
    parser.add_argument("--post-seconds", type=float, default=2.0, help="Seconds after event in clips.")
    parser.add_argument("--clip-format", choices=["mp4", "mov"], default="mp4", help="Exported clip format.")
    parser.add_argument("--progress-json", action="store_true", help="Emit machine-readable scan progress events.")
    parser.add_argument(
        "--score-mode",
        choices=["precision", "recall"],
        default="precision",
        help="precision reduces false positives; recall keeps older high-recall behavior.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("ffmpeg and ffprobe are required.", file=sys.stderr)
        return 127
    return run_batch(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
