#!/usr/bin/env python3
"""仕様マップに必要なトレーサビリティ項目が含まれるか検証する。"""
import argparse
import pathlib
import sys

REQUIRED_HEADINGS = [
    "## スコープ",
    "## 観察された振る舞い",
    "## 推定された振る舞い",
    "## 未確認の振る舞い",
    "## プリミティブ能力マップ",
    "## 置き換え設計",
    "## 検証ログ",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="プリミティブ再実装用の仕様マップを検証する。")
    parser.add_argument("path", help="仕様マップMarkdownファイルへのパス")
    args = parser.parse_args()

    path = pathlib.Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    if missing:
        print("ERROR: missing required sections: " + ", ".join(missing), file=sys.stderr)
        return 1

    if "未確認" not in text:
        print("ERROR: map must explicitly account for 未確認 behavior", file=sys.stderr)
        return 1

    print(f"SUCCESS: {path} contains required primitive reimplementation sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
