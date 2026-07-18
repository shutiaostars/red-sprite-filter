[中文](README.md) | **[English](README.en.md)** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# Red Sprite Filter

A macOS desktop tool for transient luminous event (TLE) observation that automatically screens suspected **red sprite** lightning frames and clips from storm videos recorded by cameras.

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Release](https://img.shields.io/badge/download-DMG-00bcd4?style=flat-square)
![Local](https://img.shields.io/badge/processing-local-4caf50?style=flat-square)

## What it does

Red sprites are typically brief, faint, located high in the sky, and have fine, complex shapes. Manually scanning long videos frame by frame is extremely time-consuming. This tool scans the entire video, scores every frame for red-sprite candidates, and automatically exports:

- Candidate keyframes
- Candidate short clips
- `candidates.csv`
- `contact_sheet.jpg`
- `report.html`
- `confirmed_candidates.csv` after manual review

It does **not** stop at the first candidate — it scans the whole video and then picks the highest-scoring candidate events from the entire footage.

## UI preview

The current version is a native macOS window app that uses a WebView to host the local interface. It does not open a browser, and video processing is never uploaded to the network.

The interface includes:

- Select video / folder / output directory
- Precise screening / high-recall screening
- Candidate frame grid
- Candidate clip playback
- Confirm / suspected / exclude manual review
- Open report / open result directory

## Download

Download from the **Releases** section (right side or bottom of the page):

```text
red-sprite-filter-1.0.1.dmg
```

Open the DMG and drag the app (`红色精灵筛选器.app`, shown as "Red Sprite Filter") to Applications or any folder.

## First launch

The current build is **not** Apple Developer ID signed or notarized, so macOS may show a "cannot verify developer" warning.

To open:

1. Right-click `红色精灵筛选器.app`
2. Choose "Open"
3. Click "Open" again in the dialog

## Dependencies

The macOS app now bundles `numpy` and `Pillow`, so users do not need to install Python packages manually.

The target Mac still needs:

- `ffmpeg`
- `ffprobe`

Recommended install via Homebrew:

```bash
brew install ffmpeg
```

The app checks dependencies on launch. If you see `ffmpeg not found` or `ffprobe not found`, make sure Homebrew's `ffmpeg` is installed.

## Recommended usage

### Precise single-video screening

Best when you suspect a specific video may have caught red sprites.

Recommended parameters:

- Mode: Precise
- Max candidates: 24
- Min score: 0.8
- Min red pixels: 8
- Pre-roll: 1.0s
- Post-roll: 2.0s

### Batch folder pre-screening

Best for quickly checking a batch of storm footage.

Recommended parameters:

- Mode: High recall
- Max candidates: 24
- Min score: 0.012
- Min red pixels: 8

After pre-screening, re-run suspicious videos in Precise mode.

## How to tell if a candidate is a red sprite

Candidates that look more like red sprites usually have:

- A position above the cloud top or high in the frame
- Clearly red or magenta color
- A localized shape, not a whole-horizon red glow
- Vertical columnar, tendril, jellyfish, or fine-branching structure
- Extremely short duration, usually obvious in only a few frames

Common false positives include:

- Ordinary intra-cloud or cloud-to-ground lightning
- City lights, car lights, tower lights, aircraft lights
- Horizon red glow
- Lens flare
- Large exposure changes
- Fixed hot pixels or compression noise

## Privacy

All video is processed locally on your machine. The tool never uploads video, frames, candidate clips, or path information.

## Current status

This is an early public version of a photography workflow tool. It is meant to assist screening, not replace manual review. Issues and feedback are welcome — false positives, missed detections, behavior on different camera models, and feature suggestions.

## Roadmap

- Bundle ffmpeg to lower the setup barrier
- Apple Developer ID signing and notarization
- Support finer time-range scanning
- Add a batch result summary view
- Calibrate screening thresholds with more real samples
