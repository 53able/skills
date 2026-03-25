#!/bin/bash
# resolve-skill-dir.sh
#
# meeting-to-video スキルのインストール先ディレクトリを返す。
# npx skills でインストールされた全エージェントのグローバルパスを網羅する。
#
# 使い方（他スクリプトから source して使う）:
#   source "$(dirname "${BASH_SOURCE[0]}")/resolve-skill-dir.sh"
#   echo "$MEETING_TO_VIDEO_SKILL_DIR"
#
# 優先順位:
#   1. 環境変数 MEETING_TO_VIDEO_SKILL_DIR が設定されていればそれを使う
#   2. 各エージェントのグローバルスキルディレクトリを順に検索
#   3. プロジェクトスコープのスキルディレクトリを検索
#   4. このスクリプト自身の2階層上（リポジトリから直接実行した場合）

if [[ -n "${MEETING_TO_VIDEO_SKILL_DIR:-}" && -d "$MEETING_TO_VIDEO_SKILL_DIR" ]]; then
  : # 環境変数の値をそのまま使う
else
  # npx skills グローバルインストールパス（全エージェント対応）
  # 参照: https://github.com/vercel-labs/skills
  _candidates=(
    # Claude Code
    "$HOME/.claude/skills/meeting-to-video"
    # Cursor
    "$HOME/.cursor/skills/meeting-to-video"
    # Codex
    "$HOME/.codex/skills/meeting-to-video"
    # Gemini CLI / Antigravity
    "$HOME/.gemini/skills/meeting-to-video"
    # Windsurf
    "$HOME/.codeium/windsurf/skills/meeting-to-video"
    # GitHub Copilot
    "$HOME/.copilot/skills/meeting-to-video"
    # OpenCode
    "$HOME/.config/opencode/skills/meeting-to-video"
    # Amp / Kimi Code CLI / Replit / Universal
    "$HOME/.config/agents/skills/meeting-to-video"
    # Cline / Warp
    "$HOME/.agents/skills/meeting-to-video"
    # Augment
    "$HOME/.augment/skills/meeting-to-video"
    # Droid (Factory AI)
    "$HOME/.factory/skills/meeting-to-video"
    # OpenHands
    "$HOME/.openhands/skills/meeting-to-video"
    # Pi
    "$HOME/.pi/agent/skills/meeting-to-video"
    # Roo Code
    "$HOME/.roo/skills/meeting-to-video"
    # Kiro CLI
    "$HOME/.kiro/skills/meeting-to-video"
    # Goose
    "$HOME/.config/goose/skills/meeting-to-video"
    # Junie
    "$HOME/.junie/skills/meeting-to-video"
    # Qwen Code
    "$HOME/.qwen/skills/meeting-to-video"
    # Windsurf (旧パス)
    "$HOME/.windsurf/skills/meeting-to-video"
    # プロジェクトスコープ（カレントディレクトリ基準）
    ".claude/skills/meeting-to-video"
    ".agents/skills/meeting-to-video"
    # リポジトリから直接実行した場合（開発時）
    "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
  )

  MEETING_TO_VIDEO_SKILL_DIR=""
  for _dir in "${_candidates[@]}"; do
    if [[ -d "$_dir/scripts" ]]; then
      MEETING_TO_VIDEO_SKILL_DIR="$_dir"
      break
    fi
  done

  unset _candidates _dir
fi

if [[ -z "$MEETING_TO_VIDEO_SKILL_DIR" ]]; then
  echo "ERROR: meeting-to-video スキルが見つかりません。" >&2
  echo "  インストール方法: npx skills add 53able/skills --skill meeting-to-video -g" >&2
  echo "  または MEETING_TO_VIDEO_SKILL_DIR 環境変数でパスを直接指定できます。" >&2
  exit 1
fi

export MEETING_TO_VIDEO_SKILL_DIR
