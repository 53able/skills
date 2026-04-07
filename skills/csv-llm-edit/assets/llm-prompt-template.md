# LLM Prompt Template for CSV-via-TOON Tasks

Substitute `{toon_block}` and `{task}` before sending.

---

## Template A: Return Modified TOON

Use when asking the LLM to filter, enrich, or transform rows and return the result.

```
The data below is in TOON format (2-space indent, arrays show [count] and {fields}).

```toon
{toon_block}
```

Task: {task}

Return ONLY the modified data as a TOON code block using the same header format.
Set [N] to match the actual row count in your output.
Do not include any explanation outside the code block.
```

---

## Template B: Return Python Code

Use when asking the LLM to produce a transformation script (to be executed by edit_csv.py).

```
The CSV has the following structure (shown as TOON for brevity):

```toon
{toon_block}
```

Task: {task}

Write a Python snippet that operates on `rows` (list[dict[str, str]]) and assigns
the result back to `rows`. Use only the Python standard library.
Return ONLY the Python code block with no explanation.
```

---

## Template C: Batch Processing

Use when the CSV is large and you need the LLM to process it in chunks.
Replace `{batch_number}` and `{total_batches}` accordingly.

```
Processing batch {batch_number} of {total_batches}.
Each batch is in TOON format (2-space indent, arrays show [count] and {fields}).

```toon
{toon_block}
```

Task: {task}

Return ONLY this batch's result as TOON with the same header format and correct [N].
```

---

## Tips

- For text-heavy data, consider generating TOON with `--delimiter tab` to save additional tokens.
- Add `--rows-start N --rows-end M` to `csv_to_toon.py` to slice large files into manageable batches.
- Always validate LLM TOON output with `toon_to_csv.py` before trusting row counts.
- If the LLM consistently mis-formats TOON, switch to Template B (Python code) instead.
