# 睡眠噪音守卫

睡眠噪音守卫是一款用于监听本地环境噪音的工具。程序通过麦克风估算环境分贝，当噪音超过设定阈值并满足触发条件后，会通过音箱播放反馈音效，例如咳嗽、走路、搬东西或掉东西的声音。

项目目标是帮助用户在睡眠环境中自动感知持续噪音，并通过可配置的反馈音提醒外部环境降低干扰。

## 主要功能

- 实时监听麦克风输入并估算环境分贝
- 超过阈值后播放反馈音效
- 支持设置“出现几秒后触发”
- 支持设置“出现几次后触发”
- 支持设置每次触发后的反馈音效播放次数
- 支持冷却时间，避免频繁重复触发
- CSV 日志记录噪音出现时间、分贝数、触发次数和播放音效
- 显示本小时和全天噪音统计
- 支持 macOS、Windows、Android 三个平台源码和构建流程

## 平台支持

### macOS

macOS 版本使用原生 SwiftUI 中文界面，支持打包为 DMG。

构建 `.app`：

```bash
chmod +x scripts/build_macos_app.sh
scripts/build_macos_app.sh
```

打开应用：

```bash
open "outputs/睡眠噪音守卫.app"
```

打包 DMG：

```bash
chmod +x scripts/build_macos_dmg.sh
scripts/build_macos_dmg.sh
```

产物位置：

```text
outputs/睡眠噪音守卫.dmg
```

### Windows

Windows 版本使用 Python 桌面界面，并通过 PyInstaller 打包为 EXE。

本地打包命令：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
pyinstaller packaging/windows/sleep-noise-guard-windows.spec --noconfirm
```

产物位置：

```text
dist/睡眠噪音守卫.exe
```

### Android

Android 版本位于 `android/` 目录，使用原生 Java 实现麦克风监听、分贝估算、触发策略、日志和统计。

本地构建命令：

```bash
cd android
gradle assembleDebug
```

产物位置：

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

Android 版本会请求麦克风权限，并使用系统提示音作为反馈音。

## GitHub 自动构建

仓库已配置 GitHub Actions：

```text
.github/workflows/build-release.yml
```

推送到 `main` 分支后会自动构建：

- macOS DMG：`sleep-noise-guard-macos-dmg`
- Windows EXE：`sleep-noise-guard-windows-exe`
- Android APK：`sleep-noise-guard-android-apk`

也可以在 GitHub Actions 页面手动运行工作流：

```text
Build Release Artifacts
```

## 参数说明

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| 噪音阈值 dB | 45 | 超过该分贝后认为出现噪音 |
| 出现几秒后触发 | 留空 | 留空表示不等待持续时间 |
| 出现几次后触发 | 留空 | 留空表示首次检测到噪音就可触发 |
| 每次反馈播放次数 | 留空 | 留空表示每次触发只播放一次 |
| 冷却时间 秒 | 60 | 两次触发之间的最小间隔 |
| 校准偏移 | 94 | 用于把麦克风 dBFS 粗略换算为环境分贝 |
| 日志路径 | `logs/noise_events.csv` | CSV 日志文件位置 |

当“出现几秒后触发”“出现几次后触发”“每次反馈播放次数”都留空时，程序会在检测到超过阈值的噪音后立即反馈一次。

## 日志系统

Python 桌面版默认写入：

```text
logs/noise_events.csv
```

日志字段：

- `timestamp`：噪音出现时间
- `hour`：小时统计桶
- `date`：日期统计桶
- `db`：估算分贝
- `triggered`：是否触发反馈
- `trigger_count`：累计触发次数
- `feedback_repeats`：本次反馈播放次数
- `sounds`：播放的音效文件

界面会展示：

- 本小时噪音次数
- 本小时触发次数
- 今日噪音次数
- 今日触发次数

## 音效文件

反馈音效放在：

```text
sounds/
```

支持格式：

- `.wav`
- `.mp3`
- `.m4a`
- `.flac`
- `.ogg`
- `.aif`
- `.aiff`

项目自带占位音效，可重新生成：

```bash
python3 scripts/generate_sample_sounds.py
```

实际使用时建议替换为更自然的短音频，例如咳嗽、脚步、搬东西、掉东西等声音。

## 命令行运行

安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

列出音频设备：

```bash
sleep-noise-guard --list-devices
```

使用默认设备启动：

```bash
sleep-noise-guard --sounds-dir sounds --threshold-db 45 --cooldown 60
```

指定输入和输出设备：

```bash
sleep-noise-guard --input-device 2 --output-device 5 --sounds-dir sounds
```

## 目录结构

```text
macos/                  macOS SwiftUI 原生界面
android/                Android 原生项目
sleep_noise_guard/      Python 核心逻辑和 Windows 桌面界面
scripts/                构建脚本和示例音效生成脚本
packaging/windows/      Windows EXE 打包配置
docs/中文说明.md         中文使用说明
sounds/                 示例反馈音效
tests/                  Python 单元测试
```

## 测试

```bash
python3 -m unittest discover -s tests
```
