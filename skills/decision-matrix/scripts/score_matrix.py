#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path


def load_json(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    criteria = data.get("criteria", [])
    options = data.get("options", [])
    if not criteria or not options:
        raise ValueError("JSON must contain non-empty criteria and options arrays")
    weights = {c["name"]: float(c.get("weight", 1.0)) for c in criteria}
    rows = []
    for opt in options:
        name = opt["name"]
        scores = {k: float(v) for k, v in opt.get("scores", {}).items()}
        rows.append({"option": name, "scores": scores})
    return list(weights.keys()), weights, rows


def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
    if len(reader) < 3:
        raise ValueError("CSV must have header, weight row, and at least one option row")
    header = reader[0]
    if not header or header[0] != "option":
        raise ValueError("CSV first header must be 'option'")
    criteria = header[1:]
    if reader[1][0] != "weight":
        raise ValueError("CSV second row first cell must be 'weight'")
    weights = {c: float(w) for c, w in zip(criteria, reader[1][1:])}
    rows = []
    for raw in reader[2:]:
        if not raw or not raw[0].strip():
            continue
        scores = {c: float(v) for c, v in zip(criteria, raw[1:])}
        rows.append({"option": raw[0], "scores": scores})
    if not rows:
        raise ValueError("CSV must contain at least one option row")
    return criteria, weights, rows


def compute(criteria, weights, rows):
    out = []
    for row in rows:
        total = 0.0
        weighted = {}
        for c in criteria:
            score = float(row["scores"].get(c, 0))
            value = score * weights[c]
            weighted[c] = value
            total += value
        out.append({"option": row["option"], "scores": row["scores"], "weighted": weighted, "total": total})
    return sorted(out, key=lambda x: x["total"], reverse=True)


def print_markdown(criteria, weights, results):
    header = ["順位", "選択肢"] + [f"{c} (×{weights[c]:g})" for c in criteria] + ["合計"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for i, r in enumerate(results, 1):
        cells = [str(i), r["option"]]
        for c in criteria:
            cells.append(f'{r["scores"].get(c, 0):g}')
        cells.append(f'{r["total"]:g}')
        print("| " + " | ".join(cells) + " |")


def main():
    parser = argparse.ArgumentParser(description="Score a weighted decision matrix from JSON or CSV.")
    parser.add_argument("--input", required=True, help="Path to matrix JSON or CSV")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    path = Path(args.input)
    try:
        if path.suffix.lower() == ".json":
            criteria, weights, rows = load_json(path)
        elif path.suffix.lower() == ".csv":
            criteria, weights, rows = load_csv(path)
        else:
            raise ValueError("Input must end with .json or .csv")
        results = compute(criteria, weights, rows)
        if args.output == "json":
            print(json.dumps({"criteria": criteria, "weights": weights, "results": results}, ensure_ascii=False, indent=2))
        else:
            print_markdown(criteria, weights, results)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
