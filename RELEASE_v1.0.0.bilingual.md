# Red Sprite Filter v1.0.0

The first downloadable macOS desktop release.

## Download

Download the Release asset below:

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
bd6af44aeb2a082ca09b5dfd14843dacc68388054564da5f9bdece595a2d1833
```

## Main features

- Automatically screen suspected red sprite lightning from thunderstorm videos
- Scans the entire video; does not stop at the first candidate
- Single-video and batch folder scanning
- Precise and high-recall screening modes
- Auto-exports candidate keyframes, clips, CSV, HTML report, and contact sheet
- Manual labeling: confirm / suspected / exclude
- Export confirmed candidate list
- Native macOS standalone window, no browser redirect

## Installation

1. Download `red-sprite-filter-1.0.0.dmg`
2. Open the DMG
3. Drag `红色精灵筛选器.app` (shown as "Red Sprite Filter") to Applications or any folder
4. Right-click the app and choose "Open"

## Requirements

The current version requires the following on your Mac:

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

Recommended install:

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS security note

This build is not signed or notarized. On first launch macOS may warn that the developer cannot be verified. Right-click the app, choose "Open", then confirm in the dialog. A future public release should add Apple Developer ID signing and notarization.

## Known limitations

- This is a rule-based tool (color, shape, position, and timing features), not a machine-learning model
- Results still require manual review
- Not all runtime dependencies are bundled; a fresh machine may need them installed first
- Unsigned builds show a security warning on some macOS devices at first launch

## Who it's for

- Thunderstorm photographers
- Astrophotographers
- Transient luminous event (TLE) observation enthusiasts
- Anyone who wants to quickly find red-sprite candidate clips from large amounts of footage

---

# 红色精灵筛选器 v1.0.0

首个可下载的 macOS 桌面版本。

## 下载

请下载本 Release 附件：

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
bd6af44aeb2a082ca09b5dfd14843dacc68388054564da5f9bdece595a2d1833
```

## 主要功能

- 从雷暴视频中自动筛选疑似红色精灵闪电
- 扫描完整条视频，不会遇到第一个候选就停止
- 支持单视频和文件夹批量扫描
- 支持精准筛选和高召回筛选
- 自动导出候选关键帧、候选片段、CSV、HTML 报告和 contact sheet
- 支持人工标记：确认、疑似、排除
- 支持导出确认候选列表
- macOS 原生独立窗口，不再跳转系统浏览器

## 安装方法

1. 下载 `red-sprite-filter-1.0.0.dmg`
2. 打开 DMG
3. 将 `红色精灵筛选器.app` 拖到 Applications 或任意文件夹
4. 右键 App，选择“打开”

## 依赖要求

当前版本需要本机已安装：

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

推荐安装命令：

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS 安全提示

当前版本未签名、未公证。首次打开时，macOS 可能提示无法验证开发者。

请右键点击 App，选择“打开”，再在弹窗中确认打开。

后续正式公开版本建议加入 Apple Developer ID 签名和 notarization 公证。

## 已知限制

- 当前版本不是机器学习模型，而是基于颜色、形态、位置和时序特征的候选筛选工具
- 结果仍需要人工复核
- 未内置所有运行依赖，陌生机器上可能需要先安装依赖
- 未签名版本在部分 macOS 设备上首次打开会有安全提示

## 适合谁

- 雷暴摄影师
- 星空摄影师
- 高空瞬态发光事件观测爱好者
- 想从大量素材里快速找红色精灵候选片段的人
