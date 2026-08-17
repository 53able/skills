#!/usr/bin/env python3
"""Presentation First Article Workbenchの必須構造を検査する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = [
    "## 1. 記事ブリーフ",
    "## 2. 証拠パック",
    "## 3. ナラティブ・デッキ",
    "## 4. スピーカーノート",
    "## 5. 記事本文",
    "## Sources",
    "## 6. 監査ログ",
]

REQUIRED_FIELDS = [
    "想定読者",
    "読者が困っていること",
    "記事が約束する変化",
    "中心主張",
    "撤回・限定条件",
]


def field_value(text: str, label: str) -> str | None:
    match = re.search(
        rf"^- \*\*{re.escape(label)}:\*\*\s*(.*)$", text, flags=re.MULTILINE
    )
    return match.group(1).strip() if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="検査するMarkdownファイル")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"ERROR: ファイルが見つかりません: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"必須見出しがありません: {heading}")

    for label in REQUIRED_FIELDS:
        value = field_value(text, label)
        if value is None:
            errors.append(f"記事ブリーフの項目がありません: {label}")
        elif not value or value in {"TODO", "TBD", "未定"}:
            errors.append(f"記事ブリーフの項目が空です: {label}")

    deck_match = re.search(
        r"^## 3\. ナラティブ・デッキ\s*$\n(.*?)(?=^## 4\. スピーカーノート\s*$)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    deck = deck_match.group(1) if deck_match else ""
    beats = re.findall(r"^### Beat\s+\d+", deck, flags=re.MULTILINE)
    claims = re.findall(r"^- \*\*主張:\*\*\s*(.*)$", deck, flags=re.MULTILINE)
    if not beats:
        errors.append("ナラティブ・デッキにBeatがありません")
    if not any(value.strip() for value in claims):
        errors.append("ナラティブ・デッキに空でない主張がありません")

    evidence_ids = set(re.findall(r"\bE-\d{2,}\b", text))
    if not evidence_ids:
        errors.append("証拠IDがありません。E-01の形式で追加してください")

    if "{{" in text or "}}" in text:
        errors.append("テンプレートのプレースホルダー{{...}}が残っています")
    if "https://example.com/" in text:
        errors.append("Sourcesに例示URLが残っています")
    if re.search(r"\|\s*BLOCKER\s*\|.*\|\s*open\s*\|", text, flags=re.IGNORECASE):
        errors.append("未解消のBLOCKERが監査ログに残っています")
    if re.search(r"\b(unverified|blocked|未検証)\b", text, flags=re.IGNORECASE):
        warnings.append("未検証またはblockedの項目があります")
    if not re.findall(r'https?://[^\s)>"\]]+', text):
        warnings.append("直接URLがありません。外部主張があればSourcesへ追加してください")

    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warnings:
        print(f"WARNING: {message}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)}件のエラー、{len(warnings)}件の警告", file=sys.stderr)
        return 1

    print(
        f"SUCCESS: 必須構造を確認しました（Beat {len(beats)}件、証拠ID {len(evidence_ids)}件、警告 {len(warnings)}件）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
