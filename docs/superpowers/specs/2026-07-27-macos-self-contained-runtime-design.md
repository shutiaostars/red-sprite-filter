# macOS Apple Silicon Self-Contained Runtime Design

Date: 2026-07-27

## Summary

Release `v1.0.6` will make the macOS application self-contained on Apple
Silicon. A user will not need Homebrew, a system Python installation, pip,
`numpy`, Pillow, `ffmpeg`, or `ffprobe`.

The application will continue to use the existing native Swift and WebKit
shell. The shell will launch a bundled CPython runtime, and the backend will
find bundled FFmpeg tools before any external tools.

## Scope

### Included

- Apple Silicon (`arm64`) Macs running macOS 12 or later.
- A bundled CPython runtime.
- Bundled `numpy` and Pillow packages.
- Bundled static `ffmpeg` and `ffprobe` executables.
- Pinned artifact URLs and SHA-256 verification.
- Third-party notices and redistribution information.
- An isolated functional test that does not use Homebrew or user Python.
- A new DMG, checksums, release notes, README updates, and GitHub release
  `v1.0.6`.

### Not included

- Intel Mac or universal binaries.
- Apple Developer ID signing or notarization.
- Changes to red-sprite scoring or video-analysis behavior.
- New user-interface features.
- Bundling macOS system frameworks such as Cocoa and WebKit. These are platform
  components and remain supplied by macOS.

## Locked Runtime Inputs

The build will use a committed runtime lock file. It will contain these exact
artifacts and hashes:

| Component | Version and artifact | SHA-256 |
| --- | --- | --- |
| CPython | `cpython-3.12.13+20260718-aarch64-apple-darwin-install_only_stripped.tar.gz` | `9a1e9e06175c10efd8378b904b07fa21bd791ab3345d7cdffeb4a76c9ff55903` |
| FFmpeg | `ffmpeg-8.1.2` arm64 release ZIP | `ef1aa60006c7b77ce170c1608c08d8e4ba1c30c5746f2ac986ded932d0ac2c3c` |
| FFprobe | `ffprobe-8.1.2` arm64 release ZIP | `c39787f4af7a3932502d2d48db6f6feaaa836b48a73ef78c32cc3285df61dfaf` |
| NumPy | `numpy-1.26.4-cp312-cp312-macosx_11_0_arm64.whl` | `03a8c78d01d9781b28a6989f6fa1bb2c4f2d51201cf99d3dd875df6fbd96b23b` |
| Pillow | `pillow-11.3.0-cp312-cp312-macosx_11_0_arm64.whl` | `921bd305b10e82b4d1f5e802b6850677f965d8394203d182f078873851dada69` |

Source URLs:

- CPython:
  `https://github.com/astral-sh/python-build-standalone/releases/download/20260718/cpython-3.12.13%2B20260718-aarch64-apple-darwin-install_only_stripped.tar.gz`
- FFmpeg:
  `https://ffmpeg.martin-riedl.de/download/macos/arm64/1783011502_8.1.2/ffmpeg.zip`
- FFprobe:
  `https://ffmpeg.martin-riedl.de/download/macos/arm64/1783011502_8.1.2/ffprobe.zip`
- NumPy:
  `https://files.pythonhosted.org/packages/75/5b/ca6c8bd14007e5ca171c7c03102d17b4f4e0ceb53957e8c44343a9546dcc/numpy-1.26.4-cp312-cp312-macosx_11_0_arm64.whl`
- Pillow:
  `https://files.pythonhosted.org/packages/2c/32/7e2ac19b5713657384cec55f89065fb306b06af008cfd87e572035b27119/pillow-11.3.0-cp312-cp312-macosx_11_0_arm64.whl`

The downloaded CPython executable declares `arm64` and macOS 11.0. The FFmpeg
and FFprobe executables declare `arm64` and macOS 12.0. None of these three
executables references `/opt/homebrew` or `/usr/local` dynamic libraries.

## Bundle Layout

```text
红色精灵筛选器.app/
  Contents/
    MacOS/
      red-sprite-filter
    Resources/
      app/
        red_sprite_app/
        red_sprite_filter.py
      bin/
        ffmpeg
        ffprobe
      runtime/
        python/
          bin/python3
          lib/...
      licenses/
        THIRD_PARTY_NOTICES.md
        CPython-LICENSE.txt
        FFmpeg-COPYING.GPLv3.txt
        NumPy-LICENSE.txt
        Pillow-LICENSE.txt
      AppIcon.icns
```

Build caches and downloaded archives will live outside the App bundle. They
will not be committed and will not be copied into the DMG.

## Build Components

### Runtime lock

`tools/macos_runtime.lock.json` will hold each download URL, SHA-256, expected
archive member, architecture, and maximum deployment target. Builds will never
follow a `latest` redirect.

### Runtime vendor

`tools/vendor_macos_runtime.py` will:

1. Download or reuse cached artifacts.
2. verify SHA-256 before extraction;
3. extract CPython into `Contents/Resources/runtime/python`;
4. install the two pinned Python wheels into that bundled runtime;
5. extract `ffmpeg` and `ffprobe` into `Contents/Resources/bin`;
6. remove caches, tests, pip download residue, and `__pycache__` files;
7. copy third-party licenses and source/build references;
8. verify architecture, deployment target, executable permission, and dynamic
   library references.

Any checksum mismatch, unexpected archive layout, non-arm64 binary, deployment
target newer than macOS 12, or Homebrew library reference will stop the build.

### App builder

`tools/build_app.py` will call the runtime vendor instead of installing Python
packages into a `python_lib` directory with `/usr/bin/python3`. The version will
be raised to `1.0.6`. The Swift launcher will be compiled with the explicit
target `arm64-apple-macos12.0`; the `Info.plist` minimum version alone is not
treated as sufficient evidence of compatibility. All resources will be added
before ad hoc code signing.

### Swift launcher

The native launcher will execute:

```text
Contents/Resources/runtime/python/bin/python3
```

Its `PATH` will begin with `Contents/Resources/bin` and retain only normal
macOS system directories afterward. It will no longer add Homebrew directories
or launch `/usr/bin/python3`.

The existing backend URL handshake, process termination, and WebKit window
behavior will remain unchanged.

### Backend

Source-mode behavior will remain compatible with external development tools.
In the packaged App, dependency discovery will resolve `ffmpeg` and `ffprobe`
from `Contents/Resources/bin`. The health response will continue to expose the
resolved executable paths so the packaged location can be verified.

## Runtime Flow

1. The user launches the Swift executable.
2. The launcher resolves the App resource directory.
3. It starts bundled CPython with the backend module.
4. The backend inherits a `PATH` beginning with the bundled binary directory.
5. Dependency checks resolve bundled Python, NumPy, Pillow, FFmpeg, and
   FFprobe.
6. Video probing, scanning, keyframe extraction, and clip export use the
   bundled FFmpeg tools.
7. Results are written to the user-selected output directory as before.

## Error Handling

- Build-time integrity failures stop with the component name, expected hash,
  actual hash, and source URL.
- Missing archive members stop before an incomplete App is signed.
- Runtime startup errors continue to appear in the native fatal-error dialog.
- The dependency panel will show the actual bundled path if a tool cannot be
  resolved.
- No fallback to Homebrew will be added in the packaged launch environment;
  this prevents a broken package from appearing healthy only on the build Mac.

## Licensing

The selected FFmpeg build is configured with GPL components. The App will
distribute FFmpeg and FFprobe as separate executables and include:

- the applicable GPL text;
- FFmpeg version and build configuration;
- the FFmpeg source release URL;
- the static-build project source URL;
- notices for CPython, NumPy, Pillow, and included binary dependencies.

The release notes will identify the bundled third-party components and point to
the notices inside the App bundle.

## Testing

Implementation will follow test-first development.

### Automated bundle tests

- The bundled Python, FFmpeg, and FFprobe files exist and are executable.
- The launcher source contains the bundled runtime and binary paths and no
  `/usr/bin/python3`, `/opt/homebrew`, or `/usr/local` launch dependency.
- Bundled Python imports NumPy and Pillow with user site packages disabled.
- The backend health check resolves every dependency inside the App bundle.
- All packaged Mach-O executables, including the Swift launcher, are `arm64`.
- Every packaged Mach-O executable declares a minimum macOS version no newer
  than 12.0.
- Non-system dynamic library references do not point outside the App bundle.
- The App contains no Python caches or downloaded archives.
- Ad hoc signature verification passes.

### Isolated functional test

With an empty temporary home directory and a restricted environment that
contains no Homebrew or user Python path:

1. use bundled FFmpeg to create a short synthetic video;
2. use bundled FFprobe to read its metadata;
3. run the detector with bundled CPython;
4. verify settings, CSV, HTML report, and exported media are produced.

### DMG verification

- Build and verify the compressed DMG.
- Mount the DMG read-only.
- Run dependency and functional probes directly against the mounted App.
- Launch the mounted App and confirm the backend starts.
- Run `codesign --verify --deep --strict` and `hdiutil verify`.
- Record final size and SHA-256.

## Documentation And Release

- Update all localized READMEs to say that the macOS package contains all
  third-party runtime dependencies.
- Remove the Homebrew installation requirement for release `v1.0.6`.
- Move macOS dependency bundling from the roadmap to completed work.
- Generate release notes and checksums for `red-sprite-filter-1.0.6.dmg`.
- Push source changes and publish the verified DMG in GitHub Release `v1.0.6`.

## Acceptance Criteria

The work is complete only when:

1. a clean Apple Silicon Mac running macOS 12 or later needs no Homebrew,
   Python, pip, NumPy, Pillow, FFmpeg, or FFprobe installation;
2. the mounted DMG passes the isolated dependency and functional test;
3. no packaged runtime binary references a Homebrew path;
4. code-signature and DMG integrity checks pass;
5. the release asset can be downloaded again from GitHub and matches the
   published size and SHA-256.
