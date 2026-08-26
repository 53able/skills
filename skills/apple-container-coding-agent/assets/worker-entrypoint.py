#!/usr/bin/env python3
"""operator所有のWorker entrypoint。生成evidenceはhost検証が終わるまで未信頼として扱う。"""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

RUN = Path("/run")
WORKSPACE = Path("/workspace")
EVIDENCE = Path("/evidence")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_members(archive: tarfile.TarFile):
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive path: {member.name!r}")
        if member.ischr() or member.isblk() or member.isfifo():
            raise ValueError(f"unsupported archive member: {member.name!r}")
        yield member


def run_git(*args: str, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=WORKSPACE,
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=stdout is None,
    )


def die(message: str, code: int = 2) -> int:
    print(f"ENTRYPOINT ERROR: {message}", file=sys.stderr, flush=True)
    return code


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    home = Path(os.environ.get("HOME", "/tmp/agent-home"))
    try:
        home.mkdir(parents=True, exist_ok=True, mode=0o700)
        home.chmod(0o700)
    except OSError as exc:
        return die(f"private HOME is not writable: {exc}")
    archive_path = RUN / "snapshot.tar"
    contract_path = RUN / "task-contract.json"
    command_path = RUN / "agent-command.json"
    for path in (archive_path, contract_path, command_path):
        if not path.is_file():
            return die(f"required run input is missing: {path}")

    try:
        command_doc = json.loads(command_path.read_text(encoding="utf-8"))
        argv = command_doc["argv"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return die(f"agent-command.json is invalid: {exc}")
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        return die("agent-command.json argv must be a non-empty string array")

    if any(WORKSPACE.iterdir()):
        return die("private workspace is not empty")
    try:
        with tarfile.open(archive_path, "r:") as archive:
            archive.extractall(WORKSPACE, members=safe_members(archive))
    except (OSError, tarfile.TarError, ValueError) as exc:
        return die(f"snapshot extraction failed: {exc}")

    for args in (
        ("init", "--quiet"),
        ("config", "user.name", "Isolated Worker Baseline"),
        ("config", "user.email", "isolated-worker.invalid"),
        ("add", "--all"),
        ("commit", "--quiet", "-m", "isolated baseline"),
    ):
        proc = run_git(*args)
        if proc.returncode != 0:
            return die(f"Git baseline initialization failed at {args[0]}: {proc.stderr.strip()}")
    if run_git("remote").stdout.strip():
        return die("workspace unexpectedly contains a Git remote")

    print(json.dumps({"event": "agent.start", "argv0": argv[0], "started_at": started}), flush=True)
    try:
        agent = subprocess.run(argv, cwd=WORKSPACE, check=False)
        agent_exit = agent.returncode
    except FileNotFoundError:
        return die(f"agent executable not found in image: {argv[0]}", 127)
    except OSError as exc:
        return die(f"agent process could not start: {exc}")

    # 通常のuntracked fileをtextual diffへ含めるため、intent-to-add entryを追加する。
    run_git("add", "-N", "--all")
    patch_path = EVIDENCE / "candidate.patch"
    with patch_path.open("wb") as patch:
        diff = run_git("diff", "--binary", "HEAD", stdout=patch)
    if diff.returncode != 0:
        return die(f"Git diff failed: {diff.stderr.decode('utf-8', 'replace').strip()}")

    status = run_git("status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        return die(f"Git status failed: {status.stderr.strip()}")
    manifest = {
        "schema_version": 1,
        "started_at": started,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "agent_exit": agent_exit,
        "argv0": argv[0],
        "snapshot_sha256": sha256(archive_path),
        "contract_sha256": sha256(contract_path),
        "patch_sha256": sha256(patch_path),
        "git_status_porcelain": status.stdout.splitlines(),
        "trust": "WORKERの自己申告。HOST側で再計算すること",
    }
    (EVIDENCE / "worker-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"event": "agent.exit", "exit_code": agent_exit, "patch_sha256": manifest["patch_sha256"]}), flush=True)
    return agent_exit


if __name__ == "__main__":
    raise SystemExit(main())
