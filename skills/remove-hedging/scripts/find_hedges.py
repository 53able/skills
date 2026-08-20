#!/usr/bin/env python3
"""文章から定型的な保留表現の確認候補を抽出する。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("状況依存", re.compile(r"状況(?:次第|により|によって)|状況によります")),
    ("一般化回避", re.compile(r"一概には(?:言え|いえ)ません|一概に(?:言え|いえ)ない")),
    ("可能性", re.compile(r"可能性が(?:あり|ある|考えられ)ます?|かもしれません|かもしれない")),
    ("非必然", re.compile(r"必ずしも.+?(?:ではありません|ではない)")),
    ("環境依存", re.compile(r"環境によって(?:は)?.+?(?:異な|変わ|動作しない|期待どおり)")),
    ("結果依存", re.compile(r"結果が異なる(?:可能性があります|ことがあります|場合があります)")),
    ("英語の状況依存", re.compile(r"\bit depends\b", re.IGNORECASE)),
    ("英語の可能性", re.compile(r"\b(?:may|might|could)\b", re.IGNORECASE)),
    ("英語の非必然", re.compile(r"\bnot necessarily\b", re.IGNORECASE)),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UTF-8テキストから定型的な保留表現を検出します。"
    )
    parser.add_argument("input", help="確認するUTF-8テキストファイル")
    parser.add_argument(
        "--fail-on-match",
        action="store_true",
        help="候補を1件以上検出した場合に終了コード2を返します。",
    )
    return parser.parse_args()


def read_text(path_text: str) -> str:
    path = Path(path_text)
    if not path.exists():
        raise ValueError(f"入力ファイルが存在しません: {path}")
    if not path.is_file():
        raise ValueError(f"入力パスはファイルではありません: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"UTF-8として読めません: {path}（位置 {exc.start}）"
        ) from exc
    except OSError as exc:
        raise ValueError(f"入力ファイルを読めません: {path}: {exc}") from exc


def find_candidates(text: str) -> list[tuple[int, str, str]]:
    candidates: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                candidates.append((line_number, label, line.strip()))
    return candidates


def main() -> int:
    args = parse_args()
    try:
        text = read_text(args.input)
    except ValueError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    candidates = find_candidates(text)
    if not candidates:
        print("保留表現の定型候補は見つかりませんでした。構造的な保留は目視確認してください。")
        return 0

    print(f"保留表現の確認候補を{len(candidates)}件検出しました。")
    for line_number, label, line in candidates:
        print(f"{line_number}: [{label}] {line}")
    print("各候補を削除・変換・維持・確認のいずれかに分類してください。")
    return 2 if args.fail_on_match else 0


if __name__ == "__main__":
    raise SystemExit(main())
