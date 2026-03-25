#!/bin/bash
# install.sh
#
# meeting-to-video スキルを手動インストールするフォールバックスクリプト。
#
# 通常は npx skills を使うほうが簡単です:
#   npx skills add 53able/skills --skill meeting-to-video -g
#
# npx skills が使えない場合のみ、このスクリプトを使ってください。
#
# 使い方:
#   bash meeting-to-video/install.sh
#   bash meeting-to-video/install.sh --target cursor      # Cursor のみ
#   bash meeting-to-video/install.sh --target claude      # Claude Code のみ
#   bash meeting-to-video/install.sh --dry-run            # 確認のみ

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="meeting-to-video"
TARGET="claude"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# --- プラットフォームのグローバルスキルディレクトリ定義 ---
declare -A PLATFORM_DIRS=(
  [claude]="$HOME/.claude/skills/$SKILL_NAME"
  [cursor]="$HOME/.cursor/skills/$SKILL_NAME"
  [codex]="$HOME/.codex/skills/$SKILL_NAME"
  [gemini]="$HOME/.gemini/skills/$SKILL_NAME"
  [windsurf]="$HOME/.codeium/windsurf/skills/$SKILL_NAME"
  [copilot]="$HOME/.copilot/skills/$SKILL_NAME"
  [opencode]="$HOME/.config/opencode/skills/$SKILL_NAME"
)

# --- インストール対象を決定 ---
if [[ "$TARGET" == "all" ]]; then
  TARGETS=()
  for platform in "${!PLATFORM_DIRS[@]}"; do
    parent_dir="$(dirname "${PLATFORM_DIRS[$platform]}")"
    if [[ -d "$parent_dir" ]]; then
      TARGETS+=("$platform")
    fi
  done
  if [[ ${#TARGETS[@]} -eq 0 ]]; then
    echo "ERROR: インストール可能なプラットフォームが見つかりません。" >&2
    echo "  推奨: npx skills add 53able/skills --skill meeting-to-video -g" >&2
    exit 1
  fi
else
  if [[ -z "${PLATFORM_DIRS[$TARGET]:-}" ]]; then
    echo "ERROR: 未知のターゲット: $TARGET" >&2
    echo "  有効な値: ${!PLATFORM_DIRS[*]} all" >&2
    exit 1
  fi
  TARGETS=("$TARGET")
fi

# --- インストール実行 ---
for platform in "${TARGETS[@]}"; do
  dest="${PLATFORM_DIRS[$platform]}"

  if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] $platform → $dest"
    continue
  fi

  echo "→ [$platform] $dest へインストール中..."
  mkdir -p "$(dirname "$dest")"

  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -d "$dest" ]]; then
    echo "  既存ディレクトリをバックアップ: ${dest}.bak"
    mv "$dest" "${dest}.bak"
  fi

  ln -s "$SCRIPT_DIR" "$dest"
  echo "  ✓ $dest → $SCRIPT_DIR"
done

if [[ "$DRY_RUN" == false ]]; then
  echo ""
  echo "✓ インストール完了"
  echo ""
  echo "TIP: 次回以降は npx skills が使えます:"
  echo "  npx skills add 53able/skills --skill meeting-to-video -g"
fi
