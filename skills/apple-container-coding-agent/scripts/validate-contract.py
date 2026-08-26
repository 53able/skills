#!/usr/bin/env python3
"""Apple Containerで実行するcoding agentのtask contractを検証する。"""

import argparse
import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
MEMORY = re.compile(r"^[1-9][0-9]*(?:K|M|G|T|P)$")
PATH_ESCAPE = re.compile(r"(^|/)\.\.(/|$)")


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Contract validation failed with {len(errors)} error(s).", file=sys.stderr)
    return 2


def nonempty_strings(value: object, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty array of strings")
        return []
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field}[{index}] must be a non-empty string")
        else:
            result.append(item)
    return result


def safe_relative_path(value: str) -> bool:
    return bool(value) and not value.startswith(("/", "~")) and not PATH_ESCAPE.search(value)


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["document root must be a JSON object"]

    for field in ("task_id", "goal"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string")

    baseline = data.get("baseline_commit")
    if not isinstance(baseline, str) or not SHA40.fullmatch(baseline):
        errors.append("baseline_commit must be a lowercase 40-character Git SHA")

    paths = nonempty_strings(data.get("in_scope_paths"), "in_scope_paths", errors)
    for path in paths:
        if not safe_relative_path(path):
            errors.append(f"in_scope_paths contains unsafe relative path: {path!r}")

    for field in ("out_of_scope", "constraints", "escalate_if"):
        nonempty_strings(data.get(field), field, errors)

    acceptance = data.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance:
        errors.append("acceptance must be a non-empty array")
    else:
        for index, check in enumerate(acceptance):
            if not isinstance(check, dict):
                errors.append(f"acceptance[{index}] must be an object")
                continue
            argv = check.get("argv")
            if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
                errors.append(f"acceptance[{index}].argv must be a non-empty string array")
            expected = check.get("expected_exit")
            if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0 or expected > 255:
                errors.append(f"acceptance[{index}].expected_exit must be an integer from 0 to 255")

    budget = data.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
    else:
        for field, minimum, maximum in (("wall_seconds", 1, 86400), ("cpus", 1, 32), ("retries", 0, 3)):
            value = budget.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
                errors.append(f"budget.{field} must be an integer from {minimum} to {maximum}")
        memory = budget.get("memory")
        if not isinstance(memory, str) or not MEMORY.fullmatch(memory):
            errors.append("budget.memory must use Apple Container syntax such as 4G or 2048M")

    network = data.get("network")
    if not isinstance(network, dict):
        errors.append("network must be an object")
    else:
        mode = network.get("mode")
        if mode not in ("none", "restricted"):
            errors.append("network.mode must be 'none' or 'restricted'")
        hosts = network.get("allowed_hosts")
        if not isinstance(hosts, list) or any(not isinstance(x, str) or not x for x in hosts):
            errors.append("network.allowed_hosts must be an array of non-empty strings")
        elif mode == "none" and hosts:
            errors.append("network.allowed_hosts must be empty when network.mode is 'none'")
        elif mode == "restricted" and not hosts:
            errors.append("network.allowed_hosts must be non-empty when network.mode is 'restricted'")

    allowed = data.get("snapshot_allow_sensitive_paths", [])
    if not isinstance(allowed, list) or any(not isinstance(x, str) or not safe_relative_path(x) for x in allowed):
        errors.append("snapshot_allow_sensitive_paths must be an array of safe relative paths")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.contract.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fail([f"contract does not exist: {args.contract}"])
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return fail([f"contract is not readable valid UTF-8 JSON: {exc}"])
    errors = validate(data)
    if errors:
        return fail(errors)
    print(f"Contract is valid: {args.contract}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
