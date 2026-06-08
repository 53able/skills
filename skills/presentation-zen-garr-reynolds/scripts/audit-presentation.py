#!/usr/bin/env python3
"""Tiny Presentation Zen markdown auditor.

Checks a markdown outline or slide draft for common risks:
- likely slideuments
- dense bullet runs
- very long lines
- missing audience/change framing
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a markdown presentation outline for Presentation Zen risks.")
    ap.add_argument("path", help="Markdown file to audit")
    ap.add_argument("--max-line", type=int, default=120, help="Long-line threshold")
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    findings: list[tuple[str, str]] = []

    if not re.search(r"(?i)audience|聞き手|聴衆|対象者", text):
        findings.append(("MAJOR", "Audience framing is missing or hard to find."))
    if not re.search(r"(?i)change|action|next step|変化|行動|次の一手|意思決定", text):
        findings.append(("MAJOR", "Desired change or next action is missing or hard to find."))

    bullet_run = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r"^([-*+] |\d+[.)] )", stripped):
            bullet_run += 1
        else:
            if bullet_run >= 6:
                findings.append(("MINOR", f"Dense bullet run of {bullet_run} items ends near line {i-1}."))
            bullet_run = 0
        if len(line) > args.max_line:
            findings.append(("MINOR", f"Line {i} is {len(line)} chars; likely too dense for a slide."))
    if bullet_run >= 6:
        findings.append(("MINOR", f"Dense bullet run of {bullet_run} items ends at file end."))

    word_count = len(re.findall(r"\w+", text))
    heading_count = len(re.findall(r"^#{1,6} ", text, re.M))
    if heading_count and word_count / heading_count > 180:
        findings.append(("MINOR", "Sections are text-heavy; consider separating handout content from projected slides."))

    if findings:
        print("Presentation Zen audit: FINDINGS")
        for sev, msg in findings:
            print(f"- {sev}: {msg}")
        return 1 if any(sev == "MAJOR" for sev, _ in findings) else 0

    print("Presentation Zen audit: PASS")
    print("Audience framing, change framing, and density checks did not flag obvious issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
