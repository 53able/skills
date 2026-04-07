#!/usr/bin/env python3
# Usage: python scripts/check_granularity.py
# 現在の差分（ステージ済み＋未ステージ）を分析し、
# コミット粒度の観点から概要レポートを出力する。

import subprocess
import sys

WARN_FILE_THRESHOLD = 10

def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()

def count_lines(output: str) -> int:
    return len([line for line in output.splitlines() if line]) if output else 0

def extract_extensions(filenames: str) -> list[str]:
    return sorted({
        name.rsplit(".", 1)[1]
        for name in filenames.splitlines()
        if name and "." in name.split("/")[-1]
    })

def main() -> None:
    staged_files_raw  = run_git("diff", "--cached", "--name-only")
    unstaged_files_raw = run_git("diff", "--name-only")
    staged_stat       = run_git("diff", "--cached", "--stat")
    stat_summary      = staged_stat.splitlines()[-1] if staged_stat else "（変更なし）"

    staged_count   = count_lines(staged_files_raw)
    unstaged_count = count_lines(unstaged_files_raw)
    extensions     = extract_extensions(staged_files_raw)

    print("=== コミット粒度チェック ===\n")
    print("[ステージ済み]")
    print(f"  変更ファイル数 : {staged_count}")
    print(f"  差分サマリー   : {stat_summary}")
    print()
    print("[未ステージ]")
    print(f"  変更ファイル数 : {unstaged_count}")
    print()
    print(f"[ステージ済みのファイル拡張子] {' '.join(extensions) if extensions else '（なし）'}")
    print()

    if staged_count > WARN_FILE_THRESHOLD:
        print(
            f"WARNING: ステージ済みファイルが {staged_count} 件と多め。\n"
            "         複数の論理グループが混在していないか確認してください。",
            file=sys.stderr,
        )

    deleted_raw = run_git("diff", "--cached", "--diff-filter=D", "--name-only")
    added_raw   = run_git("diff", "--cached", "--diff-filter=A", "--name-only")
    deleted     = count_lines(deleted_raw)
    added       = count_lines(added_raw)

    if deleted > 0 and added > 0:
        print(
            f"INFO: 削除ファイル {deleted} 件 / 追加ファイル {added} 件 が混在しています。\n"
            "      関数の移動が分割されていないか確認してください。"
        )

    print("\n=== チェック完了 ===")

main()
