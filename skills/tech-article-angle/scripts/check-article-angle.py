#!/usr/bin/env python3
import argparse
import re
import sys

REQUIRED_CONCEPTS = {
    "reader": [r"読者", r"対象", r"誰に", r"エンジニア", r"チーム", r"開発者"],
    "pain": [r"課題", r"痛み", r"困", r"壊", r"摩擦", r"不安", r"リスク"],
    "promise": [r"できる", r"分かる", r"判断", r"設計", r"改善", r"学べ"],
    "evidence": [r"実測", r"Before", r"After", r"設定", r"ログ", r"数", r"検証", r"TODO: collect evidence"],
    "transfer": [r"再利用", r"応用", r"持ち帰", r"別の.*チーム", r"チェックリスト", r"手順"],
}


def found_any(text, patterns):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def main():
    parser = argparse.ArgumentParser(description="Check whether a technical article draft contains core reader-value elements.")
    parser.add_argument("--file", required=True, help="Markdown file to check.")
    args = parser.parse_args()

    try:
        text = open(args.file, "r", encoding="utf-8").read()
    except Exception as exc:
        print(f"ERROR: cannot read file: {exc}", file=sys.stderr)
        return 2

    missing = [name for name, patterns in REQUIRED_CONCEPTS.items() if not found_any(text, patterns)]
    headings = len(re.findall(r"^#{1,3}\s+", text, flags=re.MULTILINE))

    if headings < 3:
        missing.append("structure_headings")

    if missing:
        print("FAIL: missing or weak elements: " + ", ".join(missing), file=sys.stderr)
        return 1

    print("PASS: draft contains reader, pain, promise, evidence path, transfer lesson, and basic structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
