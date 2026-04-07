#!/usr/bin/env python3
# 使い方: python3 scripts/check_load.py [対象ディレクトリ]
# 認知負荷アンチパターンの定量的なシグナルを stdout に出力する

import re
import sys
from pathlib import Path

TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

SOURCE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".go", ".py", ".rb", ".java", ".kt", ".swift"}
INDENT_EXTS = {".ts", ".tsx", ".js", ".jsx", ".go", ".py"}
INHERIT_EXTS = {".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".py", ".rb"}
STATUS_EXTS  = {".ts", ".tsx", ".js", ".jsx", ".go", ".py"}

MAX_HITS = 20

PATTERNS = {
    "A1": (
        "A1: 複雑な条件式",
        SOURCE_EXTS,
        re.compile(r"(\&\&.*\&\&.*\&\&|(\|\|.*){3,})"),
    ),
    "A2": (
        "A2: 深いネスト (if/for が3段以上)",
        INDENT_EXTS,
        re.compile(r"^\s{12,}(if|for|while|switch)\b"),
    ),
    "B1": (
        "B1: 継承 (extends/inherits の連鎖)",
        INHERIT_EXTS,
        re.compile(r"\b(extends|inherits)\b"),
    ),
    "A3": (
        "A3: 数値ステータスコード",
        STATUS_EXTS,
        re.compile(r"(status|code|state)\s*[=:]=?\s*[0-9]+"),
    ),
}


def collect_files(root: Path, exts: set[str]) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.suffix in exts]


def scan_pattern(files: list[Path], pattern: re.Pattern) -> list[str]:
    hits: list[str] = []
    for path in files:
        try:
            for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{path}:{lineno}: {line.rstrip()}")
                    if len(hits) >= MAX_HITS:
                        return hits
        except OSError:
            pass
    return hits


def report_module_ratio(root: Path) -> None:
    files = collect_files(root, {".ts", ".tsx", ".js", ".go", ".py"})
    total_lines = sum(
        len(p.read_text(errors="replace").splitlines())
        for p in files
        if p.stat().st_size > 0
    )
    total_files = len(files)
    print("## B2: ファイル数とコード行数の比率")
    print(f"  ファイル数: {total_files}")
    print(f"  総行数: {total_lines}")
    if total_files > 0:
        ratio = total_lines // total_files
        print(f"  平均行数/ファイル: {ratio}")
        if ratio < 50:
            print("  [要注意] 平均50行未満: 浅いモジュールが多い可能性があります")
    print()


def main() -> None:
    print("=== 認知負荷シグナル レポート ===")
    print(f"対象: {TARGET}")
    print()

    for _key, (label, exts, pattern) in PATTERNS.items():
        print(f"## {label}")
        files = collect_files(TARGET, exts)
        hits = scan_pattern(files, pattern)
        if hits:
            print("\n".join(hits))
        else:
            print("  (検出なし)")
        print()

    report_module_ratio(TARGET)

    print("=== レポート完了 ===")
    print("詳細な診断はスキル同梱の references/anti-patterns.md を参照してください。")


if __name__ == "__main__":
    main()
