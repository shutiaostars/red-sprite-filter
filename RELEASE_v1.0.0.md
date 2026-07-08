# 红色精灵筛选器 v1.0.0

首个可下载的 macOS 桌面版本。

## 下载

请下载本 Release 附件：

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
9aa9a3f5656fec5c9b1fd8d03a34e9184d2861b7e579a703796b7db704196c87
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

