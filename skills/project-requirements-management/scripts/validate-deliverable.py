#!/usr/bin/env python3
"""Validate the minimum structure of project requirements management artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = {
    "requirements": [
        "事業課題",
        "事業目標と成功条件",
        "範囲",
        "ステークホルダーと決定権",
        "要求一覧",
        "未解決事項",
        "検証記録",
    ],
    "baseline": [
        "識別",
        "対象要求",
        "除外・先送り要求",
        "前提・制約・リスク",
        "実装・検証の準備状況",
        "合意",
    ],
    "change": ["識別", "変更内容", "影響評価", "選択肢と推奨", "決定"],
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate required headings in a requirements-management Markdown artifact."
    )
    parser.add_argument("kind", choices=REQUIRED_HEADINGS, help="Artifact type to validate.")
    parser.add_argument("path", type=Path, help="Path to the Markdown artifact.")
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"ERROR: File not found: {args.path}", file=sys.stderr)
        return 2

    try:
        text = args.path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"ERROR: File is not UTF-8 text: {args.path}", file=sys.stderr)
        return 2

    missing = [
        heading
        for heading in REQUIRED_HEADINGS[args.kind]
        if not re.search(rf"^##(?:\s+\d+\.)?\s+{re.escape(heading)}\s*$", text, re.MULTILINE)
    ]
    if missing:
        print(
            "ERROR: Missing required level-2 headings for "
            f"{args.kind}: {', '.join(missing)}. "
            "Copy the matching template from assets/ and complete the missing sections.",
            file=sys.stderr,
        )
        return 1

    if text.count("|") < 4:
        print(
            "ERROR: No usable Markdown table was found. "
            "Use the matching template so decisions and requirements remain reviewable.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {args.path} contains the required {args.kind} structure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
