#!/usr/bin/env python3
"""検証ケースをApple Containerで隔離・並列実行し、証跡を集約する。"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_VALIDATOR_PATH = Path(__file__).with_name("validate-manifest.py")
_VALIDATOR_SPEC = importlib.util.spec_from_file_location("apple_container_manifest_validator", _VALIDATOR_PATH)
if _VALIDATOR_SPEC is None or _VALIDATOR_SPEC.loader is None:
    raise RuntimeError(f"validatorを読み込めない: {_VALIDATOR_PATH}")
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)
recommended_concurrency = _VALIDATOR.recommended_concurrency
validate_manifest = _VALIDATOR.validate_manifest


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path, exclude: set[Path] | None = None) -> str:
    digest = hashlib.sha256()
    excluded = {path.resolve() for path in (exclude or set())}
    if root.is_file():
        return sha256_file(root)
    for path in sorted(root.rglob("*")):
        resolved = path.resolve()
        if any(resolved == item or item in resolved.parents for item in excluded):
            continue
        relative_path = path.relative_to(root)
        if "__pycache__" in relative_path.parts or path.name in {".DS_Store"} or path.suffix == ".pyc":
            continue
        relative = str(relative_path).encode("utf-8")
        digest.update(relative + b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0" + os.readlink(path).encode("utf-8") + b"\0")
        elif path.is_file():
            digest.update(sha256_file(path).encode("ascii") + b"\0")
    return digest.hexdigest()


def run_capture(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, **kwargs)


def safe_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-") or "job"
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{normalized[:50].rstrip('-')}-{suffix}"[:63]


def redact_command(args: list[str], inherited_names: set[str]) -> list[str]:
    redacted: list[str] = []
    hide_next = False
    for token in args:
        if hide_next:
            key = token.split("=", 1)[0]
            redacted.append(f"{key}=<redacted>" if key in inherited_names else token)
            hide_next = False
        elif token in {"-e", "--env"}:
            redacted.append(token)
            hide_next = True
        else:
            redacted.append(token)
    return redacted


def check_oracle(case: dict[str, Any], exit_code: int | None, timed_out: bool, stdout: str, stderr: str, evidence: Path) -> tuple[bool, list[str]]:
    oracle = case["oracle"]
    failures: list[str] = []
    expected_exit = oracle.get("exitCode", 0)
    if timed_out:
        failures.append("timeout")
    elif exit_code != expected_exit:
        failures.append(f"exitCode expected={expected_exit} actual={exit_code}")
    for stream_name, text, positive_key, negative_key in (
        ("stdout", stdout, "stdoutContains", "stdoutNotContains"),
        ("stderr", stderr, "stderrContains", "stderrNotContains"),
    ):
        for needle in oracle.get(positive_key, []):
            if needle not in text:
                failures.append(f"{stream_name} missing {needle!r}")
        for needle in oracle.get(negative_key, []):
            if needle in text:
                failures.append(f"{stream_name} unexpectedly contains {needle!r}")
    for artifact in oracle.get("artifacts", []):
        path = evidence / artifact["path"]
        expected_exists = artifact.get("exists", True)
        if path.is_symlink():
            failures.append(f"artifact {artifact['path']} is a forbidden symlink")
            continue
        try:
            path.resolve().relative_to(evidence.resolve())
        except ValueError:
            failures.append(f"artifact {artifact['path']} escapes evidence root")
            continue
        if path.exists() != expected_exists:
            failures.append(f"artifact {artifact['path']} exists expected={expected_exists} actual={path.exists()}")
            continue
        if path.exists() and "contains" in artifact:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                failures.append(f"artifact {artifact['path']} unreadable: {exc}")
            else:
                if artifact["contains"] not in content:
                    failures.append(f"artifact {artifact['path']} missing {artifact['contains']!r}")
    return not failures, failures


def collect_artifact_hashes(evidence: Path) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    failures: list[str] = []
    for artifact_path in sorted(evidence.rglob("*")):
        relative = str(artifact_path.relative_to(evidence))
        if artifact_path.is_symlink():
            failures.append(f"forbidden artifact symlink: {relative}")
        elif artifact_path.is_file():
            hashes[relative] = sha256_file(artifact_path)
    return hashes, failures


def build_image(manifest: dict[str, Any], base: Path, run_root: Path, dry_run: bool) -> None:
    image = manifest["image"]
    if "context" not in image:
        return
    context = (base / image["context"]).resolve()
    containerfile = (base / image["file"]).resolve()
    log_path = run_root / "image-build.log"
    args = ["container", "build", "--progress", "plain", "-t", image["tag"], "-f", str(containerfile)]
    if image.get("pull", False):
        args.append("--pull")
    args.append(str(context))
    if dry_run:
        log_path.write_text("DRY RUN: " + shlex.join(args) + "\n", encoding="utf-8")
        return
    completed = run_capture(args)
    log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"image build failed ({completed.returncode}); see {log_path}")


def build_container_args(
    manifest: dict[str, Any], case: dict[str, Any], name: str, evidence: Path, base: Path
) -> tuple[list[str], set[str]]:
    defaults = manifest["defaults"]
    args = ["container", "run", "--rm", "--init", "--name", name]
    args += ["--network", case.get("network", defaults.get("network", "none"))]
    args += ["--cpus", str(case.get("cpus", defaults.get("cpus", 1)))]
    args += ["--memory", case.get("memory", defaults.get("memory", "2G"))]
    if case.get("readOnlyRoot", defaults.get("readOnlyRoot", True)):
        args += ["--read-only", "--tmpfs", "/tmp"]
    args += ["--mount", f"type=bind,source={evidence},target=/evidence"]
    for mount in manifest.get("mounts", []):
        source = (base / mount["source"]).resolve()
        spec = f"type=bind,source={source},target={mount['target']}"
        if mount.get("readonly", True):
            spec += ",readonly"
        args += ["--mount", spec]
    for key, value in sorted(case.get("env", {}).items()):
        args += ["-e", f"{key}={value}"]
    inherited = set(case.get("inheritEnv", []))
    missing = sorted(key for key in inherited if key not in os.environ)
    if missing:
        raise RuntimeError(f"missing inherited environment variables: {', '.join(missing)}")
    for key in sorted(inherited):
        args += ["-e", key]
    args.append(manifest["image"]["tag"])
    args.extend(case["command"])
    return args, inherited


def execute_job(
    manifest: dict[str, Any], case: dict[str, Any], repeat: int, run_id: str, run_root: Path, base: Path, dry_run: bool
) -> dict[str, Any]:
    job_id = f"{case['id']}-r{repeat}"
    job_root = run_root / "jobs" / job_id
    job_root.mkdir(parents=True, exist_ok=True)
    evidence = job_root / "evidence"
    if dry_run:
        evidence.mkdir(parents=True, exist_ok=True)
    stdout_path, stderr_path = job_root / "stdout.log", job_root / "stderr.log"
    result_path = job_root / "result.json"
    if result_path.exists() and not dry_run:
        existing = json.loads(result_path.read_text(encoding="utf-8"))
        if existing.get("caseId") != case["id"] or existing.get("repeat") != repeat:
            raise RuntimeError(f"resume result identity mismatch: {result_path}")
        for log_name, hash_name in (("stdout.log", "stdoutSha256"), ("stderr.log", "stderrSha256")):
            log_path = job_root / log_name
            if not log_path.is_file() or sha256_file(log_path) != existing.get(hash_name):
                raise RuntimeError(f"resume log hash mismatch: {log_path}")
        for attempt_record in existing.get("attempts", []):
            attempt_number = attempt_record.get("attempt")
            attempt_root = job_root / "attempts" / str(attempt_number)
            for log_name, hash_name in (("stdout.log", "stdoutSha256"), ("stderr.log", "stderrSha256")):
                log_path = attempt_root / log_name
                if not log_path.is_file() or sha256_file(log_path) != attempt_record.get(hash_name):
                    raise RuntimeError(f"resume attempt log hash mismatch: {log_path}")
            actual_hashes, artifact_failures = collect_artifact_hashes(attempt_root / "evidence")
            if artifact_failures or actual_hashes != attempt_record.get("artifactSha256", {}):
                raise RuntimeError(f"resume attempt artifact mismatch: {attempt_root / 'evidence'}")
        return existing
    name = safe_name(f"acv-{run_root}-{run_id}-{job_id}")
    args, inherited = build_container_args(manifest, case, name, evidence, base)
    redacted = redact_command(args, inherited)
    if dry_run:
        result = {
            "jobId": job_id,
            "caseId": case["id"],
            "group": case["group"],
            "relation": case["relation"],
            "criterionIds": case["criterionIds"],
            "agentCli": case.get("agentCli"),
            "repeat": repeat,
            "status": "dry-run",
            "command": redacted,
        }
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    timeout = case.get("timeoutSeconds", manifest["defaults"].get("timeoutSeconds", 120))
    retries = case.get("retries", manifest["defaults"].get("retries", 0))
    attempts: list[dict[str, Any]] = []
    final_stdout = ""
    final_stderr = ""
    final_exit: int | None = None
    final_timeout = False
    passed = False
    failures: list[str] = []
    started_job = time.monotonic()
    for attempt in range(1, retries + 2):
        attempt_root = job_root / "attempts" / str(attempt)
        attempt_evidence = attempt_root / "evidence"
        attempt_evidence.mkdir(parents=True, exist_ok=False)
        attempt_name = safe_name(f"acv-{run_root}-{run_id}-{job_id}-a{attempt}")
        attempt_args, inherited = build_container_args(manifest, case, attempt_name, attempt_evidence, base)
        started = time.monotonic()
        timed_out = False
        try:
            completed = run_capture(attempt_args, timeout=timeout)
            exit_code = completed.returncode
            stdout, stderr = completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = None
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
            subprocess.run(["container", "delete", "--force", attempt_name], text=True, capture_output=True, check=False)
        for secret_name in inherited:
            secret_value = os.environ.get(secret_name, "")
            if secret_value:
                stdout = stdout.replace(secret_value, f"<redacted:{secret_name}>")
                stderr = stderr.replace(secret_value, f"<redacted:{secret_name}>")
        attempt_stdout = attempt_root / "stdout.log"
        attempt_stderr = attempt_root / "stderr.log"
        attempt_stdout.write_text(stdout, encoding="utf-8")
        attempt_stderr.write_text(stderr, encoding="utf-8")
        passed, failures = check_oracle(case, exit_code, timed_out, stdout, stderr, attempt_evidence)
        attempt_artifact_hashes, artifact_failures = collect_artifact_hashes(attempt_evidence)
        if artifact_failures:
            failures.extend(artifact_failures)
            passed = False
        attempt_redacted = redact_command(attempt_args, inherited)
        attempts.append({
            "attempt": attempt,
            "containerName": attempt_name,
            "command": attempt_redacted,
            "exitCode": exit_code,
            "timedOut": timed_out,
            "durationSeconds": round(time.monotonic() - started, 3),
            "passed": passed,
            "failures": failures,
            "stdoutSha256": sha256_file(attempt_stdout),
            "stderrSha256": sha256_file(attempt_stderr),
            "artifactSha256": attempt_artifact_hashes,
        })
        final_stdout, final_stderr, final_exit, final_timeout = stdout, stderr, exit_code, timed_out
        evidence = attempt_evidence
        if passed or not timed_out:
            break
    stdout_path.write_text(final_stdout, encoding="utf-8")
    stderr_path.write_text(final_stderr, encoding="utf-8")
    artifact_hashes, final_artifact_failures = collect_artifact_hashes(evidence)
    if final_artifact_failures:
        failures.extend(item for item in final_artifact_failures if item not in failures)
        passed = False
    result = {
        "jobId": job_id,
        "caseId": case["id"],
        "group": case["group"],
        "relation": case["relation"],
        "criterionIds": case["criterionIds"],
        "agentCli": case.get("agentCli"),
        "repeat": repeat,
        "status": "oracle-pass" if passed else ("timeout" if final_timeout else "oracle-fail"),
        "description": case["description"],
        "command": attempts[-1]["command"],
        "exitCode": final_exit,
        "durationSeconds": round(time.monotonic() - started_job, 3),
        "attempts": attempts,
        "oracleFailures": failures,
        "stdoutSha256": sha256_file(stdout_path),
        "stderrSha256": sha256_file(stderr_path),
        "artifactSha256": artifact_hashes,
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def write_report(manifest: dict[str, Any], summary: dict[str, Any], run_root: Path) -> None:
    rows = []
    for result in sorted(summary["results"], key=lambda item: item["jobId"]):
        failures = "; ".join(result.get("oracleFailures", [])) or "—"
        rows.append(
            f"| `{result['jobId']}` | {result['group']} | {result['status']} | "
            f"{result.get('durationSeconds', 0)} | {failures.replace('|', '\\|')} |"
        )
    report = f"""# Apple Container検証レポート: {manifest['claim']}

## ステータス

- Run ID: `{summary['runId']}`
- Claim outcome: **{summary['claimOutcome']}**
- Execution status: **{summary['executionStatus']}**
- オラクル成立: {summary['counts'].get('oracle-pass', 0)} / {summary['jobs']}
- オラクル不成立: {summary['counts'].get('oracle-fail', 0)}
- タイムアウト: {summary['counts'].get('timeout', 0)}

## 仮説

{manifest['hypothesis']}

### 棄却条件

""" + "\n".join(f"- `{item['id']}`: {item['description']}" for item in manifest["falsificationCriteria"]) + f"""

## 環境と来歴

- Apple Container: `{summary['provenance']['containerVersion']}`
- Host: `{summary['provenance']['host']}`
- Image: `{manifest['image']['tag']}`
- Image inspect SHA-256: `{summary['provenance']['imageInspectSha256']}`
- Manifest SHA-256: `{summary['provenance']['manifestSha256']}`
- 実行開始: `{summary['startedAt']}`
- 実行終了: `{summary['completedAt']}`
- 並列度: {summary['concurrency']}
- Agent CLI: `{', '.join(sorted({case.get('agentCli') for case in manifest['cases'] if case.get('agentCli')})) or 'none'}`
- Agent CLI authentication: `subscription only`

## ケース結果

| Job | Group | Status | Seconds | Oracle failure |
|---|---|---:|---:|---|
""" + "\n".join(rows) + """

## 観察

自動判定結果と `jobs/*/stdout.log`、`jobs/*/stderr.log` を照合し、観察事実を記述する。

## 推論

観察から支持される範囲だけを記述する。

## 反証・限界・未検証事項

対象外の環境、測定誤差、並列干渉、外部依存、未実行ケースを記述する。

## 再実行

```bash
python3 scripts/run-matrix.py path/to/manifest.json --run-id NEW_RUN_ID --concurrency auto
```

## 証跡

- `run-manifest.json`
- `summary.json`
- `jobs/*/result.json`
- `jobs/*/stdout.log`
- `jobs/*/stderr.log`
"""
    (run_root / "report.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apple Container検証行列を並列実行する")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--concurrency", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}", args.run_id):
        print("ERROR: run-idが不正", file=sys.stderr)
        return 2
    manifest_path = args.manifest.resolve()
    try:
        manifest, errors, warnings = validate_manifest(manifest_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    uses_mutable_codex_cache = any(
        case.get("agentCli") == "codex-subscription"
        and "CODEX_ACCESS_TOKEN" not in case.get("inheritEnv", [])
        for case in manifest.get("cases", [])
    )
    if args.resume and uses_mutable_codex_cache:
        print("ERROR: --resume is disabled for mutable Codex subscription auth cache; use a new run-id", file=sys.stderr)
        return 2
    if shutil.which("container") is None:
        print("ERROR: Apple Container CLI unavailable", file=sys.stderr)
        return 2
    if run_capture(["container", "--version"]).returncode != 0:
        print("ERROR: Apple Container CLI unavailable", file=sys.stderr)
        return 2
    status = run_capture(["container", "system", "status"])
    if status.returncode != 0 or "running" not in status.stdout:
        print("ERROR: Apple Container system is not running", file=sys.stderr)
        print(status.stdout + status.stderr, file=sys.stderr)
        return 2

    jobs = [
        (case, repeat)
        for case in manifest["cases"]
        for repeat in range(1, case.get("repeats", manifest["defaults"].get("repeats", 1)) + 1)
    ]
    if args.concurrency == "auto":
        concurrency = recommended_concurrency(manifest, len(jobs))
    else:
        try:
            concurrency = int(args.concurrency)
        except ValueError:
            print("ERROR: concurrencyはautoまたは正整数", file=sys.stderr)
            return 2
        if concurrency < 1:
            print("ERROR: concurrencyは1以上", file=sys.stderr)
            return 2
        concurrency = min(concurrency, manifest["defaults"].get("maxConcurrency", concurrency), len(jobs))
    if any(mount.get("readonly", True) is not True for mount in manifest.get("mounts", [])):
        concurrency = 1
        print("WARNING: shared writable mount forces concurrency=1", file=sys.stderr)

    run_root = args.results_dir.resolve() / args.run_id
    if run_root.exists() and not args.resume:
        print(f"ERROR: run directory exists; use a new run-id or --resume: {run_root}", file=sys.stderr)
        return 2
    base = manifest_path.parent
    manifest_hash = sha256_file(manifest_path)
    run_manifest_path = run_root / "run-manifest.json"
    container_version = run_capture(["container", "--version"]).stdout.strip()
    mount_hashes = {
        mount["source"]: tree_sha256((base / mount["source"]).resolve())
        for mount in manifest.get("mounts", [])
    }
    skill_root = Path(__file__).resolve().parent.parent
    build_context_hash = (
        tree_sha256((base / manifest["image"]["context"]).resolve(), {run_root})
        if "context" in manifest["image"]
        else None
    )
    static_provenance = {
        "version": 1,
        "runId": args.run_id,
        "manifest": str(manifest_path),
        "manifestSha256": manifest_hash,
        "image": manifest["image"],
        "mountInputSha256": mount_hashes,
        "skillBundleSha256": tree_sha256(skill_root),
        "containerfileSha256": sha256_file((base / manifest["image"]["file"]).resolve()) if "file" in manifest["image"] else None,
        "buildContextSha256": build_context_hash,
        "jobs": [{"caseId": case["id"], "repeat": repeat} for case, repeat in jobs],
        "concurrency": concurrency,
        "containerVersion": container_version,
        "host": f"{platform.system()} {platform.release()} {platform.machine()}",
    }
    existing = None
    if run_manifest_path.exists():
        existing = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        created_at = existing.get("createdAt")
        if not isinstance(created_at, str):
            print("ERROR: existing run manifest lacks createdAt", file=sys.stderr)
            return 2
    else:
        created_at = datetime.now(timezone.utc).isoformat()
        run_root.mkdir(parents=True, exist_ok=False)
        try:
            build_image(manifest, base, run_root, args.dry_run)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    if args.dry_run:
        image_inspect_text = "dry-run: image not inspected\n"
    else:
        image_inspect = run_capture(["container", "image", "inspect", manifest["image"]["tag"]])
        image_inspect_text = image_inspect.stdout + image_inspect.stderr
        if image_inspect.returncode != 0:
            print("ERROR: image inspect failed", file=sys.stderr)
            print(image_inspect_text, file=sys.stderr)
            return 2
    image_inspect_hash = sha256_bytes(image_inspect_text.encode("utf-8"))
    run_manifest = {
        **static_provenance,
        "createdAt": created_at,
        "imageInspectSha256": image_inspect_hash,
    }
    if existing is not None:
        if existing != run_manifest:
            print("ERROR: resume provenance mismatch; use a new run-id", file=sys.stderr)
            return 2
    else:
        (run_root / "image-inspect.json").write_text(image_inspect_text, encoding="utf-8")
        run_manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    started_at = created_at

    results: list[dict[str, Any]] = []
    shared_writable_mount = any(mount.get("readonly", True) is not True for mount in manifest.get("mounts", []))
    lock_groups = {case.get("exclusiveGroup") for case, _ in jobs if case.get("exclusiveGroup")}
    if shared_writable_mount:
        lock_groups.add("__shared_writable_mount__")
    exclusive_locks = {group: threading.Lock() for group in lock_groups}

    def scheduled_job(case: dict[str, Any], repeat: int) -> dict[str, Any]:
        group = "__shared_writable_mount__" if shared_writable_mount else case.get("exclusiveGroup")
        if group is None:
            return execute_job(manifest, case, repeat, args.run_id, run_root, base, args.dry_run)
        with exclusive_locks[group]:
            return execute_job(manifest, case, repeat, args.run_id, run_root, base, args.dry_run)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        future_jobs = {
            pool.submit(scheduled_job, case, repeat): (case, repeat)
            for case, repeat in jobs
        }
        for future in concurrent.futures.as_completed(future_jobs):
            case, repeat = future_jobs[future]
            try:
                result = future.result()
            except Exception as exc:  # job-level infrastructure failure must remain visible
                print(f"ERROR: job infrastructure failure: {exc}", file=sys.stderr)
                result = {
                    "jobId": f"{case['id']}-r{repeat}",
                    "caseId": case["id"],
                    "group": case["group"],
                    "relation": case["relation"],
                    "criterionIds": case["criterionIds"],
                    "agentCli": case.get("agentCli"),
                    "status": "infrastructure-error",
                    "oracleFailures": [str(exc)],
                }
            results.append(result)
            print(f"{result['status']}: {result['jobId']}")

    completed_at = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    passed_relations = {result.get("relation") for result in results if result["status"] == "oracle-pass"}
    if args.dry_run:
        execution_status = "DRY RUN"
        claim_outcome = "UNVERIFIED"
    elif counts.get("oracle-pass", 0) != len(jobs):
        execution_status = "INCOMPLETE OR ORACLE MISMATCH"
        claim_outcome = "FALSIFIED" if "falsify" in passed_relations else "UNVERIFIED"
    else:
        execution_status = "COMPLETE"
        if "falsify" in passed_relations:
            claim_outcome = "FALSIFIED"
        elif "support" in passed_relations:
            claim_outcome = "SUPPORTED WITHIN TESTED SCOPE"
        else:
            claim_outcome = "UNVERIFIED"
    summary = {
        "version": 1,
        "runId": args.run_id,
        "executionStatus": execution_status,
        "claimOutcome": claim_outcome,
        "jobs": len(jobs),
        "counts": counts,
        "concurrency": concurrency,
        "startedAt": started_at,
        "completedAt": completed_at,
        "provenance": {
            "manifestSha256": manifest_hash,
            "imageInspectSha256": image_inspect_hash,
            "mountInputSha256": mount_hashes,
            "skillBundleSha256": run_manifest["skillBundleSha256"],
            "containerVersion": container_version,
            "host": run_manifest["host"],
        },
        "results": results,
    }
    (run_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(manifest, summary, run_root)
    print(f"SUMMARY: {run_root / 'summary.json'}")
    print(f"REPORT: {run_root / 'report.md'}")
    return 0 if execution_status in {"COMPLETE", "DRY RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
