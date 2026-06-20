#!/usr/bin/env python3
"""Lightweight structure checker for Markdown literate-programming drafts."""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = ["問題", "制約", "方針", "実装", "検証"]
CODE_FENCE_RE = re.compile(r"^```", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Markdown literate-programming draft for basic structure.")
    parser.add_argument("path", help="Path to a Markdown document")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    if path.suffix.lower() not in {".md", ".markdown"}:
        print(f"ERROR: expected a Markdown file, got: {path.suffix}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    warnings = []

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^#+\s+.*{re.escape(heading)}", text, re.MULTILINE):
            warnings.append(f"missing heading containing '{heading}'")

    fence_count = len(CODE_FENCE_RE.findall(text))
    if fence_count == 0:
        warnings.append("no fenced code blocks found")
    elif fence_count % 2 != 0:
        warnings.append("unbalanced fenced code blocks")

    if not re.search(r"(未実行|TODO: run|成功|失敗|passed|failed|not run)", text, re.IGNORECASE):
        warnings.append("verification result/status is not explicit")

    if not re.search(r"(不変条件|invariant|契約|contract)", text, re.IGNORECASE):
        warnings.append("no invariant/contract language found")

    if warnings:
        print("WARN: literate draft has structural issues:")
        for item in warnings:
            print(f"- {item}")
        return 1

    print("OK: literate draft contains the expected narrative, code, and verification structure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
