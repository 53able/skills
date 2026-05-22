#!/usr/bin/env python3
"""Zenn Markdown のよくある違反を検出する。

Usage:
  python3 scripts/validate-zenn-markdown.py path/to/article.md
  python3 scripts/validate-zenn-markdown.py path/to/articles/**/*.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MERMAID_MAX_CHARS = 2000
MERMAID_MAX_AMP_CHAINS = 10
FENCE_RE = re.compile(r"^```(\w*.*?)?\s*$")


def iter_mermaid_blocks(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    in_block = False
    start_line = 0
    buf: list[str] = []

    for idx, line in enumerate(lines, start=1):
        if not in_block:
            m = FENCE_RE.match(line.strip())
            if m and m.group(1) and m.group(1).split()[0] == "mermaid":
                in_block = True
                start_line = idx
                buf = []
            continue

        if line.strip().startswith("```"):
            blocks.append((start_line, "\n".join(buf)))
            in_block = False
            buf = []
        else:
            buf.append(line)

    return blocks


def count_amp_chains(mermaid_body: str) -> int:
    return len(re.findall(r"&", mermaid_body))


def check_math_blank_lines(text: str) -> list[str]:
    issues: list[str] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped != "$$":
            continue
        prev_blank = idx == 0 or lines[idx - 1].strip() == ""
        next_blank = idx + 1 >= len(lines) or lines[idx + 1].strip() == ""
        if not prev_blank or not next_blank:
            issues.append(
                f"L{idx + 1}: $$ block should have blank lines before and after"
            )
    return issues


def check_h1_in_body(text: str) -> list[str]:
    warnings: list[str] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if line.startswith("# ") and not line.startswith("## "):
            warnings.append(
                f"L{idx}: H1 (# ) in body — prefer ## for accessibility on Zenn"
            )
    return warnings


def check_multiline_html_comments(text: str) -> list[str]:
    issues: list[str] = []
    if "<!--" in text:
        for match in re.finditer(r"<!--([\s\S]*?)-->", text):
            inner = match.group(1)
            if "\n" in inner:
                line = text[: match.start()].count("\n") + 1
                issues.append(
                    f"L{line}: multi-line HTML comments are not supported on Zenn"
                )
    return issues


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for start, body in iter_mermaid_blocks(text):
        if len(body) > MERMAID_MAX_CHARS:
            errors.append(
                f"L{start}: mermaid block exceeds {MERMAID_MAX_CHARS} chars "
                f"({len(body)} chars)"
            )
        amp_count = count_amp_chains(body)
        if amp_count > MERMAID_MAX_AMP_CHAINS:
            errors.append(
                f"L{start}: mermaid & chain count {amp_count} exceeds "
                f"{MERMAID_MAX_AMP_CHAINS}"
            )

    errors.extend(check_math_blank_lines(text))
    errors.extend(check_multiline_html_comments(text))
    warnings.extend(check_h1_in_body(text))

    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    paths = [Path(p) for p in argv[1:]]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        for p in missing:
            print(f"ERROR: file not found: {p}", file=sys.stderr)
        return 1

    total_errors = 0
    total_warnings = 0

    for path in paths:
        errors, warnings = validate_file(path)
        if not errors and not warnings:
            print(f"OK: {path}")
            continue

        print(f"--- {path} ---")
        for msg in errors:
            print(f"ERROR: {msg}", file=sys.stderr)
            total_errors += 1
        for msg in warnings:
            print(f"WARN: {msg}")
            total_warnings += 1

    if total_errors:
        print(
            f"\nFailed: {total_errors} error(s), {total_warnings} warning(s)",
            file=sys.stderr,
        )
        return 1

    print(f"\nPassed with {total_warnings} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
