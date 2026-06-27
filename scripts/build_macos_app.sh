#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT_DIR/outputs/睡眠噪音守卫.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

swiftc -parse-as-library "$ROOT_DIR/macos/SleepNoiseGuardApp.swift" \
  -o "$MACOS_DIR/睡眠噪音守卫" \
  -framework SwiftUI \
  -framework AppKit

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>睡眠噪音守卫</string>
  <key>CFBundleIdentifier</key>
  <string>local.sleep-noise-guard.ui</string>
  <key>CFBundleName</key>
  <string>睡眠噪音守卫</string>
  <key>CFBundleDisplayName</key>
  <string>睡眠噪音守卫</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
</dict>
</plist>
PLIST

printf '%s\n' "$ROOT_DIR" > "$RESOURCES_DIR/project_path.txt"
echo "$APP_DIR"
