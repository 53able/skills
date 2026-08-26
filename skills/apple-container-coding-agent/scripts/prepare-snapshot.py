#!/usr/bin/env python3
"""変更不能なtracked-file snapshotとhost-side provenanceを作成する。"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SENSITIVE_NAMES = {
    ".env", ".npmrc", ".pypirc", ".netrc", ".git-credentials",
    "credentials", "credentials.json", "service-account.json",
}
SENSITIVE_PARTS = {".ssh", ".aws", ".gnupg", ".kube"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def run_git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null", *args],
        check=False,
        capture_output=True,
        text=text,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sensitive(path: str) -> bool:
    item = PurePosixPath(path)
    return (
        item.name in SENSITIVE_NAMES
        or any(part in SENSITIVE_PARTS for part in item.parts)
        or item.suffix.lower() in SENSITIVE_SUFFIXES
    )


def error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--agent-command", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    out = args.out.resolve()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        command_doc = json.loads(args.agent_command.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return error(f"cannot read contract or agent command: {exc}")
    argv = command_doc.get("argv") if isinstance(command_doc, dict) else None
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        return error("agent-command.json argv must be a non-empty string array")

    baseline = contract.get("baseline_commit")
    if not isinstance(baseline, str):
        return error("contract baseline_commit is missing; run validate-contract.py first")

    top = run_git(repo, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return error(f"not a Git repository: {repo}")
    repo = Path(top.stdout.strip()).resolve()

    resolved = run_git(repo, "rev-parse", f"{baseline}^{{commit}}")
    if resolved.returncode != 0 or resolved.stdout.strip() != baseline:
        return error("baseline_commit does not resolve to the exact commit in the repository")

    status = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        return error("git status failed")
    if status.stdout:
        return error("working tree is not clean; commit/stash changes or use a separate clean clone")

    listed = run_git(repo, "ls-tree", "-r", "--name-only", baseline)
    if listed.returncode != 0:
        return error("cannot enumerate baseline tree")
    tracked_paths = [line for line in listed.stdout.splitlines() if line]
    allowed = set(contract.get("snapshot_allow_sensitive_paths", []))
    flagged = [path for path in tracked_paths if is_sensitive(path) and path not in allowed]
    if flagged:
        preview = ", ".join(flagged[:12])
        suffix = " ..." if len(flagged) > 12 else ""
        return error(
            "snapshot contains sensitive-looking tracked paths: " + preview + suffix
            + ". Remove them or explicitly list reviewed paths in snapshot_allow_sensitive_paths."
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return error(f"output directory already exists: {out}")

    with tempfile.TemporaryDirectory(prefix="agent-snapshot-", dir=str(out.parent)) as temp_name:
        temp = Path(temp_name)
        archive = temp / "snapshot.tar"
        with archive.open("wb") as handle:
            proc = subprocess.run(
                ["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null", "archive", "--format=tar", baseline],
                stdout=handle,
                stderr=subprocess.PIPE,
                check=False,
            )
        if proc.returncode != 0:
            return error(f"git archive failed: {proc.stderr.decode('utf-8', 'replace').strip()}")

        canonical_contract = temp / "task-contract.json"
        canonical_contract.write_text(
            json.dumps(contract, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        canonical_command = temp / "agent-command.json"
        canonical_command.write_text(
            json.dumps(command_doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        provenance = {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "repo_basename": repo.name,
            "baseline_commit": baseline,
            "tracked_path_count": len(tracked_paths),
            "snapshot_sha256": sha256(archive),
            "contract_sha256": sha256(canonical_contract),
            "agent_command_sha256": sha256(canonical_command),
            "agent_argv0": argv[0],
            "git_version": run_git(repo, "--version").stdout.strip(),
            "host_platform": os.uname().sysname + " " + os.uname().release,
            "notes": [
                "Snapshot contains tracked files from baseline only; .git and untracked files are absent.",
                "Sensitive-path detection is name-based and is not a content secret scan."
            ],
        }
        (temp / "provenance.json").write_text(
            json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.rename(out)

    print(f"Prepared immutable run input: {out}")
    print(f"Snapshot SHA-256: {provenance['snapshot_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
