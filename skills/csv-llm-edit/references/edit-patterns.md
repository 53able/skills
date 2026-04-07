# CSV Edit Patterns

Common Python transformation patterns for `edit_csv.py --script`.
All snippets operate on `rows` (list[dict[str, str]]) and assign back to `rows`.

---

## Create — Initial Data

Used with `--create "col1,col2"` flag. `rows` starts empty; `fieldnames` is available.

```python
# Populate rows from a hardcoded list
rows = [
    {'id': '1', 'name': 'Alice', 'role': 'admin'},
    {'id': '2', 'name': 'Bob',   'role': 'user'},
]

# Generate N rows programmatically
rows = [{'id': str(i), 'value': str(i * 10)} for i in range(1, 11)]
```

---

## Append — Add Rows to Existing File

Used with `--append` flag. `rows = []` (new rows to add); `existing_rows` is the current file.

```python
# Append a fixed row
rows = [{'id': '6', 'name': 'Frank', 'role': 'user'}]

# Auto-increment id based on existing max
next_id = str(max(int(r['id']) for r in existing_rows) + 1)
rows = [{'id': next_id, 'name': 'Grace', 'role': 'user'}]

# Append only if not already present (upsert-safe insert)
existing_ids = {r['id'] for r in existing_rows}
rows = [r for r in [{'id': '3', 'name': 'Carol', 'role': 'user'}] if r['id'] not in existing_ids]
```

---

## Update by Key

```python
# Update a single field on the row matching a key
rows = [
    {**r, 'role': 'admin'} if r['id'] == '3' else r
    for r in rows
]

# Update multiple fields on rows matching a condition
rows = [
    {**r, 'status': 'inactive', 'score': '0'}
    if r['region'] == 'XX' else r
    for r in rows
]

# Bulk update: apply a mapping table {old_value: new_value}
status_map = {'A': 'active', 'I': 'inactive', 'P': 'pending'}
rows = [{**r, 'status': status_map.get(r['status'], r['status'])} for r in rows]
```

---

## Delete by Key

```python
# Delete a single row by exact key match
rows = [r for r in rows if r['id'] != '3']

# Delete multiple rows by a set of keys
remove_ids = {'3', '5', '7'}
rows = [r for r in rows if r['id'] not in remove_ids]

# Delete rows matching a condition
rows = [r for r in rows if not (r['status'] == 'inactive' and float(r['score']) < 30)]
```

---

## Insert at Specific Position

```python
# Insert a new row after the row with id == '2'
new_row = {'id': '2b', 'name': 'Bob Jr.', 'role': 'user'}
result = []
for r in rows:
    result.append(r)
    if r['id'] == '2':
        result.append(new_row)
rows = result

# Prepend rows (insert at top, after header)
rows = [{'id': '0', 'name': 'System', 'role': 'admin'}] + rows
```

---

## Filter

```python
# Keep rows where column equals a value
rows = [r for r in rows if r['status'] == 'active']

# Keep rows where numeric column passes threshold
rows = [r for r in rows if float(r['score']) >= 80.0]

# Remove rows where column is empty
rows = [r for r in rows if r['email'].strip()]

# Keep rows where column matches a substring
rows = [r for r in rows if 'JP' in r['region']]
```

## Transform Column Values

```python
# Uppercase a column
rows = [{**r, 'name': r['name'].upper()} for r in rows]

# Strip whitespace from all values
rows = [{k: v.strip() for k, v in r.items()} for r in rows]

# Replace empty strings with a default
rows = [{k: (v if v else '—') for k, v in r.items()} for r in rows]

# Normalize phone number format
import re
rows = [{**r, 'phone': re.sub(r'\D', '', r['phone'])} for r in rows]
```

## Add Column

```python
# Concatenate two columns
rows = [{**r, 'full_name': r['first'] + ' ' + r['last']} for r in rows]

# Compute a derived numeric column
rows = [{**r, 'total': str(float(r['qty']) * float(r['price']))} for r in rows]

# Add a constant column
rows = [{**r, 'source': 'import_2026'} for r in rows]

# Add sequential row number
rows = [{**r, 'row_num': str(i + 1)} for i, r in enumerate(rows)]
```

## Remove Column

```python
# Drop a single column
rows = [{k: v for k, v in r.items() if k != 'internal_id'} for r in rows]

# Drop multiple columns
drop = {'internal_id', 'debug_flag', 'tmp_col'}
rows = [{k: v for k, v in r.items() if k not in drop} for r in rows]
```

## Rename Column

```python
# Rename one column
rows = [{('new_name' if k == 'old_name' else k): v for k, v in r.items()} for r in rows]

# Rename multiple columns via mapping
rename_map = {'customerID': 'customer_id', 'Dt': 'date'}
rows = [{rename_map.get(k, k): v for k, v in r.items()} for r in rows]
```

## Sort

```python
# Sort ascending by string column
rows = sorted(rows, key=lambda r: r['name'])

# Sort descending by numeric column
rows = sorted(rows, key=lambda r: float(r['score']), reverse=True)

# Multi-key sort
rows = sorted(rows, key=lambda r: (r['region'], -float(r['score'])))
```

## Deduplicate

```python
# Remove exact duplicates (preserve order)
seen = set()
unique = []
for r in rows:
    key = tuple(r.items())
    if key not in seen:
        seen.add(key)
        unique.append(r)
rows = unique

# Deduplicate by specific column (keep first occurrence)
seen_ids = set()
unique = []
for r in rows:
    if r['id'] not in seen_ids:
        seen_ids.add(r['id'])
        unique.append(r)
rows = unique
```

## Reorder Columns

```python
# Specify desired column order
order = ['id', 'name', 'email', 'created_at']
rows = [{k: r[k] for k in order if k in r} for r in rows]
```

## Split / Sample

```python
# Keep first N rows
rows = rows[:100]

# Keep every Nth row (sampling)
rows = rows[::10]

# Skip header-like rows
rows = [r for r in rows if not r['id'].startswith('#')]
```

## Aggregate (pivot to summary)

```python
# Count by category
from collections import Counter
counts = Counter(r['category'] for r in rows)
rows = [{'category': k, 'count': str(v)} for k, v in counts.most_common()]
```

## Type Coercion / Normalization

```python
# Format date column to ISO 8601
from datetime import datetime
def parse_date(s):
    for fmt in ('%d/%m/%Y', '%m-%d-%Y', '%Y%m%d'):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return s

rows = [{**r, 'date': parse_date(r['date'])} for r in rows]
```
