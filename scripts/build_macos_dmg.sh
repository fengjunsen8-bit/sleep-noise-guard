#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_PATH="$ROOT_DIR/outputs/睡眠噪音守卫.app"
DMG_PATH="$ROOT_DIR/outputs/睡眠噪音守卫.dmg"
STAGING_DIR="$ROOT_DIR/outputs/dmg-staging"

"$ROOT_DIR/scripts/build_macos_app.sh" >/dev/null

rm -rf "$STAGING_DIR" "$DMG_PATH"
mkdir -p "$STAGING_DIR"
cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

hdiutil create \
  -volname "睡眠噪音守卫" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

rm -rf "$STAGING_DIR"
echo "$DMG_PATH"
