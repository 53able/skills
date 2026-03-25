#!/bin/bash
# Usage: bash setup.sh <output-dir>
# Copies the Remotion template to <output-dir>, installs deps, and adds Remotion skills.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:?Usage: bash setup.sh <output-dir>}"

echo "→ Copying template to $OUTPUT_DIR"
cp -r "$SKILL_DIR/template/" "$OUTPUT_DIR"

echo "→ Installing dependencies"
cd "$OUTPUT_DIR"
# Remove node_modules copied from template (cp -r dereferences symlinks on macOS,
# causing broken .bin/ entries). Always do a fresh install.
rm -rf node_modules
npm install

echo "→ Installing Remotion official skills (project-scoped)"
# npx skills は Cursor / Claude Code など複数プラットフォームで利用可能
# 利用できない環境ではスキップして手動参照で続行する
if command -v npx &>/dev/null && npx skills add remotion-dev/skills --yes 2>/dev/null; then
  echo "  Remotion skills installed"
  # Cursor: .cursor/skills/  Claude Code: rules/ など環境により異なる
  echo "  Verify: ls .cursor/skills/ 2>/dev/null || ls rules/ 2>/dev/null"
else
  echo "  INFO: npx skills add をスキップ。"
  echo "        Remotion 公式ドキュメントを手動参照: https://remotion.dev/docs"
fi

echo ""
echo "✓ Setup complete."
echo "  Next: write content.json, then run: cd $OUTPUT_DIR && npx remotion preview"
