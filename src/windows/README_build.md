# 构建 Windows 版 `red-sprite-filter.exe`

本项目用 **Python + pywebview** 作为跨平台桌面壳（Windows 上走系统自带的 Edge / WebView2），
配合原有的 Python 检测器与 HTML 前端，一套代码即可在 Windows / macOS / Linux 上运行原生窗口。

本目录下的脚本帮你把整个程序打包成**单个可移植的 `.exe`**——双击即用、无需安装，
ffmpeg/ffprobe 已自动打包进 exe，用户无需自行安装任何东西。

## 准备工作（只需一次）

1. 安装 **Python 3.10+**（勾选 "Add python.exe to PATH"）。
   验证：打开命令提示符输入 `python --version` 能看到版本号。
2. 确保电脑能联网（首次构建需下载一次 ffmpeg）。

## 一键构建

在**文件资源管理器**里进入 `work\windows` 目录，双击 `build.bat` 即可。
脚本会自动：

1. 创建隔离虚拟环境 `venv`（不污染你的系统 Python）
2. 安装运行依赖与 PyInstaller
3. 下载 Windows 版 ffmpeg / ffprobe 到 `red_sprite_app\bin\windows`
4. 用 PyInstaller 打包

完成后在 `work\dist\red-sprite-filter.exe` 生成单个 exe 文件。

> 想用命令行构建，在该目录执行 `build.bat` 同样效果。

## 产物

| 文件 | 说明 |
|------|------|
| `dist\red-sprite-filter.exe` | 单文件可移植程序，双击运行、无需安装 |
| `red_sprite_app\bin\windows\ffmpeg.exe` | 构建时下载的 ffmpeg（已打进 exe） |
| `red_sprite_app\bin\windows\ffprobe.exe` | 构建时下载的 ffprobe（已打进 exe） |

## 给最终用户的使用说明

- 把 `red-sprite-filter.exe` 复制到有写入权限的目录（如桌面），双击运行。
- 首次启动可能弹出 **Windows SmartScreen** 拦截提示（因为软件未签名）。
  点击「更多信息」→「仍要运行」即可。
- 软件窗口内选择视频 / 素材文件夹 / 输出目录，点击开始分析即可。

## 如何更新到新版本

重新执行 `build.bat` 会覆盖旧产物。建议构建前先 `git pull` 拉取最新源码。

## 常见问题

**Q：构建时报 "python 不是内部或外部命令"？**
A：Python 没加入 PATH。重新安装 Python 并勾选 "Add python.exe to PATH"，
或手动把 Python 安装目录加入系统环境变量。

**Q：ffmpeg 下载失败 / 很慢？**
A：`get_ffmpeg.py` 从 GitHub 下载 BtbN 构建版。若网络受限，可手动下载
`ffmpeg-master-latest-win64-gpl.zip`（来自 https://github.com/BtbN/FFmpeg-Builds/releases），
解压后把 `bin\ffmpeg.exe` 和 `bin\ffprobe.exe` 复制到 `red_sprite_app\bin\windows\`，再重跑 `build.bat`。

**Q：能不能做成安装包（含开始菜单/卸载）？**
A：当前方案是单文件 exe。若需要 NSIS 安装向导，可在此基础上加一层 NSIS 打包，
告诉我即可。

## 各平台壳对应关系

| 平台 | 原生壳 | 说明 |
|------|--------|------|
| Windows | pywebview (WebView2/Edge) | 本构建产出 |
| macOS | pywebview (WebKit) 或 原 Swift 壳 | 原 macOS 版走 Swift 壳 |
| Linux | pywebview (GTK-WebKit) | 需系统装 webkit2gtk |
