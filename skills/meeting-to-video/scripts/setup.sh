#!/bin/bash
# Usage: bash setup.sh <output-dir>
# Copies the Remotion template to <output-dir> and installs deps from package-lock.json (npm ci).
# Remotion 公式スキルは SKILL.md の任意ステップで npx 実行する（setup 内ではネット上の別スキルを取り込まない）。

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:?Usage: bash setup.sh <output-dir>}"

echo "→ Copying template to $OUTPUT_DIR"
cp -r "$SKILL_DIR/template/" "$OUTPUT_DIR"

echo "→ Installing dependencies (npm ci from lockfile)"
cd "$OUTPUT_DIR"
# Remove node_modules copied from template (cp -r dereferences symlinks on macOS,
# causing broken .bin/ entries). Always do a fresh install.
rm -rf node_modules
npm ci

echo ""
echo "✓ Setup complete."
echo "  Next: write content.json, then run: cd $OUTPUT_DIR && npx remotion preview"
echo "  Optional: Remotion official skills → see SKILL.md Step 3b"
