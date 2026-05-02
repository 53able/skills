#!/usr/bin/env python3
"""余計な認知負荷のシグナルをヒューリスティックに走査する。

意図的に保守的にしている。レビューに値するテキストパターンを報告するが、
コードが誤りかどうかは決めない。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    category: str
    message: str
    line: str


PATTERNS = (
    (
        "control-flow",
        re.compile(r"if\s+.*(&&|\|\|).*(\(|&&|\|\|)"),
        "複雑な条件式は名前付きの中間事実が必要かもしれない",
    ),
    (
        "abstraction",
        re.compile(r"\bextends\b|:\s*public\s+\w+"),
        "継承は祖先・子孫の確認が必要",
    ),
    (
        "abstraction",
        re.compile(r"\bFactoryFactory\b|\bManagerManager\b|\bHelperHelper\b"),
        "名前から浅い／偶然の抽象の可能性",
    ),
    (
        "protocol-mapping",
        re.compile(r"\b(401|403|404|409|418|500)\b.*(expired|banned|permission|role|plan|quota)", re.IGNORECASE),
        "トランスポートステータスに業務固有の意味が載っている可能性",
    ),
    (
        "architecture",
        re.compile(r"\b(port|adapter|repository|usecase|interactor)\b", re.IGNORECASE),
        "アーキレイヤー用語は有用か装飾か要確認",
    ),
)


def iter_files(path: Path) -> tuple[Path, ...]:
    if path.is_file():
        return (path,)

    return tuple(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in TEXT_EXTENSIONS
        and ".git" not in file_path.parts
        and "node_modules" not in file_path.parts
    )


def scan_file(path: Path) -> tuple[Finding, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return ()

    findings = []
    for index, line in enumerate(lines, start=1):
        stripped_line = line.strip()
        for category, pattern, message in PATTERNS:
            if pattern.search(stripped_line):
                findings.append(
                    Finding(
                        path=path,
                        line_number=index,
                        category=category,
                        message=message,
                        line=stripped_line[:160],
                    )
                )

    return tuple(findings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="余計な認知負荷のヒューリスティックシグナルをファイルから走査する。"
    )
    parser.add_argument("--path", required=True, help="走査するファイルまたはディレクトリ。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_path = Path(args.path).expanduser().resolve()

    if not root_path.exists():
        print(f"エラー: パスが存在しません: {root_path}", file=sys.stderr)
        return 2

    findings = tuple(
        finding
        for file_path in iter_files(root_path)
        for finding in scan_file(file_path)
    )

    if not findings:
        print("ヒューリスティック上、認知負荷のシグナルは見つかりませんでした。")
        return 0

    for finding in findings:
        print(
            f"{finding.path}:{finding.line_number}: "
            f"[{finding.category}] {finding.message}: {finding.line}"
        )

    print(f"\n指摘件数: {len(findings)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
