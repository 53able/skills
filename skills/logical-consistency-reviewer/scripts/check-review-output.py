#!/usr/bin/env python3
import argparse
import pathlib
import sys

REQUIRED_MARKERS = [
    "論理整合性レビュー",
    "論点",
    "論理構造",
    "指摘",
    "修正",
]


def main():
    parser = argparse.ArgumentParser(description="論理整合性レビューに必要なセクションが含まれているか確認する。")
    parser.add_argument("path", help="確認対象のMarkdownレビュー文書")
    args = parser.parse_args()

    path = pathlib.Path(args.path)
    if not path.exists():
        print(f"エラー: ファイルが見つからない: {path}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing:
        print("エラー: 必須のレビュー項目が不足している: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("成功: 論理整合性レビューに必要なセクションが含まれている。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
