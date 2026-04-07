#!/usr/bin/env python3
# meeting-to-video スキルのインストール先ディレクトリを標準出力に書き出す。
# npx skills（vercel-labs/skills）でインストールされたエージェントのグローバルパスを網羅する。
# 参照: https://github.com/vercel-labs/skills README の Supported Agents
#
# 使い方（シェルから）:
#   MEETING_TO_VIDEO_SKILL_DIR=$(python3 resolve_skill_dir.py)
#   python3 "$MEETING_TO_VIDEO_SKILL_DIR/scripts/setup.py" <output-dir>
#
# 使い方（Python スクリプト内で直接インポート）:
#   from resolve_skill_dir import resolve
#   skill_dir = resolve()
#
# 優先順位:
#   1. 環境変数 MEETING_TO_VIDEO_SKILL_DIR が設定されていればそれを使う
#   2. 各エージェントのグローバルスキルディレクトリを順に検索
#   3. プロジェクトスコープのスキルディレクトリを検索
#   4. このスクリプトの1階層上（リポジトリから直接実行した場合）

import os
import sys
from pathlib import Path


def resolve() -> str:
    """スキルディレクトリを解決して返す。見つからない場合は sys.exit する。"""
    env_val = os.environ.get("MEETING_TO_VIDEO_SKILL_DIR", "")
    if env_val and Path(env_val).is_dir():
        return env_val

    home = Path.home()
    # グローバルパスは vercel-labs/skills の Supported Agents 表に準拠
    candidates = [
        home / ".config/agents/skills/meeting-to-video",
        home / ".gemini/antigravity/skills/meeting-to-video",
        home / ".augment/skills/meeting-to-video",
        home / ".claude/skills/meeting-to-video",
        home / ".openclaw/skills/meeting-to-video",
        home / ".agents/skills/meeting-to-video",
        home / ".codebuddy/skills/meeting-to-video",
        home / ".codex/skills/meeting-to-video",
        home / ".commandcode/skills/meeting-to-video",
        home / ".continue/skills/meeting-to-video",
        home / ".snowflake/cortex/skills/meeting-to-video",
        home / ".config/crush/skills/meeting-to-video",
        home / ".cursor/skills/meeting-to-video",
        home / ".deepagents/agent/skills/meeting-to-video",
        home / ".factory/skills/meeting-to-video",
        home / ".gemini/skills/meeting-to-video",
        home / ".copilot/skills/meeting-to-video",
        home / ".config/goose/skills/meeting-to-video",
        home / ".junie/skills/meeting-to-video",
        home / ".iflow/skills/meeting-to-video",
        home / ".kilocode/skills/meeting-to-video",
        home / ".kiro/skills/meeting-to-video",
        home / ".kode/skills/meeting-to-video",
        home / ".mcpjam/skills/meeting-to-video",
        home / ".vibe/skills/meeting-to-video",
        home / ".mux/skills/meeting-to-video",
        home / ".config/opencode/skills/meeting-to-video",
        home / ".openhands/skills/meeting-to-video",
        home / ".pi/agent/skills/meeting-to-video",
        home / ".qoder/skills/meeting-to-video",
        home / ".qwen/skills/meeting-to-video",
        home / ".roo/skills/meeting-to-video",
        home / ".trae/skills/meeting-to-video",
        home / ".trae-cn/skills/meeting-to-video",
        home / ".codeium/windsurf/skills/meeting-to-video",
        home / ".zencoder/skills/meeting-to-video",
        home / ".neovate/skills/meeting-to-video",
        home / ".pochi/skills/meeting-to-video",
        home / ".adal/skills/meeting-to-video",
        home / ".windsurf/skills/meeting-to-video",
        Path(".claude/skills/meeting-to-video"),
        Path(".agents/skills/meeting-to-video"),
        Path(__file__).parent.parent.resolve(),
    ]

    for candidate in candidates:
        if (candidate / "scripts").is_dir():
            return str(candidate)

    print(
        "ERROR: meeting-to-video スキルが見つかりません。\n"
        "  インストール: npx skills add 53able/skills --skill meeting-to-video -g\n"
        "  または MEETING_TO_VIDEO_SKILL_DIR 環境変数でパスを直接指定できます。",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    print(resolve())
