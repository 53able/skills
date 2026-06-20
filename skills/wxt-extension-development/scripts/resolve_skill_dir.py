#!/usr/bin/env python3
# wxt-extension-development スキルのインストール先ディレクトリを標準出力に書き出す。
# npx skills（vercel-labs/skills）でインストールされたエージェントのグローバルパスを網羅する。
# 参照: https://github.com/vercel-labs/skills README の Supported Agents
#
# 使い方（シェルから）:
#   WXT_SKILL_DIR=$(python3 resolve_skill_dir.py)
#   python3 "$WXT_SKILL_DIR/scripts/inspect-wxt-project.py" /path/to/wxt-project
#
# 優先順位:
#   1. 環境変数 WXT_EXTENSION_DEVELOPMENT_SKILL_DIR が設定されていればそれを使う
#   2. 各エージェントのグローバルスキルディレクトリを順に検索
#   3. プロジェクトスコープのスキルディレクトリを検索
#   4. このスクリプトの1階層上（リポジトリから直接実行した場合）

import os
import sys
from pathlib import Path

SKILL_NAME = "wxt-extension-development"
ENV_VAR = "WXT_EXTENSION_DEVELOPMENT_SKILL_DIR"


def resolve() -> str:
    """スキルディレクトリを解決して返す。見つからない場合は sys.exit する。"""
    env_val = os.environ.get(ENV_VAR, "")
    if env_val and Path(env_val).is_dir():
        return env_val

    home = Path.home()
    candidates = [
        home / ".config/agents/skills" / SKILL_NAME,
        home / ".gemini/antigravity/skills" / SKILL_NAME,
        home / ".augment/skills" / SKILL_NAME,
        home / ".claude/skills" / SKILL_NAME,
        home / ".openclaw/skills" / SKILL_NAME,
        home / ".agents/skills" / SKILL_NAME,
        home / ".codebuddy/skills" / SKILL_NAME,
        home / ".codex/skills" / SKILL_NAME,
        home / ".commandcode/skills" / SKILL_NAME,
        home / ".continue/skills" / SKILL_NAME,
        home / ".snowflake/cortex/skills" / SKILL_NAME,
        home / ".config/crush/skills" / SKILL_NAME,
        home / ".cursor/skills" / SKILL_NAME,
        home / ".deepagents/agent/skills" / SKILL_NAME,
        home / ".factory/skills" / SKILL_NAME,
        home / ".gemini/skills" / SKILL_NAME,
        home / ".copilot/skills" / SKILL_NAME,
        home / ".config/goose/skills" / SKILL_NAME,
        home / ".junie/skills" / SKILL_NAME,
        home / ".iflow/skills" / SKILL_NAME,
        home / ".kilocode/skills" / SKILL_NAME,
        home / ".kiro/skills" / SKILL_NAME,
        home / ".kode/skills" / SKILL_NAME,
        home / ".mcpjam/skills" / SKILL_NAME,
        home / ".vibe/skills" / SKILL_NAME,
        home / ".mux/skills" / SKILL_NAME,
        home / ".config/opencode/skills" / SKILL_NAME,
        home / ".openhands/skills" / SKILL_NAME,
        home / ".pi/agent/skills" / SKILL_NAME,
        home / ".qoder/skills" / SKILL_NAME,
        home / ".qwen/skills" / SKILL_NAME,
        home / ".roo/skills" / SKILL_NAME,
        home / ".trae/skills" / SKILL_NAME,
        home / ".trae-cn/skills" / SKILL_NAME,
        home / ".codeium/windsurf/skills" / SKILL_NAME,
        home / ".zencoder/skills" / SKILL_NAME,
        home / ".neovate/skills" / SKILL_NAME,
        home / ".pochi/skills" / SKILL_NAME,
        home / ".adal/skills" / SKILL_NAME,
        home / ".windsurf/skills" / SKILL_NAME,
        Path(".claude/skills") / SKILL_NAME,
        Path(".agents/skills") / SKILL_NAME,
        Path(__file__).parent.parent.resolve(),
    ]

    for candidate in candidates:
        if (candidate / "scripts").is_dir():
            return str(candidate)

    print(
        f"ERROR: {SKILL_NAME} スキルが見つかりません。\n"
        f"  インストール: npx skills add 53able/skills --skill {SKILL_NAME} -g\n"
        f"  または {ENV_VAR} 環境変数でパスを直接指定できます。",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    print(resolve())
