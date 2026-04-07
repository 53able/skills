---
name: csv-llm-edit
description: Edits CSV files using Python and converts tabular data to TOON format for token-efficient LLM processing. Use when editing CSV files programmatically, filtering or transforming tabular data, passing CSV data to LLMs with minimal token cost, or building LLM pipelines that process structured CSV records. Don't use for non-CSV formats (JSON, XML, Parquet), real-time streaming data sources, or tasks where the CSV file itself never needs LLM involvement.
---

# CSV LLM Edit

Python-based CSV editing with TOON conversion for token-efficient LLM calls.

TOON (Token-Oriented Object Notation) is a compact format that saves 30–60% tokens compared to JSON
by declaring field names once and streaming rows as compact CSV-like lines.

## Step 1: Determine the Workflow

Choose a workflow based on the task:

- **Workflow A (Python-only)**: The edit logic is deterministic (create, append, filter, update, delete, sort, etc.) → Go to **Step 2A**.
- **Workflow B (LLM-assisted)**: The edit requires language understanding or generation (classify, extract entities, enrich values, etc.) → Go to **Step 2B**.

---

## Workflow A: Python-Only CSV CRUD

### A-0: Select the CRUD Mode

| Goal | Mode flag | Command shape |
|---|---|---|
| Create new CSV from scratch | `--create "col1,col2"` | `edit_csv.py <new.csv> --create "..."` |
| Append rows to existing CSV | `--append` | `edit_csv.py <target.csv> --append --script "..."` |
| Read / inspect | `--preview` | `edit_csv.py <input.csv> --preview` |
| Update / filter / transform | *(default)* | `edit_csv.py <input.csv> <output.csv> --script "..."` |
| Delete rows | *(default)* | `edit_csv.py <input.csv> <output.csv> --script "..."` |

---

**Step 2A-1: Inspect the CSV** (Read)

```bash
python scripts/edit_csv.py <input.csv> --preview
```

Prints column names, total row count, and first 5 rows.

---

**Step 2A-2: Create a new CSV** (Create)

```bash
# Empty file with headers only
python scripts/edit_csv.py new.csv --create "id,name,role"

# With initial data via --script
python scripts/edit_csv.py new.csv --create "id,name,role" \
  --script "rows = [{'id':'1','name':'Alice','role':'admin'}]"
```

---

**Step 2A-3: Append rows** (Create — row level)

```bash
# Append a fixed row
python scripts/edit_csv.py data.csv --append \
  --script "rows = [{'id':'6','name':'Frank','role':'user'}]"

# Auto-increment id from existing data
python scripts/edit_csv.py data.csv --append \
  --script "next_id = str(max(int(r['id']) for r in existing_rows) + 1); rows = [{'id': next_id, 'name': 'Grace', 'role': 'user'}]"
```

In `--append` mode: `rows = []` (new rows to produce); `existing_rows` holds the current file content.

---

**Step 2A-4: Transform, filter, or delete rows** (Update / Delete)

Read `references/edit-patterns.md` to find the matching pattern (Update by key, Delete by key, Insert at position, etc.).

```bash
python scripts/edit_csv.py <input.csv> <output.csv> --script "<python_code>"
```

For multi-line scripts, write the code to a file first:

```bash
python scripts/edit_csv.py <input.csv> <output.csv> --script-file /tmp/transform.py
```

---

**Step 2A-5: Verify**

```bash
python scripts/edit_csv.py <output.csv> --preview
```

Confirm row count and column values match expectations.

---

## Workflow B: LLM-Assisted CSV Editing

**Step 2B-1: Convert CSV to TOON**

```bash
python scripts/csv_to_toon.py <input.csv> [--key <array_key>] [--rows-start N] [--rows-end M]
```

- `--key` sets the array name in the TOON header (default: `rows`)
- `--rows-start` / `--rows-end` enables batch processing for large files

Capture the stdout output (the TOON block).

**Step 2B-2: Build the LLM Prompt**

Read `assets/llm-prompt-template.md` and substitute:
- `{toon_block}` — the TOON output captured above
- `{task}` — the edit instruction in natural language

**Step 2B-3: Send to LLM**

Send the assembled prompt to the LLM. The model returns one of:
- Modified TOON data → proceed to **Step 2B-4A**
- Python transformation code → proceed to **Step 2B-4B**

**Step 2B-4A: TOON Response → CSV**

```bash
echo "<toon_output>" | python scripts/toon_to_csv.py --output <output.csv>
# or from a file:
python scripts/toon_to_csv.py --input response.toon --output <output.csv>
```

**Step 2B-4B: Python Code Response → CSV**

```bash
python scripts/edit_csv.py <input.csv> <output.csv> --script "<python_code_from_llm>"
```

**Step 2B-5: Verify**

```bash
python scripts/edit_csv.py <output.csv> --preview
```

---

## Error Handling

| Error | Cause | Fix |
|---|---|---|
| `UnicodeDecodeError` in `csv_to_toon.py` | Non-UTF-8 file | Add `--encoding latin-1` or `--encoding shift-jis` |
| `Row count mismatch` in `toon_to_csv.py` | LLM truncated the output | Re-prompt with smaller batch using `--rows-start` / `--rows-end` |
| `KeyError: 'column_name'` in `edit_csv.py` | Wrong column name | Run with `--preview` to check exact column names |
| `SyntaxError` in `edit_csv.py` | Invalid Python in `--script` | Check quoting; prefer `--script-file` for complex code |
| TOON decode fails | Non-uniform rows (nested objects) | LLM returned JSON instead; parse with `python -c "import json, sys; ..."` |
