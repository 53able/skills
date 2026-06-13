#!/usr/bin/env python3
"""Print paragraph candidates with line numbers for role labeling."""
import argparse, pathlib, sys

parser = argparse.ArgumentParser(description="List non-heading Markdown paragraphs for Japanese prose revision.")
parser.add_argument("path", help="Markdown/text file to inspect")
args = parser.parse_args()
path = pathlib.Path(args.path)
if not path.exists():
    print(f"ERROR: file not found: {path}", file=sys.stderr)
    sys.exit(1)
text = path.read_text(encoding="utf-8")
paras = []
start = None
buf = []
for i, line in enumerate(text.splitlines(), 1):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("-") or stripped.startswith("|") or stripped.startswith(">"):
        if buf:
            paras.append((start, " ".join(buf)))
            start = None
            buf = []
        continue
    if start is None:
        start = i
    buf.append(stripped)
if buf:
    paras.append((start, " ".join(buf)))

for idx, (line, para) in enumerate(paras, 1):
    preview = para[:120] + ("…" if len(para) > 120 else "")
    print(f"{idx}\tline {line}\t{preview}")
print(f"TOTAL\t{len(paras)} paragraphs", file=sys.stderr)
