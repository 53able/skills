#!/bin/bash
# Usage: bash setup.sh <output-dir>
# Copies the Remotion template to <output-dir>, runs npm ci, then ensures remotion-dev/skills
# (skill name: remotion-best-practices) is present under .agents/skills/ — runs npx skills add if missing.

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

REMOTION_SKILL_MARK=".agents/skills/remotion-best-practices/SKILL.md"
if [[ ! -f "$REMOTION_SKILL_MARK" ]]; then
  echo "→ Installing remotion-dev/skills (remotion-best-practices) — $REMOTION_SKILL_MARK not found"
  npx skills add remotion-dev/skills --yes
else
  echo "→ remotion-best-practices already present ($REMOTION_SKILL_MARK), skipping npx skills add"
fi

echo ""
echo "✓ Setup complete."
echo "  Next: write content.json, then run: cd $OUTPUT_DIR && npx remotion preview"
