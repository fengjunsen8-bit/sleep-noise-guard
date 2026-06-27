# Cross Platform Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package Sleep Noise Guard for macOS DMG, Windows EXE, and Android APK, with Chinese source documentation and GitHub Actions build automation.

**Architecture:** Keep the existing Python core for macOS/Windows desktop behavior. Add a native Android Java implementation that mirrors the current monitoring, trigger, logging, and statistics behavior. Use GitHub Actions to build platform artifacts on their native runners.

**Tech Stack:** Python, SwiftUI, Java Android, GitHub Actions, hdiutil, PyInstaller, Gradle Android Plugin.

---

### Task 1: macOS DMG Packaging

**Files:**
- Create: `scripts/build_macos_dmg.sh`
- Modify: `README.md`

- [x] Add a script that builds `outputs/睡眠噪音守卫.app` and packages it as `outputs/睡眠噪音守卫.dmg`.
- [x] Verify locally with `scripts/build_macos_dmg.sh`.

### Task 2: Windows Desktop Source and EXE CI

**Files:**
- Create: `sleep_noise_guard/windows_desktop.py`
- Create: `packaging/windows/sleep-noise-guard-windows.spec`
- Create: `.github/workflows/build-release.yml`

- [ ] Add a Windows-friendly Tk desktop entry that exposes the same Chinese controls.
- [ ] Add PyInstaller configuration for a single-folder or single-file EXE.
- [ ] Build EXE on `windows-latest` in GitHub Actions.

### Task 3: Android APK Source and CI

**Files:**
- Create: `android/settings.gradle`
- Create: `android/build.gradle`
- Create: `android/app/build.gradle`
- Create: `android/app/src/main/AndroidManifest.xml`
- Create: `android/app/src/main/java/com/sleepnoiseguard/MainActivity.java`

- [ ] Build a native Android app with microphone monitoring, trigger delay, repeat playback, CSV logging, and hourly/daily counters.
- [ ] Build debug APK through GitHub Actions.

### Task 4: Chinese Documentation and Upload

**Files:**
- Create: `docs/中文说明.md`
- Modify: `README.md`

- [ ] Explain macOS, Windows, and Android build/use steps in Chinese.
- [ ] Initialize git if missing.
- [ ] Commit changes locally.
- [ ] Push only if a GitHub remote is configured or user provides one.
