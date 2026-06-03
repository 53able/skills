#!/usr/bin/env python3
"""
context-to-gantt/scripts/extract-tasks.py

Validates a Gantt JSON file against gantt-data-schema.json.
Execution: python3 scripts/extract-tasks.py --input path/to/gantt.json

Exit 0  = valid
Exit 1  = validation error (stderr)
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


def _parse_date(s: str, field: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        print(f"DATE ERROR: '{field}' value '{s}' is not a valid ISO date (YYYY-MM-DD).", file=sys.stderr)
        sys.exit(1)


def validate(data: dict) -> list[str]:
    errors: list[str] = []

    if "title" not in data or not isinstance(data["title"], str):
        errors.append("MISSING FIELD: 'title' must be a non-empty string.")

    groups = data.get("groups")
    if not groups or not isinstance(groups, list):
        errors.append("MISSING FIELD: 'groups' must be a non-empty array.")
        return errors

    valid_colors = {"blue", "green", "orange", "purple", "red", "gray"}
    valid_statuses = {"todo", "in-progress", "done", "blocked"}

    for gi, group in enumerate(groups):
        prefix = f"groups[{gi}]"
        if not group.get("id"):
            errors.append(f"{prefix}: missing 'id'.")
        if not group.get("name"):
            errors.append(f"{prefix}: missing 'name'.")
        tasks = group.get("tasks")
        if not tasks or not isinstance(tasks, list):
            errors.append(f"{prefix}: 'tasks' must be a non-empty array.")
            continue

        for ti, task in enumerate(tasks):
            tp = f"{prefix}.tasks[{ti}]"
            if not task.get("id"):
                errors.append(f"{tp}: missing 'id'.")
            if not task.get("name"):
                errors.append(f"{tp}: missing 'name'.")

            start_str = task.get("startDate")
            end_str = task.get("endDate")
            if not start_str:
                errors.append(f"{tp}: missing 'startDate'.")
            if not end_str:
                errors.append(f"{tp}: missing 'endDate'.")
            if start_str and end_str:
                start = _parse_date(start_str, f"{tp}.startDate")
                end = _parse_date(end_str, f"{tp}.endDate")
                if end < start:
                    errors.append(f"{tp}: 'endDate' ({end_str}) must be >= 'startDate' ({start_str}).")

            color = task.get("color")
            if color and color not in valid_colors:
                errors.append(f"{tp}: 'color' must be one of {sorted(valid_colors)}, got '{color}'.")

            status = task.get("status")
            if status and status not in valid_statuses:
                errors.append(f"{tp}: 'status' must be one of {sorted(valid_statuses)}, got '{status}'.")

    for mi, marker in enumerate(data.get("markers", [])):
        mp = f"markers[{mi}]"
        if not marker.get("date"):
            errors.append(f"{mp}: missing 'date'.")
        else:
            _parse_date(marker["date"], f"{mp}.date")
        if not marker.get("label"):
            errors.append(f"{mp}: missing 'label'.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Gantt JSON data.")
    parser.add_argument("--input", required=True, help="Path to gantt JSON file")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"FILE ERROR: '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"JSON ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate(data)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    total_tasks = sum(len(g.get("tasks", [])) for g in data.get("groups", []))
    print(f"SUCCESS: Valid Gantt data — {len(data['groups'])} group(s), {total_tasks} task(s).")
    sys.exit(0)


if __name__ == "__main__":
    main()
