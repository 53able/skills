#!/usr/bin/env python3
"""Validate the required sections of a modeless UI review Markdown file."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REQUIRED_HEADINGS = [
    "## 1. 対象と目的",
    "## 2. 観測事実",
    "## 3. 仮定と未検証事項",
    "## 4. モードと中断点",
    "## 5. モードレス化の判断",
    "## 6. 改善案",
    "## 7. 状態と例外",
    "## 8. モーダルを残す根拠",
    "## 9. 検証計画",
    "## 10. 推奨順位",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="モードレスUI設計レビューの必須見出しを検証する"
    )
    parser.add_argument("review", help="検証するMarkdownファイルのパス")
    args = parser.parse_args()

    path = pathlib.Path(args.review)
    if not path.is_file():
        print(
            f"ERROR: レビューファイルが見つかりません: {path}",
            file=sys.stderr,
        )
        return 2

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(
            f"ERROR: UTF-8として読み込めません: {path}",
            file=sys.stderr,
        )
        return 2

    matches = [
        re.search(rf"(?m)^{re.escape(heading)}\s*$", text)
        for heading in REQUIRED_HEADINGS
    ]
    missing = [
        heading for heading, match in zip(REQUIRED_HEADINGS, matches) if match is None
    ]
    if missing:
        print("ERROR: 次の必須見出しがありません:", file=sys.stderr)
        for heading in missing:
            print(f"  - {heading}", file=sys.stderr)
        print(
            "assets/modeless-ui-review-template.md の構造に合わせて修正してください。",
            file=sys.stderr,
        )
        return 1

    positions = [match.start() for match in matches if match is not None]
    if positions != sorted(positions):
        print(
            "ERROR: 必須見出しの順序がテンプレートと一致しません。",
            file=sys.stderr,
        )
        return 1

    print(f"SUCCESS: 必須見出しと順序を確認しました: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
