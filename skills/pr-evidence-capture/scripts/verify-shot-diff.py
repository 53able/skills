#!/usr/bin/env python3
#
# verify-shot-diff.py
#
# 目的: 2枚のスクリーンショットが「操作後に取得した別ファイル」であることを
#       sha256 ハッシュで確認する。キャンセル/戻る/閉じる/リセット系の操作は
#       見た目が操作前へ戻り同一ハッシュになりやすいため、エビデンスとして
#       使う前にこのスクリプトで差分の有無を検証する。
#
# 実行方法:
#   python3 ~/.agents/skills/pr-evidence-capture/scripts/verify-shot-diff.py <画像A> <画像B>
#
# 終了コード:
#   0  ... ハッシュ不一致（差分あり。エビデンスとして利用可）
#   1  ... ハッシュ一致（同一。再操作して取り直すこと）
#   2  ... 引数エラー / ファイル不在

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "ERROR: 画像パスを2つ指定してください: verify-shot-diff.py <画像A> <画像B>",
            file=sys.stderr,
        )
        return 2

    paths = tuple(Path(arg) for arg in argv)
    for path in paths:
        if not path.is_file():
            print(f"ERROR: ファイルが見つかりません: {path}", file=sys.stderr)
            return 2

    hash_a = sha256(paths[0])
    hash_b = sha256(paths[1])

    if hash_a == hash_b:
        print(
            "SAME: 同一ハッシュです。操作後の別ファイルである証拠になりません。再操作して取り直してください。",
            file=sys.stderr,
        )
        print(f"  {paths[0]}", file=sys.stderr)
        print(f"  {paths[1]}", file=sys.stderr)
        print(f"  sha256={hash_a}", file=sys.stderr)
        return 1

    print("DIFF: ハッシュが異なります。操作後のエビデンスとして利用できます。")
    print(f"  {paths[0]}  sha256={hash_a}")
    print(f"  {paths[1]}  sha256={hash_b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
