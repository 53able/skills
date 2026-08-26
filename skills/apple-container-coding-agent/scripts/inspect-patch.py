#!/usr/bin/env python3
"""未信頼patchをquarantine cloneへ適用し、path／file type policyを検査する。"""

import argparse
import fnmatch
import json
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

PROTECTED_PATTERNS = (
    ".github/workflows/*", ".gitlab-ci.yml", "Jenkinsfile", "Dockerfile*", "Containerfile*",
    ".gitmodules", ".gitattributes", ".claude/*", ".codex/*", ".pi/*", ".mcp.json",
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock",
    "requirements*.txt", "pyproject.toml", "Cargo.lock", "go.sum",
)


def git(cwd: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(cwd), "-c", "core.hooksPath=/dev/null", *args],
        capture_output=True,
        check=False,
        text=text,
    )


def path_in_scope(path: str, scopes: list[str]) -> bool:
    normalized = path.rstrip("/")
    for scope in scopes:
        root = scope.rstrip("/")
        if normalized == root or normalized.startswith(root + "/"):
            return True
    return False


def unsafe_path(path: str) -> bool:
    item = PurePosixPath(path)
    return path.startswith(("/", "~")) or ".." in item.parts or "\x00" in path


def emit(report: dict, output: Path | None) -> None:
    body = json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
    print(body, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        patch_bytes = args.patch.read_bytes()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: input is unreadable: {exc}", file=sys.stderr)
        return 2
    if not patch_bytes:
        print("ERROR: patch is empty", file=sys.stderr)
        return 2

    scopes = contract.get("in_scope_paths")
    if not isinstance(scopes, list) or not scopes:
        print("ERROR: contract has no in_scope_paths; validate it first", file=sys.stderr)
        return 2

    violations: list[str] = []
    observations: list[str] = []
    changed: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="patch-quarantine-") as temp_name:
        temp = Path(temp_name)
        clone = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(args.repo.resolve()), str(temp / "repo")],
            capture_output=True,
            check=False,
            text=True,
        )
        if clone.returncode != 0:
            print(f"ERROR: quarantine clone failed: {clone.stderr.strip()}", file=sys.stderr)
            return 2
        quarantine = temp / "repo"
        checkout = git(quarantine, "checkout", "--quiet", "--detach", args.baseline)
        if checkout.returncode != 0:
            print("ERROR: baseline does not resolve in quarantine clone", file=sys.stderr)
            return 2
        apply_check = git(quarantine, "apply", "--check", "--index", str(args.patch.resolve()))
        if apply_check.returncode != 0:
            print(f"ERROR: git apply --check --index rejected patch: {apply_check.stderr.strip()}", file=sys.stderr)
            return 2
        applied = git(quarantine, "apply", "--index", str(args.patch.resolve()))
        if applied.returncode != 0:
            print(f"ERROR: patch application failed after check: {applied.stderr.strip()}", file=sys.stderr)
            return 2

        names = git(quarantine, "diff", "--cached", "--name-status", "-z", text=False)
        if names.returncode != 0:
            print("ERROR: cannot enumerate changed paths", file=sys.stderr)
            return 2
        fields = names.stdout.split(b"\x00")
        index = 0
        while index < len(fields) and fields[index]:
            status = fields[index].decode("utf-8", "surrogateescape")
            index += 1
            count = 2 if status.startswith(("R", "C")) else 1
            paths = [fields[index + i].decode("utf-8", "surrogateescape") for i in range(count)]
            index += count
            for path in paths:
                changed.append({"status": status, "path": path})
                if unsafe_path(path):
                    violations.append(f"unsafe path: {path}")
                if not path_in_scope(path, scopes):
                    violations.append(f"out-of-scope path: {path}")
                if any(fnmatch.fnmatch(path, pattern) for pattern in PROTECTED_PATTERNS):
                    violations.append(f"protected path requires manual review: {path}")

        staged = git(quarantine, "ls-files", "-s", "-z", text=False)
        if staged.returncode != 0:
            print("ERROR: cannot inspect staged file modes", file=sys.stderr)
            return 2
        changed_paths = {entry["path"] for entry in changed}
        for record in staged.stdout.split(b"\x00"):
            if not record:
                continue
            meta, raw_path = record.split(b"\t", 1)
            mode = meta.split(b" ", 1)[0].decode("ascii")
            path = raw_path.decode("utf-8", "surrogateescape")
            if path in changed_paths and mode in ("120000", "160000"):
                violations.append(f"symlink or gitlink requires manual review: {path} ({mode})")

        numstat = git(quarantine, "diff", "--cached", "--numstat")
        for line in numstat.stdout.splitlines():
            added, deleted, path = line.split("\t", 2)
            if added == "-" or deleted == "-":
                violations.append(f"binary change requires manual review: {path}")

        summary = git(quarantine, "diff", "--cached", "--summary")
        for line in summary.stdout.splitlines():
            if "mode change" in line or "create mode 100755" in line:
                violations.append(f"executable or mode change requires manual review: {line.strip()}")

        observations.append("Patch parsed and applied with Git in a detached quarantine clone.")
        observations.append("No hooks were executed by this inspection workflow.")

    report = {
        "schema_version": 1,
        "baseline": args.baseline,
        "patch": str(args.patch),
        "changed": changed,
        "violations": sorted(set(violations)),
        "observations": observations,
        "disposition": "MANUAL_REVIEW_REQUIRED" if violations else "ELIGIBLE_FOR_CLEAN_REVALIDATION",
    }
    emit(report, args.report)
    if violations:
        print(f"Patch policy found {len(set(violations))} violation(s).", file=sys.stderr)
        return 3
    print("Patch passed structural policy; clean tests are still required.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
