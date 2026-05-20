#!/usr/bin/env python3
"""LLM アプリ設計書向けの軽量キーワード監査。

このスクリプトはヒューリスティックであり、正しさを証明しない。
レビュー対象の抜け漏れ候補を見つけるためだけに使う。
"""
import argparse
import re
import sys
from pathlib import Path

CHECKS = [
    ("structured_intents", [r"intent", r"tool call", r"structured output", r"schema", r"構造化", r"スキーマ"]),
    ("prompt_ownership", [r"prompt", r"system message", r"template", r"プロンプト"]),
    ("context_builder", [r"context", r"thread", r"history", r"retriev", r"コンテキスト", r"履歴"]),
    ("state_history", [r"event", r"state", r"append", r"log", r"状態", r"イベント"]),
    ("pause_resume", [r"pause", r"resume", r"callback", r"webhook", r"再開", r"停止"]),
    ("human_approval", [r"approval", r"human", r"review", r"escalat", r"承認", r"人間"]),
    ("control_flow", [r"retry", r"timeout", r"branch", r"policy", r"再試行", r"ポリシー"]),
    ("compact_errors", [r"error", r"exception", r"retryable", r"redact", r"エラー", r"例外"]),
    ("small_agents", [r"agent", r"handoff", r"scope", r"エージェント", r"責務"]),
    ("triggers", [r"trigger", r"slack", r"email", r"cron", r"webhook", r"トリガ"]),
    ("stateless_reducer", [r"reducer", r"stateless", r"replay", r"idempot", r"リプレイ"]),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM アプリ仕様の信頼性原則カバレッジを軽量監査する")
    parser.add_argument("path", help="監査する text、Markdown、source file のパス")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: ファイルが見つかりません: {path}", file=sys.stderr)
        return 2
    if path.is_dir():
        print(f"ERROR: ファイルを指定してください。ディレクトリが指定されました: {path}", file=sys.stderr)
        return 2

    text = path.read_text(errors="replace").lower()
    print(f"audit_file={path}")
    missing = []
    for name, patterns in CHECKS:
        hits = sum(1 for pat in patterns if re.search(pat, text))
        status = "present" if hits else "missing"
        print(f"{name}: {status} ({hits}/{len(patterns)} signals)")
        if not hits:
            missing.append(name)

    if missing:
        print("MISSING_SIGNALS=" + ",".join(missing), file=sys.stderr)
        return 1
    print("SUCCESS: すべてのヒューリスティック signal group が見つかりました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
