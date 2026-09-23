#!/usr/bin/env python3
"""Validate the minimum structure of an AI interface design review."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## 1. 結論",
    "## 2. 対象と前提",
    "## 3. リスク階層",
    "## 4. 五段階の状態設計",
    "## 5. 主要な設計判断",
    "## 6. 権限・承認・共有制御",
    "## 7. 信頼・倫理・アクセシビリティ",
    "## 8. 検証シナリオ",
    "## 9. 受入条件",
    "## 10. 未検証事項と次の一歩",
]

FORBIDDEN_PATTERNS = {
    "未解決のTODO": re.compile(r"\bTODO\b", re.IGNORECASE),
    "ローカル絶対パス": re.compile(
        r"(?<![A-Za-z0-9])/(?:Users|home)/[^\s)`]+"
        r"|(?<![A-Za-z0-9])[A-Za-z]:\\(?:Users|home)\\[^\s)`]+"
    ),
    "未置換プレースホルダー": re.compile(r"\{\{[^{}\n]{1,80}\}\}"),
}


def section(text: str, start: str, end: str | None) -> str:
    start_match = re.search(rf"(?m)^{re.escape(start)}\s*$", text)
    if not start_match:
        return ""
    if end is None:
        return text[start_match.end() :]
    end_match = re.search(rf"(?m)^{re.escape(end)}\s*$", text[start_match.end() :])
    if not end_match:
        return text[start_match.end() :]
    return text[start_match.end() : start_match.end() + end_match.start()]


def validate(path: Path) -> list[str]:
    if not path.exists():
        return [f"ファイルが存在しません: {path}"]
    if not path.is_file():
        return [f"通常ファイルではありません: {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^{re.escape(heading)}\s*$", text):
            errors.append(f"必須見出しがありません: {heading}")

    for label, pattern in FORBIDDEN_PATTERNS.items():
        match = pattern.search(text)
        if match:
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{label}を検出しました（{line}行目）: {match.group(0)}")

    scenario_terms = ["正常系", "誤解系", "誤出力系", "副作用系", "復旧系"]
    scenario_section = section(text, REQUIRED_HEADINGS[7], REQUIRED_HEADINGS[8])
    for term in scenario_terms:
        if term not in scenario_section:
            errors.append(f"検証シナリオがありません: {term}")

    risk_terms = ["R0", "R1", "R2", "R3"]
    risk_section = section(text, REQUIRED_HEADINGS[2], REQUIRED_HEADINGS[3])
    if not any(term in risk_section for term in risk_terms):
        errors.append("リスク階層 R0〜R3 の記載がありません。")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIインターフェース設計／レビューの必須構造を検証します。"
    )
    parser.add_argument("path", type=Path, help="検証するMarkdownファイル")
    args = parser.parse_args()

    errors = validate(args.path)
    if errors:
        print("VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"VALIDATION PASSED: {args.path}")
    print(f"- 必須見出し: {len(REQUIRED_HEADINGS)}")
    print("- 検証シナリオ: 正常系、誤解系、誤出力系、副作用系、復旧系")
    print("- 禁止パターン: なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
