#!/usr/bin/env python3
"""
edit_csv.py — Full CRUD operations on CSV files via Python transformation scripts.

The script variable `rows` (list[dict[str, str]]) is the working data.
Assign the result back to `rows` to write it out.

MODES
  (default edit)  python scripts/edit_csv.py <input.csv> <output.csv> --script CODE
  --preview       python scripts/edit_csv.py <input.csv> --preview
  --create COLS   python scripts/edit_csv.py <new.csv>  --create "col1,col2,col3"
  --append        python scripts/edit_csv.py <target.csv> --append --script CODE

Options:
  --preview           Print column names and first 5 rows; no output written
  --create COLS       Create a new CSV with the given comma-separated column names
  --append            Append new rows to an existing CSV (rows starts empty;
                      existing_rows holds the current file content for reference)
  --script CODE       Inline Python code operating on `rows`
  --script-file PATH  Path to a .py file operating on `rows`
  --encoding ENC      File encoding (default: utf-8)

Examples:
  # Preview
  python scripts/edit_csv.py data.csv --preview

  # Create empty CSV with headers
  python scripts/edit_csv.py new.csv --create "id,name,role"

  # Create CSV with initial data
  python scripts/edit_csv.py new.csv --create "id,name,role" \
    --script "rows = [{'id':'1','name':'Alice','role':'admin'}]"

  # Append one row
  python scripts/edit_csv.py data.csv --append \
    --script "rows = [{'id':'6','name':'Frank','role':'user'}]"

  # Append rows referencing existing data (auto-increment id)
  python scripts/edit_csv.py data.csv --append \
    --script "next_id = str(max(int(r['id']) for r in existing_rows) + 1); rows = [{'id': next_id, 'name': 'Grace', 'role': 'user'}]"

  # Filter: keep rows where age > 18
  python scripts/edit_csv.py data.csv out.csv \
    --script "rows = [r for r in rows if int(r['age']) > 18]"

  # Update: set status='inactive' where score < 60
  python scripts/edit_csv.py data.csv out.csv \
    --script "rows = [{**r, 'status': 'inactive'} if float(r['score']) < 60 else r for r in rows]"

# Run: python scripts/edit_csv.py input.csv --preview
"""
from __future__ import annotations

import argparse
import csv
import sys
from typing import Sequence


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_csv(path: str, encoding: str) -> tuple[list[dict[str, str]], list[str]]:
    """Return (rows, fieldnames). Exits on file-not-found or decode error."""
    try:
        with open(path, newline="", encoding=encoding) as f:
            reader = csv.DictReader(f)
            rows = [dict(row) for row in reader]
            fieldnames = list(reader.fieldnames or (list(rows[0].keys()) if rows else []))
            return rows, fieldnames
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(
            f"Error: cannot decode '{path}' with encoding '{encoding}': {e}\n"
            "Hint: retry with --encoding latin-1",
            file=sys.stderr,
        )
        sys.exit(1)


def _write_csv(rows: list[dict[str, str]], path: str, fieldnames: list[str]) -> None:
    """Overwrite path with rows. Uses fieldnames from first row if rows is non-empty."""
    effective_fields = list(rows[0].keys()) if rows else fieldnames
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=effective_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(new_rows: list[dict[str, str]], path: str, fieldnames: list[str]) -> None:
    """Append new_rows to path without rewriting the header."""
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerows(new_rows)


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------

def _load_code(args: argparse.Namespace) -> str:
    """Return the transformation code from --script or --script-file."""
    if args.script_file:
        try:
            with open(args.script_file, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: script file not found: {args.script_file}", file=sys.stderr)
            sys.exit(1)
    if args.script:
        return args.script
    print("Error: provide --script CODE or --script-file PATH", file=sys.stderr)
    sys.exit(1)


def _run_script(
    rows: list[dict[str, str]],
    code: str,
    extra: dict | None = None,
) -> list[dict[str, str]]:
    """Execute transformation code. `extra` injects additional names into the namespace."""
    namespace: dict = {"rows": rows, "csv": csv, **(extra or {})}
    try:
        exec(compile(code, "<script>", "exec"), namespace)  # noqa: S102
    except SyntaxError as e:
        print(f"Error: syntax error in script: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: script raised {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    result = namespace.get("rows")
    if not isinstance(result, list):
        print(
            f"Error: script must assign a list[dict] to `rows`, got {type(result).__name__}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def _preview(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    print(f"Columns ({len(fieldnames)}): {fieldnames}")
    print(f"Total rows: {len(rows)}")
    print()
    sample = rows[:5]
    if not sample:
        return
    col_widths = {
        f: max(len(f), max(len(str(r.get(f, ""))) for r in sample))
        for f in fieldnames
    }
    header = " | ".join(f.ljust(col_widths[f]) for f in fieldnames)
    print(header)
    print("-" * len(header))
    for row in sample:
        print(" | ".join(str(row.get(f, "")).ljust(col_widths[f]) for f in fieldnames))


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Full CRUD operations on CSV files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        help=(
            "Input CSV (edit/preview/append mode) "
            "or output path (create mode)"
        ),
    )
    parser.add_argument(
        "output", nargs="?", default=None,
        help="Output CSV path (edit mode only; omit for append/create/preview)",
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Print column names and first 5 rows without writing output",
    )
    parser.add_argument(
        "--create", metavar="COLS",
        help='Create a new CSV with given columns, e.g. "id,name,role"',
    )
    parser.add_argument(
        "--append", action="store_true",
        help=(
            "Append rows produced by --script to the existing CSV. "
            "`rows` starts empty; `existing_rows` holds the current file content."
        ),
    )
    parser.add_argument(
        "--script", default=None,
        help="Inline Python code operating on `rows` (list[dict])",
    )
    parser.add_argument(
        "--script-file", default=None,
        help="Path to a Python script file operating on `rows`",
    )
    parser.add_argument(
        "--encoding", default="utf-8",
        help="Input file encoding (default: utf-8)",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)

    # ---- CREATE mode -------------------------------------------------------
    if args.create:
        fieldnames = [c.strip() for c in args.create.split(",") if c.strip()]
        if not fieldnames:
            print("Error: --create requires at least one column name", file=sys.stderr)
            sys.exit(1)
        rows: list[dict[str, str]] = []
        if args.script or args.script_file:
            code = _load_code(args)
            rows = _run_script([], code, extra={"fieldnames": fieldnames})
        _write_csv(rows, args.path, fieldnames)
        print(
            f"OK: created {args.path} ({len(fieldnames)} columns, {len(rows)} rows)",
            file=sys.stderr,
        )
        return

    # ---- PREVIEW mode ------------------------------------------------------
    if args.preview:
        loaded_rows, fieldnames = _load_csv(args.path, args.encoding)
        _preview(loaded_rows, fieldnames)
        return

    # ---- APPEND mode -------------------------------------------------------
    if args.append:
        existing_rows, fieldnames = _load_csv(args.path, args.encoding)
        code = _load_code(args)
        new_rows = _run_script(
            [],
            code,
            extra={"existing_rows": existing_rows, "fieldnames": fieldnames},
        )
        if not new_rows:
            print("Warning: script produced 0 rows; nothing appended", file=sys.stderr)
            return
        _append_csv(new_rows, args.path, fieldnames)
        print(
            f"OK: appended {len(new_rows)} rows to {args.path} "
            f"(total now {len(existing_rows) + len(new_rows)})",
            file=sys.stderr,
        )
        return

    # ---- EDIT mode (default) -----------------------------------------------
    if not args.script and not args.script_file:
        print("Error: provide --script CODE or --script-file PATH", file=sys.stderr)
        sys.exit(1)
    if not args.output:
        print(
            "Error: output path required for edit mode\n"
            "Hint: for in-place append use --append; for new file use --create",
            file=sys.stderr,
        )
        sys.exit(1)

    loaded_rows, fieldnames = _load_csv(args.path, args.encoding)
    code = _load_code(args)
    result = _run_script(loaded_rows, code)
    _write_csv(result, args.output, fieldnames)
    print(
        f"OK: {len(loaded_rows)} rows → {len(result)} rows → {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
