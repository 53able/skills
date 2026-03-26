#!/bin/bash
# resolve-skill-dir.sh
#
# meeting-to-video スキルのインストール先ディレクトリを返す。
# npx skills（vercel-labs/skills）でインストールされたエージェントのグローバルパスを網羅する。
# 参照: https://github.com/vercel-labs/skills README の Supported Agents
#
# 使い方（他スクリプトから source して使う）:
#   source "$(dirname "${BASH_SOURCE[0]}")/resolve-skill-dir.sh"
#   echo "$MEETING_TO_VIDEO_SKILL_DIR"
#
# 優先順位:
#   1. 環境変数 MEETING_TO_VIDEO_SKILL_DIR が設定されていればそれを使う
#   2. 各エージェントのグローバルスキルディレクトリを順に検索
#   3. プロジェクトスコープのスキルディレクトリを検索
#   4. このスクリプトの1階層上（リポジトリから直接実行した場合）

if [[ -n "${MEETING_TO_VIDEO_SKILL_DIR:-}" && -d "$MEETING_TO_VIDEO_SKILL_DIR" ]]; then
  : # 環境変数の値をそのまま使う
else
  # グローバルパスは vercel-labs/skills の Supported Agents 表に準拠（2025-03 時点）
  _candidates=(
    "$HOME/.config/agents/skills/meeting-to-video"
    "$HOME/.gemini/antigravity/skills/meeting-to-video"
    "$HOME/.augment/skills/meeting-to-video"
    "$HOME/.claude/skills/meeting-to-video"
    "$HOME/.openclaw/skills/meeting-to-video"
    "$HOME/.agents/skills/meeting-to-video"
    "$HOME/.codebuddy/skills/meeting-to-video"
    "$HOME/.codex/skills/meeting-to-video"
    "$HOME/.commandcode/skills/meeting-to-video"
    "$HOME/.continue/skills/meeting-to-video"
    "$HOME/.snowflake/cortex/skills/meeting-to-video"
    "$HOME/.config/crush/skills/meeting-to-video"
    "$HOME/.cursor/skills/meeting-to-video"
    "$HOME/.deepagents/agent/skills/meeting-to-video"
    "$HOME/.factory/skills/meeting-to-video"
    "$HOME/.gemini/skills/meeting-to-video"
    "$HOME/.copilot/skills/meeting-to-video"
    "$HOME/.config/goose/skills/meeting-to-video"
    "$HOME/.junie/skills/meeting-to-video"
    "$HOME/.iflow/skills/meeting-to-video"
    "$HOME/.kilocode/skills/meeting-to-video"
    "$HOME/.kiro/skills/meeting-to-video"
    "$HOME/.kode/skills/meeting-to-video"
    "$HOME/.mcpjam/skills/meeting-to-video"
    "$HOME/.vibe/skills/meeting-to-video"
    "$HOME/.mux/skills/meeting-to-video"
    "$HOME/.config/opencode/skills/meeting-to-video"
    "$HOME/.openhands/skills/meeting-to-video"
    "$HOME/.pi/agent/skills/meeting-to-video"
    "$HOME/.qoder/skills/meeting-to-video"
    "$HOME/.qwen/skills/meeting-to-video"
    "$HOME/.roo/skills/meeting-to-video"
    "$HOME/.trae/skills/meeting-to-video"
    "$HOME/.trae-cn/skills/meeting-to-video"
    "$HOME/.codeium/windsurf/skills/meeting-to-video"
    "$HOME/.zencoder/skills/meeting-to-video"
    "$HOME/.neovate/skills/meeting-to-video"
    "$HOME/.pochi/skills/meeting-to-video"
    "$HOME/.adal/skills/meeting-to-video"
    "$HOME/.windsurf/skills/meeting-to-video"
    ".claude/skills/meeting-to-video"
    ".agents/skills/meeting-to-video"
    "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
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
  echo "  インストール: npx skills add 53able/skills --skill meeting-to-video -g" >&2
  echo "  または MEETING_TO_VIDEO_SKILL_DIR 環境変数でパスを直接指定できます。" >&2
  exit 1
fi

export MEETING_TO_VIDEO_SKILL_DIR
