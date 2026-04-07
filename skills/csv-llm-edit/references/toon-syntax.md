# TOON Syntax Quick Reference

TOON (Token-Oriented Object Notation) — saves 30–60% tokens vs JSON for uniform arrays.
Spec: https://github.com/toon-format/spec

---

## Tabular Array (CSV use case)

```
key[N]{field1,field2,field3}:
  value1,value2,value3
  value1,value2,value3
```

- `key`   — array name (e.g. `rows`, `users`, `products`)
- `[N]`   — declared row count; LLMs use this to detect truncation
- `{…}`   — comma-separated field names (declared once)
- Each data line starts with 2-space indent

### Delimiter Variants

| Delimiter | Header | Field separator |
|---|---|---|
| Comma (default) | `key[N]{a,b}:` | `,` |
| Tab | `key[N\t]{a\tb}:` | `\t` |
| Pipe | `key[N\|]{a\|b}:` | `\|` |

Tab delimiter often tokenizes better for text-heavy data.

---

## Quoting Rules

A string value MUST be double-quoted when it:
- is empty (`""`)
- has leading or trailing whitespace
- equals `true`, `false`, or `null`
- starts with `-`
- looks like a number (`42`, `-3.14`, `1e6`)
- contains: `,` `:` `"` `\` `[` `]` `{` `}` newline tab

Otherwise, leave it unquoted.

### Escape Sequences (inside quoted strings)

| Literal | Escape |
|---|---|
| `\` | `\\` |
| `"` | `\"` |
| newline | `\n` |
| carriage return | `\r` |
| tab | `\t` |

---

## Examples

### Simple (3 users, comma delimiter)

```
users[3]{id,name,role}:
  1,Alice,admin
  2,Bob,user
  3,Charlie,user
```

### With quoted values

```
products[2]{sku,name,price}:
  A1,"Widget, Deluxe",9.99
  B2,Gadget,"14.50"
```

### Tab delimiter (fewer tokens for text)

```
logs[2	]{id	level	message}:
  1	error	Connection timeout
  2	warn	Slow query detected
```

---

## Nested Object Context (YAML-style)

When metadata accompanies the tabular data, wrap in a YAML-style root object:

```
context:
  source: crm_export
  exported_at: 2026-04-07
rows[3]{id,name,status}:
  1,Alice,active
  2,Bob,inactive
  3,Carol,active
```

---

## Validation Checklist for LLM Output

- [ ] `[N]` matches the actual number of data rows
- [ ] `{fields}` count matches values per row
- [ ] All quoted strings are properly closed
- [ ] No extra braces, brackets, or colons outside quotes
