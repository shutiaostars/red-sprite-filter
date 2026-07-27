[中文](README.md) | **[English](README.en.md)** | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# Red Sprite Filter

A macOS / Windows desktop tool for transient luminous event (TLE) observation that automatically screens suspected **red sprite** lightning frames and clips from storm videos recorded by cameras.

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078d4?style=flat-square)
[![Release](https://img.shields.io/badge/download-DMG%20%2B%20EXE-00bcd4?style=flat-square)](https://github.com/shutiaostars/red-sprite-filter/releases/latest)
![Local](https://img.shields.io/badge/processing-local-4caf50?style=flat-square)

## What it does

Red sprites are typically brief, faint, located high in the sky, and have fine, complex shapes. Manually scanning long videos frame by frame is extremely time-consuming. This tool scans the entire video, scores every frame for red-sprite candidates, and automatically exports:

- Candidate keyframes
- Candidate short clips
- `candidates.csv`
- `contact_sheet.jpg`
- `report.html`
- `confirmed_candidates.csv` after manual review

It does **not** stop at the first candidate. Precise screening keeps every separate event that reaches the explicit minimum score, so consecutive sprites are no longer reduced to only the strongest event.

## UI preview

The current version is a desktop window app that uses a WebView to host the local interface. It does not open a browser, and video processing is never uploaded to the network.

The interface includes:

- Select video / folder / output directory
- Precise screening / high-recall screening
- Candidate frame grid
- Candidate clip playback
- Scan progress, elapsed time, and estimated remaining time
- No repeated console windows while scanning on Windows
- Original-video timeline display for clips, such as `3:12-3:14`
- Score guide with high / medium / low suspected-target categories
- Confirm / suspected / exclude manual review
- Open report / open result directory

## Download

Download from the **Releases** section (right side or bottom of the page):

- [macOS Apple Silicon: red-sprite-filter-1.0.6.dmg](https://github.com/shutiaostars/red-sprite-filter/releases/download/v1.0.6/red-sprite-filter-1.0.6.dmg)
- [Windows 10/11: red-sprite-filter-setup.exe](https://github.com/shutiaostars/red-sprite-filter/releases/download/v1.0.6/red-sprite-filter-setup.exe)

On macOS, open the DMG and drag the app (`红色精灵筛选器.app`, shown as "Red Sprite Filter") to Applications or any folder.

Windows installer users can double-click `red-sprite-filter-setup.exe` and follow the installer. It creates a Start Menu shortcut and can optionally create a desktop shortcut.

## First launch

The current build is **not** Apple Developer ID signed or notarized, so macOS may show a "cannot verify developer" warning.

To open:

1. Right-click `红色精灵筛选器.app`
2. Choose "Open"
3. Click "Open" again in the dialog

## Dependencies

The macOS package bundles:

- CPython 3.12.13
- NumPy 1.26.4
- Pillow 11.3.0
- FFmpeg 8.1.2
- FFprobe 8.1.2

Homebrew is not required. Users do not need to install Python, pip, or any command-line dependency. The app checks its bundled dependencies on launch.

The Windows installer bundles `ffmpeg`, `ffprobe`, the Python runtime, and Python dependencies, so users usually do not need command-line dependencies. Windows 10/11 normally already includes the Edge WebView2 runtime.

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

## Score guide and categories

Candidates are labeled by review priority:

- `≥ 5.0`: highly suspected target
- `1.0 - 5.0`: medium suspected target
- `< 1.0`: low suspected target

The category is only a review-priority hint, not a final scientific conclusion. Please confirm with the keyframe, exported clip, and original video.

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

## Scientific basis and references

The tool combines published research with public NOAA and NASA observation material, translating the visible characteristics below into candidate scores. It is a **rule-based candidate screening tool**, not a scientifically calibrated confirmation system. Scores and high/medium/low suspicion labels only set manual-review priority. Thresholds in the code are engineering values tuned for camera footage, not physical constants taken from the papers.

### 1. High-altitude position above thunderstorms

The Sprites94 aircraft observations by Sentman et al. describe red sprites as high-altitude luminous events above thunderstorms. The tool therefore prioritizes the upper frame and regions above cloud tops while reducing the weight of the horizon, urban light bands, and fixed near-ground lights.

- Sentman, D. D. et al. (1995), *Preliminary results from the Sprites94 Aircraft Campaign: 1. Red sprites*, Geophysical Research Letters, 22(10), 1205-1208.
  https://doi.org/10.1029/95GL00583

### 2. Red or magenta spectral signature

Spectroscopic observations identify molecular nitrogen first-positive-band emissions as a major component of sprite light. The tool scores red excess over green and blue plus the local red-pixel ratio, while penalizing the broad white or near-neutral brightening typical of ordinary lightning.

- Hampton, D. L. et al. (1996), *Optical spectral characteristics of sprites*, Geophysical Research Letters, 23(1), 89-92.
  https://doi.org/10.1029/95GL03587
- Mende, S. B. et al. (1995), *Sprite spectra: N2 1PG band identification*, Geophysical Research Letters, 22(19), 2633-2636.
  https://doi.org/10.1029/95GL02827

### 3. High-altitude discharge associated with thunderstorms

Pasko et al. discuss electrical discharge extending from a thundercloud top toward the lower ionosphere. The tool uses the spatial combination of an elevated, localized event above active storm clouds as supporting evidence instead of confirming a target from red color alone.

- Pasko, V. P. et al. (2002), *Electrical discharge from a thundercloud top to the lower ionosphere*, Nature, 416, 152-154.
  https://doi.org/10.1038/416152a

### 4. Millisecond, frame-to-frame transient behavior

High-speed imaging shows that sprite, halo, and related structures develop rapidly on millisecond time scales. The tool compares red excess and structural changes between neighboring frames, prioritizing brief localized appearances and suppressing persistent sources such as city lights, vehicle lights, tower lights, and hot pixels.

- Moudry, D. R. et al. (2003), *Imaging of elves, halos and sprite initiation at 1 ms time resolution*, Journal of Atmospheric and Solar-Terrestrial Physics, 65(5), 509-518.
  https://doi.org/10.1016/S1364-6826(02)00323-1

### 5. Vertical streamers, columns, tendrils, and branches

High-speed observations show rapidly developing streamers along with columnar, carrot-shaped, tendril-like, and branching structures. The tool rewards elevated, narrow, vertically extended red components and groups of nearby components, while penalizing broad horizon bands and whole-frame exposure changes.

- Stenbaek-Nielsen, H. C. et al. (2013), *High-Speed Observations of Sprite Streamers*, Surveys in Geophysics, 34, 769-795.
  https://doi.org/10.1007/s10712-013-9224-4

### 6. Public NOAA and NASA observation guidance

NOAA and NASA describe red sprites as brief, predominantly red transient luminous events above thunderstorms that can appear jellyfish-shaped, carrot-shaped, or columnar. These sources provide a cross-check for the visible features and manual-review guidance used for photographic video.

- NOAA NSSL, *Lightning Types: Transient Luminous Events*
  https://www.nssl.noaa.gov/education/svrwx101/lightning/types/
- NASA Science, *Spritacular*
  https://science.nasa.gov/citizen-science/spritacular/
- NASA Scientific Visualization Studio, *The Elusive Red Sprite*
  https://svs.gsfc.nasa.gov/11059
- NASA Scientific Visualization Studio, *Elusive Sprite Captured from the International Space Station*
  https://svs.gsfc.nasa.gov/31111/

## Privacy

All video is processed locally on your machine. The tool never uploads video, frames, candidate clips, or path information.

## Current status

This is an early public version of a photography workflow tool. It is meant to assist screening, not replace manual review. Issues and feedback are welcome — false positives, missed detections, behavior on different camera models, and feature suggestions.

## Recently completed

- The macOS package bundles CPython, NumPy, Pillow, FFmpeg, and FFprobe; Homebrew is not required
- The Windows installer now bundles `ffmpeg`, `ffprobe`, the Python runtime, and dependencies, and scanning no longer opens repeated console windows
- Full-video scanning keeps multiple independent events above the threshold, including consecutive sprites
- Folder batch scanning provides one candidate list plus keyframes, event clips, CSV, contact sheet, and HTML report
- Scan progress, elapsed time, estimated remaining time, original-video timestamps, suspicion levels, and manual review

## Next steps

- Complete Apple Developer ID signing and notarization
- Let users select scan start/end times and the sky region of interest
- Add richer batch statistics, candidate filtering, sorting, and summary export
- Calibrate thresholds with more labeled real-world samples and publish precision/recall results
