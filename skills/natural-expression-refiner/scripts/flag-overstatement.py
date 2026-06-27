#!/usr/bin/env python3
"""Flag likely overstatement / under-grounded expressions in Japanese prose.

Usage:
  python3 scripts/flag-overstatement.py path/to/text.md
"""
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    ("誇張・絶対化", r"世界を変|革命|圧倒的|唯一無二|最高|完全|完璧|すべての人|誰もが|必ず|絶対に|劇的|飛躍的"),
    ("借り物の美辞麗句", r"かけがえのない|心を動かす|新たな価値|未来を創る|可能性を広げる|寄り添う|伴走|挑戦し続ける"),
    ("曖昧な絶賛", r"素晴らしい|すごい|魅力的|画期的|革新的|本質的|深い|大切な|重要な"),
    ("過剰な謙遜", r"まだまだ未熟|たいしたこと(?:は|では)ない|恐縮ですが|僭越ながら|素人なりに|ただの"),
    ("根拠要求", r"成果を出し|成功し|改善し|解決し|成長し|実現し|達成し"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag likely non-grounded expressions.")
    parser.add_argument("file", help="UTF-8 text or markdown file to inspect")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings = []
    for idx, line in enumerate(lines, start=1):
        labels = [label for label, pattern in PATTERNS if re.search(pattern, line)]
        if labels:
            findings.append((idx, ", ".join(labels), line.strip()))

    if not findings:
        print("OK: no obvious overstatement candidates found.")
        return 0

    print(f"FOUND: {len(findings)} candidate line(s). Review context before rewriting.")
    for line_no, label, line in findings:
        print(f"{line_no}: {label}: {line}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
