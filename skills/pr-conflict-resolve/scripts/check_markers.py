#!/usr/bin/env python3
# Usage: python scripts/check_markers.py
# ステージ済みファイルにgitコンフリクトマーカーが残っていないかをスキャンする。
# クリーンなら exit 0、マーカーが見つかれば対象ファイルを stderr に出力して exit 1。

import subprocess
import sys
from pathlib import Path

MARKERS = ("<<<<<<< ", "=======", ">>>>>>> ")


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def find_markers_in_file(path: Path) -> list[str]:
    try:
        content = path.read_text(errors="replace")
        return [m for m in MARKERS if m in content]
    except OSError:
        return []


def main() -> None:
    staged = get_staged_files()

    if not staged:
        print("ステージ済みファイルがありません。", file=sys.stderr)
        sys.exit(0)

    detected: dict[str, list[str]] = {}
    for filename in staged:
        found = find_markers_in_file(Path(filename))
        if found:
            detected[filename] = found

    if detected:
        for filename, markers in detected.items():
            for marker in markers:
                print(
                    f"コンフリクトマーカー検出: {filename} （'{marker.strip()}' が残存）",
                    file=sys.stderr,
                )
        print(
            "コミットする前にすべてのコンフリクトマーカーを解消してください。",
            file=sys.stderr,
        )
        sys.exit(1)

    print("OK: ステージ済みファイルにコンフリクトマーカーは検出されませんでした。")


main()
