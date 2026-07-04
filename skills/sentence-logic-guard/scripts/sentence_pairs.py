#!/usr/bin/env python3
"""Extract adjacent sentence pairs from Japanese/English prose for coherence review."""
import argparse
import json
import re
import sys
from pathlib import Path

BOUNDARY = re.compile(r'(?<=[。！？!?\.])\s+|(?<=[。！？!?\.])(?=[「『（\(A-Za-z0-9一-龥ぁ-んァ-ン])')


def read_text(path: str | None) -> str:
    if path:
        p = Path(path)
        if not p.exists():
            print(f"ERROR: input file not found: {path}", file=sys.stderr)
            sys.exit(2)
        return p.read_text(encoding="utf-8")
    return sys.stdin.read()


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r'\s+', ' ', text.strip())
    if not cleaned:
        return []
    parts = [s.strip() for s in BOUNDARY.split(cleaned) if s.strip()]
    return parts


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract adjacent sentence pairs for logic continuity review.")
    ap.add_argument("input", nargs="?", help="UTF-8 text/markdown file. Reads stdin when omitted.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    args = ap.parse_args()

    text = read_text(args.input)
    sentences = split_sentences(text)
    pairs = [
        {"index": i + 1, "previous": sentences[i], "next": sentences[i + 1]}
        for i in range(max(0, len(sentences) - 1))
    ]

    if args.json:
        print(json.dumps({"sentence_count": len(sentences), "pairs": pairs}, ensure_ascii=False, indent=2))
    else:
        print(f"Sentence count: {len(sentences)}")
        if not pairs:
            print("No adjacent sentence pairs found.")
        for pair in pairs:
            print(f"\n## Pair {pair['index']}")
            print(f"PREV: {pair['previous']}")
            print(f"NEXT: {pair['next']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
