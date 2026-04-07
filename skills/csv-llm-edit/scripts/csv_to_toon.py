#!/usr/bin/env python3
"""
csv_to_toon.py — Convert a CSV file to TOON tabular format for token-efficient LLM input.

Usage:
  python scripts/csv_to_toon.py <input.csv> [options]

Options:
  --key NAME        Array key name in TOON header (default: rows)
  --encoding ENC    File encoding (default: utf-8)
  --rows-start N    First row index to include, 0-based (default: 0)
  --rows-end N      Last row index exclusive (default: all rows)
  --delimiter CHAR  TOON output delimiter: comma | tab | pipe (default: comma)

Output: TOON block printed to stdout.
Errors: printed to stderr with non-zero exit code.

# Run: python scripts/csv_to_toon.py sample.csv --key users
"""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Sequence


_TOON_DELIMITERS = {"comma": ",", "tab": "\t", "pipe": "|"}

_SPECIAL_CHARS_COMMA = set(':"\\[]{}\n\r\t,')
_SPECIAL_CHARS_TAB = set(':"\\[]{}\n\r\t')
_SPECIAL_CHARS_PIPE = set(':"\\[]{}\n\r\t|')

_RESERVED_TOKENS = frozenset({"true", "false", "null"})


def _needs_quoting(value: str, delimiter: str) -> bool:
    """Determine whether a string value requires TOON quoting."""
    if not value or value != value.strip():
        return True
    if value in _RESERVED_TOKENS:
        return True
    if value.startswith("-"):
        return True
    try:
        float(value)
        return True
    except ValueError:
        pass
    specials = (
        _SPECIAL_CHARS_COMMA if delimiter == ","
        else _SPECIAL_CHARS_TAB if delimiter == "\t"
        else _SPECIAL_CHARS_PIPE
    )
    return bool(set(value) & specials)


def _quote(value: str) -> str:
    """Wrap value in double quotes with TOON escape sequences."""
    escaped = (
        value
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _encode_value(value: str, delimiter: str) -> str:
    """Encode a single CSV string value as a TOON field."""
    if _needs_quoting(value, delimiter):
        return _quote(value)
    return value


def csv_to_toon(
    rows: list[dict[str, str]],
    key: str,
    delimiter: str,
) -> str:
    """Encode a uniform list of dicts (CSV rows) as a TOON tabular block."""
    if not rows:
        return f"{key}[0]:"

    fields = list(rows[0].keys())
    n = len(rows)
    sep = delimiter

    header_delim = "" if delimiter == "," else (
        "\\t" if delimiter == "\t" else "|"
    )
    field_sep = sep if delimiter != "," else ","
    field_header = field_sep.join(fields)

    header = f"{key}[{n}{header_delim}]{{{field_header}}}:"
    toon_lines = [header]

    for row in rows:
        values = [_encode_value(row.get(f, ""), delimiter) for f in fields]
        toon_lines.append("  " + sep.join(values))

    return "\n".join(toon_lines)


def _load_csv(path: str, encoding: str) -> list[dict[str, str]]:
    try:
        with open(path, newline="", encoding=encoding) as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(
            f"Error: cannot decode '{path}' with encoding '{encoding}': {e}\n"
            "Hint: retry with --encoding latin-1 or --encoding shift-jis",
            file=sys.stderr,
        )
        sys.exit(1)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to TOON tabular format."
    )
    parser.add_argument("input", help="Path to the input CSV file")
    parser.add_argument(
        "--key", default="rows", help="TOON array key name (default: rows)"
    )
    parser.add_argument(
        "--encoding", default="utf-8", help="File encoding (default: utf-8)"
    )
    parser.add_argument(
        "--rows-start", type=int, default=0, help="First row index, 0-based"
    )
    parser.add_argument(
        "--rows-end", type=int, default=None, help="Last row index (exclusive)"
    )
    parser.add_argument(
        "--delimiter",
        choices=["comma", "tab", "pipe"],
        default="comma",
        help="TOON output delimiter (default: comma)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)

    all_rows = _load_csv(args.input, args.encoding)
    rows = all_rows[args.rows_start : args.rows_end]

    if not rows:
        print(
            f"Warning: no rows selected (total={len(all_rows)}, "
            f"start={args.rows_start}, end={args.rows_end})",
            file=sys.stderr,
        )

    delimiter = _TOON_DELIMITERS[args.delimiter]
    toon_output = csv_to_toon(rows, key=args.key, delimiter=delimiter)
    print(toon_output)


if __name__ == "__main__":
    main()
