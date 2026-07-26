**[中文](README.md)** | [English](README.en.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md)

# 红色精灵筛选器

一个面向高空瞬态发光事件观测的 macOS / Windows 桌面工具，用来从相机拍摄的雷暴视频中自动筛选疑似红色精灵闪电帧与片段。

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078d4?style=flat-square)
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

它不会只找到第一个候选就停止，而是会扫描完整条视频。精准筛选会保留所有达到最小分数的独立事件，连续出现的红色精灵不再只保留最强一组。

## 界面预览

当前版本是桌面窗口 App，内部使用 WebView 承载本地界面。打开后不会跳转浏览器，视频处理也不会上传到网络。

界面包含：

- 选择视频 / 选择文件夹 / 选择输出目录
- 精准筛选 / 高召回筛选
- 候选帧网格
- 候选片段播放
- 扫描进度、已花费时间、预计剩余时间
- Windows 扫描期间不显示反复弹出的黑色终端窗口
- 原视频时间轴片段显示，例如 `3:12-3:14`
- 评分标准与高度疑似目标 / 中等疑似目标 / 低疑似目标分类
- 确认 / 疑似 / 排除人工复核
- 打开报告 / 打开结果目录

## 下载

到右侧或页面下方的 **Releases** 中下载：

```text
macOS:   red-sprite-filter-1.0.5.dmg
Windows: red-sprite-filter-setup.exe
```

macOS 下载后打开 DMG，把 `红色精灵筛选器.app` 拖到 Applications 或任意文件夹即可。

Windows 安装包下载后双击 `red-sprite-filter-setup.exe`，按安装向导完成安装。安装器会创建开始菜单快捷方式，也可选择创建桌面快捷方式。

## 第一次打开

当前版本尚未进行 Apple Developer ID 签名和公证，所以 macOS 可能会提示“无法验证开发者”。

解决方式：

1. 右键点击 `红色精灵筛选器.app`
2. 选择“打开”
3. 在弹窗中再次点击“打开”

## 依赖

当前 macOS App 已内置 `numpy` 和 `Pillow`，不需要用户手动安装 Python 包。

macOS 目标电脑仍需要安装：

- `ffmpeg`
- `ffprobe`

推荐用 Homebrew 安装：

```bash
brew install ffmpeg
```

App 启动后会自动检查依赖状态。如果看到 `ffmpeg not found` 或 `ffprobe not found`，请先确认 Homebrew 已安装 `ffmpeg`。

Windows 安装包会随程序打包 `ffmpeg`、`ffprobe`、Python 运行时和 Python 依赖；通常不需要用户额外安装命令行依赖。Windows 10/11 一般已带 Edge WebView2 运行环境。

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

## 评分标准与分类

候选结果会按照分数显示复核优先级：

- `≥ 5.0`：高度疑似目标
- `1.0 - 5.0`：中等疑似目标
- `< 1.0`：低疑似目标

这个分类用于帮助排序复核优先级，不代表最终结论。最终仍建议结合关键帧、候选片段和原视频人工确认。

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

## 科学判断依据与参考文献

本工具综合论文和 NOAA、NASA 的公开观测资料，把下列可见特征转换为候选评分。它是**规则型候选筛选工具**，不是经过专业观测设备标定的科学确认系统；分数和“高度/中等/低度疑似”只代表人工复核优先级。代码中的阈值是针对相机视频进行样本调试后的工程参数，不是论文中的物理常数。

### 1. 位于雷暴云顶上方的高空区域

Sentman 等人的 Sprites94 飞机观测将红色精灵描述为雷暴上方的高空发光事件。工具因此优先检查画面上部和云顶上方区域，并降低地平线、城市灯光带及近地固定光源的权重。

- Sentman, D. D. et al. (1995), *Preliminary results from the Sprites94 Aircraft Campaign: 1. Red sprites*, Geophysical Research Letters, 22(10), 1205-1208.
  https://doi.org/10.1029/95GL00583

### 2. 红色或品红色光谱特征

光谱观测表明，红色精灵的可见辐射主要与分子氮第一正带系统有关。工具使用红色相对绿色、蓝色的增量和局部红像素比例进行评分，同时惩罚普通闪电常见的白色、近中性色大面积增亮。

- Hampton, D. L. et al. (1996), *Optical spectral characteristics of sprites*, Geophysical Research Letters, 23(1), 89-92.
  https://doi.org/10.1029/95GL03587
- Mende, S. B. et al. (1995), *Sprite spectra: N2 1PG band identification*, Geophysical Research Letters, 22(19), 2633-2636.
  https://doi.org/10.1029/95GL02827

### 3. 雷暴触发的高空放电背景

Pasko 等人讨论了从雷暴云顶向低层电离层发展的高空放电。工具据此把“云顶上方、局部出现、与雷暴活动同场”的空间关系作为辅助特征，而不会仅凭红色就确认目标。

- Pasko, V. P. et al. (2002), *Electrical discharge from a thundercloud top to the lower ionosphere*, Nature, 416, 152-154.
  https://doi.org/10.1038/416152a

### 4. 毫秒级、帧间突现的瞬态特征

高速成像显示精灵、光晕和相关瞬态结构会在毫秒尺度快速发展。工具比较相邻帧的红色增量和结构变化，优先保留短暂突现的局部目标，并抑制城市灯、车灯、塔灯和热像素等长期稳定光源。

- Moudry, D. R. et al. (2003), *Imaging of elves, halos and sprite initiation at 1 ms time resolution*, Journal of Atmospheric and Solar-Terrestrial Physics, 65(5), 509-518.
  https://doi.org/10.1016/S1364-6826(02)00323-1

### 5. 竖向流光、柱状、须状和分支形态

高速观测显示红色精灵常包含快速发展的 streamer（流光）以及柱状、胡萝卜状、须状和分支结构。工具会奖励位于高空、较窄、竖向延伸并包含多个相近分量的红色结构，同时惩罚横贯地平线的宽光带和整帧曝光变化。

- Stenbaek-Nielsen, H. C. et al. (2013), *High-Speed Observations of Sprite Streamers*, Surveys in Geophysics, 34, 769-795.
  https://doi.org/10.1007/s10712-013-9224-4

### 6. NOAA 与 NASA 的公开观测说明

NOAA 和 NASA 的资料将红色精灵概括为雷暴上方、以红色为主、持续短暂，并可能呈水母状、胡萝卜状或柱状的瞬态发光事件。这些资料用于交叉核对软件面向摄影视频的可见特征和人工复核建议。

- NOAA NSSL, *Lightning Types: Transient Luminous Events*
  https://www.nssl.noaa.gov/education/svrwx101/lightning/types/
- NASA Science, *Spritacular*
  https://science.nasa.gov/citizen-science/spritacular/
- NASA Scientific Visualization Studio, *The Elusive Red Sprite*
  https://svs.gsfc.nasa.gov/11059
- NASA Scientific Visualization Studio, *Elusive Sprite Captured from the International Space Station*
  https://svs.gsfc.nasa.gov/31111/

## 隐私说明

所有视频都在本机处理。工具不会上传视频、帧图、候选片段或路径信息。

## 当前状态

这是一个摄影工作流工具的早期公开版本。它适合辅助筛选，不应替代人工复核。欢迎提交 Issue，反馈误报、漏检、不同相机素材表现和功能建议。

## 已完成的近期改进

- Windows 安装包已内置 `ffmpeg`、`ffprobe`、Python 运行时和依赖，扫描时不再反复弹出终端窗口
- 扫描完整条视频，并保留达到阈值的多个独立事件和连续出现的红色精灵
- 支持文件夹批量扫描，以统一候选列表、关键帧、事件片段、CSV、接触表和 HTML 报告汇总结果
- 增加扫描进度、已用时间、预计剩余时间、原视频时间轴、疑似等级和人工复核

## 下一步计划

- 在 macOS 安装包中内置 `ffmpeg` 和 `ffprobe`，移除 Homebrew 依赖
- 完成 Apple Developer ID 签名与公证
- 支持用户指定扫描起止时间和天空区域
- 增强批量统计、候选筛选、排序与摘要导出
- 使用更多已标注真实样本校准阈值，并公布 precision / recall 测试结果
