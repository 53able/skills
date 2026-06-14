#!/usr/bin/env python3
import argparse
import json
import sys

CRITERIA = ["reader_pain", "timeliness", "evidence_path", "transferability", "specificity"]


def main():
    parser = argparse.ArgumentParser(description="Score technical article angle candidates from JSON.")
    parser.add_argument("--input", required=True, help="JSON file with a list of candidates.")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"ERROR: cannot read JSON: {exc}", file=sys.stderr)
        return 2

    candidates = data.get("candidates") if isinstance(data, dict) else data
    if not isinstance(candidates, list):
        print("ERROR: input must be a list or an object with candidates list", file=sys.stderr)
        return 2

    ok = True
    for i, cand in enumerate(candidates, 1):
        if not isinstance(cand, dict):
            print(f"ERROR: candidate {i} is not an object", file=sys.stderr)
            ok = False
            continue
        title = cand.get("title") or cand.get("angle") or f"candidate-{i}"
        scores = cand.get("scores", {})
        if not isinstance(scores, dict):
            print(f"ERROR: {title}: scores must be an object", file=sys.stderr)
            ok = False
            continue
        total = 0
        missing = []
        invalid = []
        for criterion in CRITERIA:
            value = scores.get(criterion)
            if value is None:
                missing.append(criterion)
                continue
            if not isinstance(value, int) or not 0 <= value <= 3:
                invalid.append(criterion)
                continue
            total += value
        verdict = "PASS" if total >= 11 and not missing and not invalid else "REVISE"
        print(f"{verdict}\t{total}/15\t{title}")
        if missing:
            print(f"  missing: {', '.join(missing)}")
            ok = False
        if invalid:
            print(f"  invalid 0-3 integer scores: {', '.join(invalid)}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
