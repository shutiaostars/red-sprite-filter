from __future__ import annotations

import shutil
import subprocess
import sys
import hashlib
import re
from pathlib import Path

import build_app


ROOT = Path(__file__).resolve().parents[1]
VERSION = build_app.VERSION
OUTPUTS = ROOT / "outputs"
APP = OUTPUTS / "红色精灵筛选器.app"
DMG = OUTPUTS / "红色精灵筛选器.dmg"
RELEASE_DMG = OUTPUTS / f"red-sprite-filter-{VERSION}.dmg"
GITHUB_PUBLISH = OUTPUTS / "github_publish"
NOTES = OUTPUTS / "GITHUB_RELEASE_NOTES.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_release_notes(digest: str) -> None:
    NOTES.write_text(
        f"""# 红色精灵筛选器 v{VERSION}

## 下载

请下载本 Release 附件：

```text
{RELEASE_DMG.name}
```

这个文件可上传到 GitHub Releases，供其他用户下载。本版本修复了其他电脑上扫描时报 `ModuleNotFoundError: No module named 'numpy'` 的问题。

SHA-256:

```text
{digest}
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
- App 内置 `numpy` 和 `Pillow`，不再要求用户手动安装 Python 包

## 安装方法

1. 下载 `{RELEASE_DMG.name}`
2. 打开 DMG
3. 将 `红色精灵筛选器.app` 拖到 Applications 或任意文件夹
4. 右键 App，选择“打开”

## 依赖要求

当前 macOS App 已内置 `numpy` 和 `Pillow`，不需要用户手动安装 Python 包。

目标电脑仍需要安装：

- `ffmpeg`
- `ffprobe`

推荐安装命令：

```bash
brew install ffmpeg
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
""",
        encoding="utf-8",
    )


def refresh_github_publish_files(digest: str) -> None:
    if not GITHUB_PUBLISH.exists():
        return

    shutil.copy2(RELEASE_DMG, GITHUB_PUBLISH / RELEASE_DMG.name)
    (GITHUB_PUBLISH / "CHECKSUMS.txt").write_text(f"{digest}  {RELEASE_DMG.name}\n", encoding="utf-8")
    for path in GITHUB_PUBLISH.glob(f"RELEASE_v{VERSION}*.md"):
        text = path.read_text(encoding="utf-8")
        path.write_text(re.sub(r"[0-9a-f]{64}", digest, text), encoding="utf-8")


def build_dmg() -> Path:
    app = build_app.build()
    if DMG.exists():
        DMG.unlink()
    if RELEASE_DMG.exists():
        RELEASE_DMG.unlink()
    subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            "红色精灵筛选器",
            "-srcfolder",
            str(app),
            "-ov",
            "-format",
            "UDZO",
            str(DMG),
        ],
        check=True,
    )
    shutil.copy2(DMG, RELEASE_DMG)
    digest = sha256(RELEASE_DMG)
    write_release_notes(digest)
    refresh_github_publish_files(digest)
    return DMG


if __name__ == "__main__":
    print(build_dmg())
