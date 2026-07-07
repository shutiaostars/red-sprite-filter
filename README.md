**[中文](README.md)** | [English](README.en.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# 红色精灵筛选器

一个面向高空瞬态发光事件观测的 macOS 桌面工具，用来从相机拍摄的雷暴视频中自动筛选疑似红色精灵闪电帧与片段。

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Release](https://img.shields.io/badge/download-DMG-00bcd4?style=flat-square)
![Local](https://img.shields.io/badge/processing-local-4caf50?style=flat-square)

## 它能做什么

红色精灵闪电通常短暂、微弱、位置高、形态细而复杂，人工从长视频里逐帧寻找非常耗时。这个工具会扫描整条视频，对每一帧进行红色精灵候选评分，并自动导出：

- 候选关键帧
- 候选短片段
- `candidates.csv`
- `contact_sheet.jpg`
- `report.html`
- 人工复核后的 `confirmed_candidates.csv`

它不会只找到第一个候选就停止，而是会扫描完整条视频，再从全片中挑出得分最高的候选事件。

## 界面预览

当前版本是 macOS 原生窗口 App，内部使用 WebView 承载本地界面。打开后不会跳转浏览器，视频处理也不会上传到网络。

界面包含：

- 选择视频 / 选择文件夹 / 选择输出目录
- 精准筛选 / 高召回筛选
- 候选帧网格
- 候选片段播放
- 确认 / 疑似 / 排除人工复核
- 打开报告 / 打开结果目录

## 下载

到右侧或页面下方的 **Releases** 中下载：

```text
red-sprite-filter-1.0.0.dmg
```

下载后打开 DMG，把 `红色精灵筛选器.app` 拖到 Applications 或任意文件夹即可。

## 第一次打开

当前版本尚未进行 Apple Developer ID 签名和公证，所以 macOS 可能会提示“无法验证开发者”。

解决方式：

1. 右键点击 `红色精灵筛选器.app`
2. 选择“打开”
3. 在弹窗中再次点击“打开”

## 依赖

当前版本为了保持包体较小，仍使用目标电脑上的本地运行环境。需要：

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

推荐用 Homebrew 安装：

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

App 启动后会自动检查依赖状态。如果看到 `ffmpeg not found` 或 `ffprobe not found`，请先确认 Homebrew 已安装 `ffmpeg`。

## 推荐使用方式

### 精筛单条视频

适合已知某条视频可能拍到红色精灵的情况。

推荐参数：

- 模式：精准筛选
- 候选上限：24
- 最小分数：0.8
- 最小红像素：8
- 前置秒数：1.0
- 后置秒数：2.0

### 批量初筛文件夹

适合先快速检查一批雷暴素材。

推荐参数：

- 模式：高召回筛选
- 候选上限：24
- 最小分数：0.012
- 最小红像素：8

初筛后，再对可疑视频单独使用“精准筛选”复跑。

## 如何判断候选是不是红色精灵

更像红色精灵的候选通常具有：

- 位于云顶上方或画面较高处
- 红色或品红色明显
- 形态局部，不是整条地平线泛红
- 有竖向柱状、须状、水母状或精细分支感
- 持续时间极短，通常只在少数几帧中明显

常见误报包括：

- 普通云内闪电或云地闪电
- 城市灯光、车灯、塔灯、飞机灯
- 地平线红光
- 镜头眩光
- 大面积曝光变化
- 固定热噪点或压缩噪声

## 隐私说明

所有视频都在本机处理。工具不会上传视频、帧图、候选片段或路径信息。

## 当前状态

这是一个摄影工作流工具的早期公开版本。它适合辅助筛选，不应替代人工复核。欢迎提交 Issue，反馈误报、漏检、不同相机素材表现和功能建议。

## 未来计划

- 内置 Python 与 ffmpeg，降低安装门槛
- Apple Developer ID 签名与公证
- 支持更细的时间范围扫描
- 增加批量结果汇总视图
- 引入更多真实样本校准筛选阈值

