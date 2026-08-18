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
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_VALIDATOR_PATH = Path(__file__).with_name("validate-manifest.py")
_VALIDATOR_SPEC = importlib.util.spec_from_file_location("apple_container_manifest_validator", _VALIDATOR_PATH)
if _VALIDATOR_SPEC is None or _VALIDATOR_SPEC.loader is None:
    raise RuntimeError(f"validatorを読み込めない: {_VALIDATOR_PATH}")
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)
recommended_concurrency = _VALIDATOR.recommended_concurrency
validate_manifest = _VALIDATOR.validate_manifest
extract_inherited_env_names = _VALIDATOR.extract_inherited_env_names
reject_lone_surrogates = _VALIDATOR.reject_lone_surrogates
CliArgumentError = _VALIDATOR.CliArgumentError
SilentArgumentParser = _VALIDATOR.SilentArgumentParser

CONTAINER_CLEANUP_TIMEOUT_SECONDS = 10.0


class ResumeIntegrityError(RuntimeError):
    """A completed resume job failed validation and must remain untouched."""


class BufferedDiagnostics:
    """Preserve event order and emit one checked stream to one physical channel."""

    def __init__(self) -> None:
        self.records: list[str] = []
        self.inherited_names: set[str] = set()

    def set_inherited_names(self, names: set[str]) -> None:
        self.inherited_names.update(names)

    def add(self, value: Any = "", *, stderr: bool = False) -> None:
        # stderr is intentionally only a semantic hint until the final exit status
        # selects the invocation's single physical channel.
        self.records.append(str(value))

    def flush(self, *, success: bool) -> None:
        if not self.records:
            return
        try:
            payload = "".join(record + "\n" for record in self.records)
            encoded = safe_text_bytes(payload, self.inherited_names)
        except (RuntimeError, UnicodeEncodeError):
            fallback = "ERROR: output encoding failed\n"
            if any(secret in fallback for secret in inherited_values(self.inherited_names)):
                encoded = b""
            else:
                encoded = fallback.encode("ascii")
        stream = sys.stdout if success else sys.stderr
        if hasattr(stream, "buffer"):
            stream.buffer.write(encoded)
        else:
            stream.write(encoded.decode("utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, value: bytes, *, root: Path | None = None) -> None:
    """排他的に作った同一ディレクトリの0600一時ファイルから原子的に置換する。"""
    publication_root = root if root is not None else path.parent
    require_real_directory(publication_root, path.parent, "atomic write parent")
    file_descriptor: int | None = None
    temporary_name: str | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "wb") as handle:
            file_descriptor = None
            handle.write(value)
        require_real_file(publication_root, Path(temporary_name), "atomic write temporary file")
        require_real_directory(publication_root, path.parent, "atomic write parent")
        os.replace(temporary_name, path)
        temporary_name = None  # os.replace is the commit point; nothing fallible follows it.
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _assert_secret_free_bytes(value: bytes, inherited_names: set[str]) -> None:
    for secret in inherited_values(inherited_names):
        if secret.encode("utf-8") in value:
            raise RuntimeError("final serialized output cannot be published safely")


def safe_text_bytes(value: str, inherited_names: set[str]) -> bytes:
    result = redact_inherited_text(value, inherited_names).encode("utf-8")
    _assert_secret_free_bytes(result, inherited_names)
    return result


def safe_json_bytes(value: Any, inherited_names: set[str]) -> bytes:
    redacted = redact_inherited_structure(value, inherited_names)
    result = (json.dumps(redacted, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _assert_secret_free_bytes(result, inherited_names)
    return result


def atomic_write_text(
    path: Path, value: str, *, root: Path | None = None,
    inherited_names: set[str] | None = None,
) -> None:
    atomic_write_bytes(path, safe_text_bytes(value, inherited_names or set()), root=root)


def atomic_create_bytes(path: Path, value: bytes, *, root: Path) -> None:
    """Publish a complete immutable file without replacing an existing destination."""
    require_real_directory(root, path.parent, "exclusive publication parent")
    fd: int | None = None
    temporary_name: str | None = None
    try:
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        require_real_file(root, Path(temporary_name), "exclusive publication temporary file")
        os.link(temporary_name, path, follow_symlinks=False)
    finally:
        if fd is not None:
            os.close(fd)
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def atomic_create_text(
    path: Path, value: str, *, root: Path, inherited_names: set[str] | None = None
) -> None:
    atomic_create_bytes(path, safe_text_bytes(value, inherited_names or set()), root=root)


def atomic_write_json(
    path: Path, value: dict[str, Any], *, root: Path | None = None,
    inherited_names: set[str] | None = None,
) -> None:
    names = inherited_names or set()
    serialized = safe_json_bytes(value, names).decode("utf-8")
    atomic_write_text(path, serialized, root=root, inherited_names=names)


def _require_contained_path(root: Path, path: Path, *, directory: bool, label: str) -> Path:
    """root配下の実体ファイル/ディレクトリだけを返し、symlinkを拒否する。"""
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes expected root: {path}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"{label} must not contain symlinks: {current}")
    if root.is_symlink():
        raise RuntimeError(f"{label} root must not be a symlink: {root}")
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"{label} is missing or outside expected root: {path}") from exc
    valid = path.is_dir() if directory else path.is_file()
    if not valid:
        kind = "directory" if directory else "regular file"
        raise RuntimeError(f"{label} must be a real {kind}: {path}")
    return path


def require_real_file(root: Path, path: Path, label: str) -> Path:
    return _require_contained_path(root, path, directory=False, label=label)


def require_real_directory(root: Path, path: Path, label: str) -> Path:
    return _require_contained_path(root, path, directory=True, label=label)


def create_or_validate_directory(root: Path, path: Path, label: str) -> Path:
    """既存のsymlinkをたどらず、root配下の検証済み親へ0700で1階層を作る。"""
    require_real_directory(root, root, f"{label} root")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes expected root: {path}") from exc
    if not relative.parts:
        return require_real_directory(root, path, label)
    require_real_directory(root, path.parent, f"{label} parent")
    created = False
    if not os.path.lexists(path):
        try:
            path.mkdir(mode=0o700)
            created = True
        except FileExistsError:
            pass
    validated = require_real_directory(root, path, label)
    if created:
        validated.chmod(0o700)
    return validated


def reject_lexical_symlinks(path: Path) -> Path:
    """resolve前のresults pathに含まれる既存symlink componentを拒否する。"""
    lexical = path if path.is_absolute() else Path.cwd() / path
    current = Path(lexical.anchor)
    for part in lexical.parts[1:] if lexical.is_absolute() else lexical.parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            raise RuntimeError(f"results directory must not contain symlinks: {current}")
    return lexical


def create_results_directory(path: Path) -> Path:
    lexical = reject_lexical_symlinks(path)
    existed = lexical.exists()
    lexical.mkdir(parents=True, mode=0o700, exist_ok=True)
    reject_lexical_symlinks(path)
    if not lexical.is_dir() or lexical.is_symlink():
        raise RuntimeError(f"results directory must be a real directory: {lexical}")
    if not existed:
        lexical.chmod(0o700)
    return lexical.resolve(strict=True)


def _inventory_evidence(root: Path) -> None:
    require_real_directory(root, root, "evidence root")
    for entry in root.rglob("*"):
        if entry.is_symlink():
            raise RuntimeError(f"forbidden evidence symlink: {entry}")
        if entry.is_dir():
            require_real_directory(root, entry, "evidence directory")
        elif entry.is_file():
            require_real_file(root, entry, "evidence file")
        else:
            raise RuntimeError(f"forbidden evidence special file: {entry}")


def _require_exact_entries(root: Path, allowed: set[str], label: str) -> None:
    actual = {entry.name for entry in root.iterdir()}
    rogue = actual - allowed
    if rogue:
        raise RuntimeError(f"unexpected {label} entries: {', '.join(sorted(rogue))}")


def inventory_job_tree(
    run_root: Path, expected_job_ids: set[str], *, require_complete: bool = False
) -> None:
    """Validate the complete runner-owned jobs schema, not only job IDs."""
    jobs_root = require_real_directory(run_root, run_root / "jobs", "jobs directory")
    actual = {entry.name for entry in jobs_root.iterdir()}
    unexpected = actual - expected_job_ids
    if unexpected:
        raise RuntimeError(f"unexpected job tree entries: {', '.join(sorted(unexpected))}")
    for job_root in jobs_root.iterdir():
        require_real_directory(jobs_root, job_root, "job tree entry")
        _require_exact_entries(
            job_root, {"result.json", "stdout.log", "stderr.log", "attempts", "evidence"},
            "job",
        )
        result_path = job_root / "result.json"
        result = load_json_object(result_path, root=job_root, label="job result") if result_path.exists() else None
        if (job_root / "evidence").exists():
            _inventory_evidence(require_real_directory(job_root, job_root / "evidence", "job evidence"))
        attempts_root = job_root / "attempts"
        expected_attempts: set[str] = set()
        if result is not None and isinstance(result.get("attempts"), list):
            expected_attempts = {str(index) for index in range(1, len(result["attempts"]) + 1)}
        if attempts_root.exists():
            require_real_directory(job_root, attempts_root, "attempts directory")
            _require_exact_entries(attempts_root, expected_attempts, "attempts")
            for attempt_root in attempts_root.iterdir():
                require_real_directory(attempts_root, attempt_root, "attempt directory")
                _require_exact_entries(attempt_root, {"stdout.log", "stderr.log", "evidence"}, "attempt")
                evidence = require_real_directory(attempt_root, attempt_root / "evidence", "attempt evidence")
                _inventory_evidence(evidence)
                actual_hashes, hash_failures = collect_artifact_hashes(evidence)
                attempt_index = int(attempt_root.name) - 1
                attempt_records = result.get("attempts", []) if result is not None else []
                expected_hashes = (
                    attempt_records[attempt_index].get("artifactSha256")
                    if attempt_index < len(attempt_records) and isinstance(attempt_records[attempt_index], dict)
                    else None
                )
                if hash_failures or actual_hashes != expected_hashes:
                    raise RuntimeError(f"attempt evidence is not hash-bound: {evidence}")
                require_real_file(attempt_root, attempt_root / "stdout.log", "attempt stdout")
                require_real_file(attempt_root, attempt_root / "stderr.log", "attempt stderr")
        if result is not None:
            status = result.get("status")
            if status == "dry-run":
                _require_exact_entries(job_root, {"result.json", "evidence"}, "dry-run job")
                if any((job_root / "evidence").rglob("*")):
                    raise RuntimeError(f"dry-run evidence must be empty: {job_root / 'evidence'}")
            elif status == "infrastructure-error" and not result.get("attempts"):
                allowed = {"result.json", "evidence"} if (job_root / "evidence").exists() else {"result.json"}
                _require_exact_entries(job_root, allowed, "pre-attempt infrastructure job")
                if (job_root / "evidence").exists() and any((job_root / "evidence").rglob("*")):
                    raise RuntimeError(f"pre-attempt infrastructure evidence must be empty: {job_root / 'evidence'}")
            else:
                _require_exact_entries(job_root, {"result.json", "stdout.log", "stderr.log", "attempts"}, "completed job")
                require_real_file(job_root, job_root / "stdout.log", "job stdout")
                require_real_file(job_root, job_root / "stderr.log", "job stderr")
        elif require_complete:
            raise RuntimeError(f"job result is missing: {job_root}")
    missing = expected_job_ids - actual
    if require_complete and missing:
        raise RuntimeError(f"missing job tree entries: {', '.join(sorted(missing))}")


_GENERATION_REPORT_RE = re.compile(r"^report\.[0-9a-f]{32}\.md$")


def inventory_run_root(run_root: Path) -> None:
    """Reject every undocumented sibling before authoritative publication."""
    require_real_directory(run_root, run_root, "run directory")
    fixed_files = {
        "run-manifest.json", "image-inspect.json", "image-build.log",
        "summary.json", "report.md",
    }
    for entry in run_root.iterdir():
        if entry.name == "jobs":
            require_real_directory(run_root, entry, "jobs directory")
        elif entry.name in fixed_files or _GENERATION_REPORT_RE.fullmatch(entry.name):
            require_real_file(run_root, entry, "run file")
        else:
            raise RuntimeError(f"unexpected run-root entry: {entry.name}")


def load_json_object(path: Path, *, root: Path, label: str) -> dict[str, Any]:
    require_real_file(root, path, label)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        reject_lone_surrogates(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"{label} is unreadable or malformed: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path}")
    return value


def read_resume_text(root: Path, path: Path, label: str) -> str:
    try:
        return require_real_file(root, path, label).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, RuntimeError) as exc:
        raise ResumeIntegrityError("persisted resume text is unreadable") from exc


def verify_persisted_image_inspect(
    run_root: Path, existing: dict[str, Any], expected_hash: str
) -> str:
    inspect_path = require_real_file(
        run_root, run_root / "image-inspect.json", "persisted image inspect"
    )
    persisted_hash = sha256_file(inspect_path)
    if (
        persisted_hash != existing.get("imageInspectSha256")
        or persisted_hash != expected_hash
    ):
        raise RuntimeError("persisted image inspect provenance mismatch")
    return persisted_hash


def _lexical_absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def tree_sha256(root: Path, exclude: set[Path] | None = None) -> str:
    """Hash a type-framed tree while skipping lexical exclusions before any resolve."""
    root = _lexical_absolute(root)
    excluded = {_lexical_absolute(path) for path in (exclude or set())}
    if root.is_symlink():
        raise RuntimeError(f"hash root must not be a symlink: {root}")
    digest = hashlib.sha256()
    if root.is_file():
        digest.update(b"tree-v2\0regular-file\0")
        digest.update(sha256_file(root).encode("ascii"))
        return digest.hexdigest()
    if not root.is_dir():
        raise RuntimeError(f"hash root must be a regular file or real directory: {root}")
    digest.update(b"tree-v2\0directory\0")
    for path in sorted(root.rglob("*")):
        lexical = _lexical_absolute(path)
        if any(lexical == item or item in lexical.parents for item in excluded):
            continue
        relative_path = path.relative_to(root)
        if "__pycache__" in relative_path.parts or path.name in {".DS_Store"} or path.suffix == ".pyc":
            continue
        relative = str(relative_path).encode("utf-8")
        digest.update(b"entry\0" + relative + b"\0")
        if path.is_symlink():
            raise RuntimeError(f"unsupported input tree entry type: {path}")
        elif path.is_file():
            digest.update(b"regular-file\0" + sha256_file(path).encode("ascii") + b"\0")
        elif path.is_dir():
            digest.update(b"directory\0")
        else:
            raise RuntimeError(f"unsupported input tree entry type: {path}")
    return digest.hexdigest()


def tree_hash_exclusion(root: Path, results_root: Path) -> str | None:
    root = _lexical_absolute(root)
    results_root = _lexical_absolute(results_root)
    if root in results_root.parents:
        return str(results_root.relative_to(root))
    return None


def validate_results_hash_layout(
    skill_root: Path, results_root: Path, input_directory_roots: list[Path] | None = None
) -> None:
    if results_root == skill_root or results_root in skill_root.parents:
        raise RuntimeError("results directory must not equal or contain the skill root")
    for input_root in input_directory_roots or []:
        if results_root == input_root:
            raise RuntimeError("results directory must not equal a hashed input directory")


def tree_sha256_excluding_results(root: Path, results_root: Path) -> str:
    exclusion = tree_hash_exclusion(root, results_root)
    return tree_sha256(root, {results_root} if exclusion is not None else set())


def resolve_manifest_input(base: Path, value: str, *, directory: bool, label: str) -> Path:
    relative = Path(value)
    if (
        not isinstance(value, str) or not value.strip() or relative == Path(".")
        or relative.is_absolute() or ".." in relative.parts
        or any(ord(char) < 32 or 0x7F <= ord(char) <= 0x9F for char in value)
    ):
        raise RuntimeError(f"{label} must be a safe relative path")
    current = base
    for part in relative.parts:
        current = current / part
        if os.path.lexists(current) and current.is_symlink():
            raise RuntimeError(f"{label} must not contain symlinks")
    target = base / relative
    try:
        target.resolve(strict=True).relative_to(base.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"{label} must remain under the manifest directory") from exc
    if directory:
        if not target.is_dir() or target.is_symlink():
            raise RuntimeError(f"{label} must be a real directory")
    elif not target.is_file() or target.is_symlink():
        raise RuntimeError(f"{label} must be a regular file")
    return target.resolve(strict=True)


def resolve_mount_input(base: Path, value: str, label: str) -> Path:
    # Mount source may be a file or directory, but never a symlink/special file.
    relative = Path(value)
    if relative == Path("."):
        target = base
        if target.is_symlink() or not target.is_dir():
            raise RuntimeError(f"{label} must be a real directory")
        return target.resolve(strict=True)
    target = resolve_manifest_input(base, value, directory=False, label=label) if (base / relative).is_file() else None
    if target is not None:
        return target
    return resolve_manifest_input(base, value, directory=True, label=label)


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


def inherited_values(inherited_names: set[str]) -> list[str]:
    return sorted(
        {os.environ.get(name, "") for name in inherited_names if os.environ.get(name, "")},
        key=lambda value: (-len(value), value),
    )


def _delete_secrets_text(text: str, secrets_to_remove: list[str]) -> str:
    previous: str | None = None
    while text != previous:
        previous = text
        for secret in secrets_to_remove:
            text = text.replace(secret, "")
    if any(secret in text for secret in secrets_to_remove):
        raise RuntimeError("known inherited value remains after text sanitization")
    return text


def redact_inherited_text(text: str, inherited_names: set[str]) -> str:
    """Delete exact inherited values to a fixed point without adding a derived label."""
    return _delete_secrets_text(text, inherited_values(inherited_names))


def redact_inherited_structure(value: Any, inherited_names: set[str]) -> Any:
    if isinstance(value, str):
        return redact_inherited_text(value, inherited_names)
    if isinstance(value, list):
        return [redact_inherited_structure(item, inherited_names) for item in value]
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            safe_key = redact_inherited_text(key, inherited_names) if isinstance(key, str) else key
            if safe_key in redacted:
                raise RuntimeError("secret removal caused a persisted key collision")
            redacted[safe_key] = redact_inherited_structure(item, inherited_names)
        return redacted
    return value


def _delete_secrets_bytes(data: bytes, secrets_to_remove: list[bytes]) -> bytes:
    previous: bytes | None = None
    while data != previous:
        previous = data
        for secret in secrets_to_remove:
            data = data.replace(secret, b"")
    if any(secret in data for secret in secrets_to_remove):
        raise RuntimeError("known inherited value remains after binary sanitization")
    return data


def sanitize_artifacts(evidence: Path, inherited_names: set[str]) -> list[str]:
    """Remove exact inherited values and reject links/special files without following them."""
    failures: list[str] = []
    secrets_to_remove = [value.encode("utf-8") for value in inherited_values(inherited_names)]
    for path in sorted(evidence.rglob("*")):
        relative = str(path.relative_to(evidence))
        if path.is_symlink():
            failures.append(f"forbidden artifact symlink: {relative}")
            continue
        if path.is_dir():
            path.chmod(0o700)
            continue
        if not path.is_file():
            failures.append(f"forbidden artifact type: {relative}")
            continue
        data = path.read_bytes()
        sanitized = _delete_secrets_bytes(data, secrets_to_remove)
        if sanitized != data:
            atomic_write_bytes(path, sanitized, root=evidence)
            failures.append(f"artifact contained a known inherited value and was sanitized: {relative}")
        else:
            path.chmod(0o600)
    return failures


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
        for index, needle in enumerate(oracle.get(positive_key, [])):
            if needle not in text:
                failures.append(f"{positive_key}[{index}] failed")
        for index, needle in enumerate(oracle.get(negative_key, [])):
            if needle in text:
                failures.append(f"{negative_key}[{index}] failed")
    for artifact_index, artifact in enumerate(oracle.get("artifacts", [])):
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
        exists = path.exists()
        if exists != expected_exists:
            failures.append(f"artifact {artifact['path']} exists expected={expected_exists} actual={exists}")
            continue
        if exists and not path.is_file():
            failures.append(f"artifact {artifact['path']} must be a regular file")
            continue
        if exists and "contains" in artifact:
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                failures.append(f"artifact {artifact['path']} unreadable: {exc}")
            else:
                if artifact["contains"] not in content:
                    failures.append(f"artifacts[{artifact_index}].contains failed")
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
        elif not artifact_path.is_dir():
            failures.append(f"forbidden artifact type: {relative}")
    return hashes, failures


JOB_STATUS_KEYS = (
    "oracle-pass",
    "oracle-fail",
    "timeout",
    "infrastructure-error",
    "dry-run",
)


def evaluate_run(
    results: list[dict[str, Any]], expected_jobs: list[dict[str, Any]], dry_run: bool
) -> tuple[str, str, int]:
    """期待ジョブとの照合、実行完了、仮説との関係を独立して集約する。"""
    expected_by_id: dict[str, dict[str, Any]] = {}
    duplicate_expected_ids: set[str] = set()
    for expected in expected_jobs:
        job_id = expected.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("expected job lacks jobId")
        if job_id in expected_by_id:
            duplicate_expected_ids.add(job_id)
        expected_by_id[job_id] = expected
    if duplicate_expected_ids:
        raise ValueError(f"duplicate expected job IDs: {', '.join(sorted(duplicate_expected_ids))}")

    results_by_id: dict[str, list[dict[str, Any]]] = {}
    has_anonymous_results = False
    for result in results:
        job_id = result.get("jobId")
        if isinstance(job_id, str) and job_id:
            results_by_id.setdefault(job_id, []).append(result)
        else:
            has_anonymous_results = True

    matched: dict[str, dict[str, Any]] = {
        job_id: candidates[0]
        for job_id, candidates in results_by_id.items()
        if job_id in expected_by_id and len(candidates) == 1
    }
    has_unexpected_ids = bool(set(results_by_id) - set(expected_by_id))
    has_duplicate_ids = any(len(candidates) != 1 for candidates in results_by_id.values())
    evidence_integrity_clean = not (
        has_anonymous_results or has_unexpected_ids or has_duplicate_ids
    )
    identities_complete = (
        evidence_integrity_clean
        and len(results) == len(expected_by_id)
        and set(results_by_id) == set(expected_by_id)
    )
    if dry_run:
        dry_run_complete = identities_complete and all(
            result.get("status") == "dry-run" for result in matched.values()
        )
        return (
            ("DRY RUN", "UNVERIFIED", 0)
            if dry_run_complete
            else ("INCOMPLETE", "UNVERIFIED", 1)
        )

    adjudicated_statuses = {"oracle-pass", "oracle-fail"}
    execution_complete = identities_complete and all(
        result.get("status") in adjudicated_statuses for result in matched.values()
    )
    execution_status = "COMPLETE" if execution_complete else "INCOMPLETE"
    exit_code = 0 if execution_complete else 1

    if any(
        expected_by_id[job_id].get("relation") == "falsify"
        and result.get("status") == "oracle-pass"
        for job_id, result in matched.items()
    ):
        return execution_status, "FALSIFIED", exit_code

    support_ids = {
        job_id
        for job_id, expected in expected_by_id.items()
        if expected.get("relation") == "support"
    }
    falsify_ids = {
        job_id
        for job_id, expected in expected_by_id.items()
        if expected.get("relation") == "falsify"
    }
    support_complete = bool(support_ids) and all(
        job_id in matched and matched[job_id].get("status") == "oracle-pass"
        for job_id in support_ids
    )
    falsify_adjudicated = all(
        job_id in matched and matched[job_id].get("status") == "oracle-fail"
        for job_id in falsify_ids
    )
    if evidence_integrity_clean and support_complete and falsify_adjudicated:
        return execution_status, "SUPPORTED WITHIN TESTED SCOPE", exit_code

    return execution_status, "UNVERIFIED", exit_code


def aggregate_run_results(
    results: list[dict[str, Any]], expected_jobs: list[dict[str, Any]], dry_run: bool
) -> tuple[dict[str, Any], int]:
    """summary.jsonへ入れる安定した集約値とランナー終了コードを返す。"""
    counts = {status: 0 for status in JOB_STATUS_KEYS}
    counts["other/unadjudicated"] = 0
    for result in results:
        status = result.get("status")
        if status in counts and status != "other/unadjudicated":
            counts[status] += 1
        else:
            counts["other/unadjudicated"] += 1
    execution_status, claim_outcome, exit_code = evaluate_run(results, expected_jobs, dry_run)
    return {
        "version": 2,
        "executionStatus": execution_status,
        "claimOutcome": claim_outcome,
        "jobs": len(expected_jobs),
        "counts": counts,
    }, exit_code


def build_image(
    manifest: dict[str, Any], base: Path, run_root: Path, dry_run: bool,
    inherited_names: set[str],
) -> None:
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
        atomic_write_text(
            log_path,
            redact_inherited_text("DRY RUN: " + shlex.join(args) + "\n", inherited_names),
            root=run_root,
            inherited_names=inherited_names,
        )
        return
    completed = run_capture(args)
    atomic_write_text(
        log_path,
        redact_inherited_text(completed.stdout + completed.stderr, inherited_names),
        root=run_root,
        inherited_names=inherited_names,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"image build failed ({completed.returncode}); see {log_path}")


def build_container_args(
    manifest: dict[str, Any],
    case: dict[str, Any],
    name: str,
    evidence: Path,
    base: Path,
    *,
    require_inherited: bool = True,
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
    if require_inherited and missing:
        raise RuntimeError(f"missing inherited environment variables: {', '.join(missing)}")
    for key in sorted(inherited):
        args += ["-e", key]
    args.append(manifest["image"]["tag"])
    args.extend(case["command"])
    return args, inherited


def execute_job(
    manifest: dict[str, Any], case: dict[str, Any], repeat: int, run_id: str,
    run_root: Path, base: Path, dry_run: bool,
    all_inherited_names: set[str] | None = None,
    *, persist_resume_rebind: bool = True,
) -> dict[str, Any]:
    job_id = f"{case['id']}-r{repeat}"
    inherited = set(case.get("inheritEnv", []))
    known_inherited = inherited | (all_inherited_names or set())
    jobs_root = create_or_validate_directory(run_root, run_root / "jobs", "jobs directory")
    job_root = jobs_root / job_id
    result_path = job_root / "result.json"
    if os.path.lexists(job_root):
        require_real_directory(run_root, job_root, "job directory")
        if not result_path.exists() and any(job_root.iterdir()):
            raise RuntimeError(
                f"partial job state preserved at {job_root}; move it outside {run_root} or use a new run-id"
            )
    else:
        create_or_validate_directory(jobs_root, job_root, "job directory")
    require_real_directory(run_root, job_root, "job directory")
    evidence = job_root / "evidence"
    if dry_run:
        create_or_validate_directory(job_root, evidence, "dry-run evidence directory")
    stdout_path, stderr_path = job_root / "stdout.log", job_root / "stderr.log"
    if result_path.exists() and not dry_run:
        try:
            existing = load_json_object(result_path, root=job_root, label="resume result")
        except RuntimeError as exc:
            raise ResumeIntegrityError("persisted resume result is unreadable") from exc
        required_result_fields = {
            "jobId", "caseId", "repeat", "group", "relation", "criterionIds", "agentCli",
            "description", "status", "command", "exitCode", "durationSeconds",
            "attempts", "oracleFailures", "stdoutSha256", "stderrSha256",
            "artifactSha256",
        }
        if not required_result_fields.issubset(existing):
            raise RuntimeError(f"resume result lacks writer provenance: {result_path}")
        duration = existing.get("durationSeconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0:
            raise RuntimeError(f"resume result duration is invalid: {result_path}")
        if (
            existing.get("jobId") != job_id
            or existing.get("caseId") != case["id"]
            or type(existing.get("repeat")) is not int
            or existing.get("repeat") != repeat
        ):
            raise RuntimeError(f"resume result identity mismatch: {result_path}")
        for log_name, hash_name in (("stdout.log", "stdoutSha256"), ("stderr.log", "stderrSha256")):
            log_path = require_real_file(job_root, job_root / log_name, "resume top-level log")
            if sha256_file(log_path) != existing.get(hash_name):
                raise RuntimeError(f"resume log hash mismatch: {log_path}")
        attempt_records = existing.get("attempts")
        if not isinstance(attempt_records, list) or not attempt_records:
            raise RuntimeError(f"resume result lacks attempt records: {result_path}")
        max_attempts = case.get("retries", manifest["defaults"].get("retries", 0)) + 1
        if len(attempt_records) > max_attempts:
            raise RuntimeError(f"resume result has too many attempts: {result_path}")
        attempts_root = require_real_directory(
            job_root, job_root / "attempts", "resume attempts directory"
        )
        expected_attempt_names = {str(number) for number in range(1, len(attempt_records) + 1)}
        if {path.name for path in attempts_root.iterdir()} != expected_attempt_names:
            raise RuntimeError(f"resume attempt directory set is invalid: {attempts_root}")
        for attempt_path in attempts_root.iterdir():
            require_real_directory(attempts_root, attempt_path, "resume attempt directory")
        recomputed_attempts: list[tuple[bool, list[str], dict[str, str]]] = []
        for expected_attempt, attempt_record in enumerate(attempt_records, start=1):
            required_attempt_fields = {
                "attempt", "containerName", "command", "exitCode", "timedOut",
                "durationSeconds", "passed", "failures", "stdoutSha256",
                "stderrSha256", "artifactSha256",
            }
            if (
                not isinstance(attempt_record, dict)
                or not required_attempt_fields.issubset(attempt_record)
                or type(attempt_record.get("attempt")) is not int
                or attempt_record.get("attempt") != expected_attempt
            ):
                raise RuntimeError(f"resume attempt sequence or provenance mismatch: {result_path}")
            duration = attempt_record.get("durationSeconds")
            if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0:
                raise RuntimeError(f"resume attempt duration is invalid: {result_path}")
            attempt_root = require_real_directory(
                attempts_root,
                attempts_root / str(expected_attempt),
                "resume attempt directory",
            )
            attempt_evidence = require_real_directory(
                attempt_root, attempt_root / "evidence", "resume attempt evidence root"
            )
            expected_name = safe_name(f"acv-{run_root}-{run_id}-{job_id}-a{expected_attempt}")
            container_name = attempt_record.get("containerName")
            command = attempt_record.get("command")
            if container_name != expected_name:
                raise RuntimeError(f"resume attempt container identity mismatch: {attempt_root}")
            if not isinstance(command, list) or not command or not all(
                isinstance(token, str) and token for token in command
            ):
                raise RuntimeError(f"resume attempt command is invalid: {attempt_root}")
            expected_args, expected_inherited = build_container_args(
                manifest,
                case,
                expected_name,
                attempt_evidence,
                base,
                require_inherited=False,
            )
            if command != redact_command(expected_args, expected_inherited):
                raise RuntimeError(f"resume attempt command mismatch: {attempt_root}")
            for log_name, hash_name in (("stdout.log", "stdoutSha256"), ("stderr.log", "stderrSha256")):
                log_path = require_real_file(
                    attempt_root, attempt_root / log_name, "resume attempt log"
                )
                if sha256_file(log_path) != attempt_record.get(hash_name):
                    raise RuntimeError(f"resume attempt log hash mismatch: {log_path}")
            actual_hashes, artifact_failures = collect_artifact_hashes(attempt_evidence)
            if artifact_failures or actual_hashes != attempt_record.get("artifactSha256", {}):
                raise RuntimeError(f"resume attempt artifact mismatch: {attempt_evidence}")
            timed_out = attempt_record.get("timedOut")
            exit_code = attempt_record.get("exitCode")
            infrastructure_error = attempt_record.get("infrastructureError", False)
            if not isinstance(infrastructure_error, bool) or not isinstance(timed_out, bool):
                raise RuntimeError(f"resume attempt outcome is invalid: {result_path}")
            if infrastructure_error:
                if timed_out or exit_code is not None:
                    raise RuntimeError(f"resume infrastructure attempt outcome is invalid: {result_path}")
            elif (timed_out and exit_code is not None) or (not timed_out and type(exit_code) is not int):
                raise RuntimeError(f"resume attempt outcome is invalid: {result_path}")
            attempt_stdout = read_resume_text(
                attempt_root, attempt_root / "stdout.log", "resume attempt stdout"
            )
            attempt_stderr = read_resume_text(
                attempt_root, attempt_root / "stderr.log", "resume attempt stderr"
            )
            if infrastructure_error:
                passed, failures = False, [
                    "runner timeout cleanup timed out"
                    if "runner timeout cleanup timed out" in attempt_stderr
                    else "runner timeout cleanup failure"
                    if "runner timeout cleanup failure" in attempt_stderr
                    else "runner infrastructure failure"
                ]
            else:
                passed, failures = check_oracle(
                    case,
                    exit_code,
                    timed_out,
                    attempt_stdout,
                    attempt_stderr,
                    attempt_root / "evidence",
                )
            failures.extend(item for item in artifact_failures if item not in failures)
            if artifact_failures:
                passed = False
            if attempt_record.get("passed") is not passed or attempt_record.get("failures") != failures:
                raise RuntimeError(f"resume attempt outcome mismatch: {attempt_root}")
            if expected_attempt < len(attempt_records) and (not timed_out or infrastructure_error):
                raise RuntimeError(f"resume retry sequence mismatch: {attempt_root}")
            recomputed_attempts.append((passed, failures, actual_hashes))

        final_attempt = attempt_records[-1]
        if final_attempt.get("timedOut") is True and len(attempt_records) != max_attempts:
            raise RuntimeError(f"resume timeout result ended before retries were exhausted: {result_path}")
        passed, failures, artifact_hashes = recomputed_attempts[-1]
        timed_out = final_attempt["timedOut"]
        exit_code = final_attempt["exitCode"]
        reconstructed_status = (
            "infrastructure-error" if final_attempt.get("infrastructureError", False)
            else "oracle-pass" if passed
            else "timeout" if timed_out
            else "oracle-fail"
        )
        if (
            final_attempt.get("passed") is not passed
            or final_attempt.get("failures") != failures
            or existing.get("stdoutSha256") != final_attempt.get("stdoutSha256")
            or existing.get("stderrSha256") != final_attempt.get("stderrSha256")
            or existing.get("command") != final_attempt.get("command")
            or existing.get("status") != reconstructed_status
            or existing.get("exitCode") != exit_code
            or existing.get("oracleFailures") != failures
            or existing.get("artifactSha256") != artifact_hashes
        ):
            raise RuntimeError(f"resume result outcome mismatch: {result_path}")

        rebound = {
            **existing,
            "jobId": job_id,
            "caseId": case["id"],
            "group": case["group"],
            "relation": case["relation"],
            "criterionIds": case["criterionIds"],
            "agentCli": case.get("agentCli"),
            "repeat": repeat,
            "description": case["description"],
            "status": reconstructed_status,
            "exitCode": exit_code,
            "oracleFailures": failures,
            "artifactSha256": artifact_hashes,
        }
        if persist_resume_rebind:
            atomic_write_json(
                result_path, rebound, root=job_root, inherited_names=known_inherited
            )
        return rebound
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
        atomic_write_json(
            result_path, result, root=job_root, inherited_names=known_inherited
        )
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
    attempts_root = create_or_validate_directory(
        job_root, job_root / "attempts", "attempts directory"
    )
    for attempt in range(1, retries + 2):
        attempt_root = create_or_validate_directory(
            attempts_root, attempts_root / str(attempt), "attempt directory"
        )
        attempt_evidence = create_or_validate_directory(
            attempt_root, attempt_root / "evidence", "attempt evidence directory"
        )
        attempt_name = safe_name(f"acv-{run_root}-{run_id}-{job_id}-a{attempt}")
        attempt_args, inherited = build_container_args(manifest, case, attempt_name, attempt_evidence, base)
        started = time.monotonic()
        timed_out = False
        infrastructure_failed = False
        try:
            completed = run_capture(attempt_args, timeout=timeout)
            exit_code = completed.returncode
            raw_stdout, raw_stderr = completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = None
            raw_stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
            raw_stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
            try:
                cleanup = subprocess.run(
                    ["container", "delete", "--force", attempt_name],
                    text=True, capture_output=True, check=False,
                    timeout=CONTAINER_CLEANUP_TIMEOUT_SECONDS,
                )
                if cleanup.returncode != 0:
                    raise RuntimeError("container cleanup returned nonzero")
            except subprocess.TimeoutExpired:
                timed_out = False
                infrastructure_failed = True
                raw_stderr += "\nrunner timeout cleanup timed out"
            except Exception:
                # Cleanup is part of this attempt. Bind the failure rather than
                # leaving a timeout directory that no result authenticates.
                timed_out = False
                infrastructure_failed = True
                raw_stderr += "\nrunner timeout cleanup failure"
        except Exception as exc:
            infrastructure_failed = True
            exit_code = None
            raw_stdout = ""
            raw_stderr = redact_inherited_text(
                "runner infrastructure failure: " + str(exc), known_inherited
            )
        secret_artifact_failures = sanitize_artifacts(attempt_evidence, known_inherited)
        if infrastructure_failed:
            passed, raw_failures = False, [
                "runner timeout cleanup timed out"
                if "runner timeout cleanup timed out" in raw_stderr
                else "runner timeout cleanup failure"
                if "runner timeout cleanup failure" in raw_stderr
                else "runner infrastructure failure"
            ]
        else:
            passed, raw_failures = check_oracle(
                case, exit_code, timed_out, raw_stdout, raw_stderr, attempt_evidence
            )
        stdout = redact_inherited_text(raw_stdout, known_inherited)
        stderr = redact_inherited_text(raw_stderr, known_inherited)
        failures = [redact_inherited_text(item, known_inherited) for item in raw_failures]
        for item in secret_artifact_failures:
            if item not in failures:
                failures.append(item)
        if secret_artifact_failures:
            passed = False
        attempt_stdout = attempt_root / "stdout.log"
        attempt_stderr = attempt_root / "stderr.log"
        atomic_write_text(
            attempt_stdout, stdout, root=attempt_root, inherited_names=known_inherited
        )
        atomic_write_text(
            attempt_stderr, stderr, root=attempt_root, inherited_names=known_inherited
        )
        attempt_artifact_hashes, artifact_failures = collect_artifact_hashes(attempt_evidence)
        if artifact_failures:
            failures.extend(
                redact_inherited_text(item, known_inherited) for item in artifact_failures
            )
            passed = False
        attempt_redacted = redact_command(attempt_args, inherited)
        attempts.append({
            "attempt": attempt,
            "containerName": attempt_name,
            "command": attempt_redacted,
            "exitCode": exit_code,
            "timedOut": timed_out,
            "infrastructureError": infrastructure_failed,
            "durationSeconds": round(time.monotonic() - started, 3),
            "passed": passed,
            "failures": failures,
            "stdoutSha256": sha256_file(attempt_stdout),
            "stderrSha256": sha256_file(attempt_stderr),
            "artifactSha256": attempt_artifact_hashes,
        })
        final_stdout, final_stderr, final_exit, final_timeout = stdout, stderr, exit_code, timed_out
        evidence = attempt_evidence
        if infrastructure_failed or passed or not timed_out:
            break
    atomic_write_text(
        stdout_path, final_stdout, root=job_root, inherited_names=known_inherited
    )
    atomic_write_text(
        stderr_path, final_stderr, root=job_root, inherited_names=known_inherited
    )
    artifact_hashes, final_artifact_failures = collect_artifact_hashes(evidence)
    if final_artifact_failures:
        for item in final_artifact_failures:
            redacted_failure = redact_inherited_text(item, known_inherited)
            if redacted_failure not in failures:
                failures.append(redacted_failure)
        passed = False
    result = {
        "jobId": job_id,
        "caseId": case["id"],
        "group": case["group"],
        "relation": case["relation"],
        "criterionIds": case["criterionIds"],
        "agentCli": case.get("agentCli"),
        "repeat": repeat,
        "status": (
            "infrastructure-error" if attempts[-1].get("infrastructureError")
            else "oracle-pass" if passed
            else "timeout" if final_timeout
            else "oracle-fail"
        ),
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
    atomic_write_json(
        result_path, result, root=job_root, inherited_names=known_inherited
    )
    return result


def _markdown_inert(value: Any) -> str:
    """Return single-line text whose dynamic ASCII punctuation is parser-inert."""
    normalized = " ".join(
        "".join(
            " " if ord(char) < 32 or 0x7F <= ord(char) <= 0x9F else char
            for char in str(value)
        ).split()
    )
    return "".join(
        f"&#{ord(char)};" if 0x21 <= ord(char) <= 0x2F
        or 0x3A <= ord(char) <= 0x40
        or 0x5B <= ord(char) <= 0x60
        or 0x7B <= ord(char) <= 0x7E
        else char
        for char in normalized
    )


def markdown_inline(value: Any) -> str:
    return _markdown_inert(value)


def markdown_code(value: Any) -> str:
    return _markdown_inert(value)


def markdown_cell(value: Any) -> str:
    return _markdown_inert(value)


def render_report(
    manifest: dict[str, Any], summary: dict[str, Any], run_root: Path,
    report_name: str = "report.md",
) -> str:
    rows = []
    labeled_results: list[tuple[str, dict[str, Any]]] = []
    anonymous = 0
    for result in summary.get("results", []):
        job_id = result.get("jobId") if isinstance(result, dict) else None
        if not isinstance(job_id, str) or not job_id:
            anonymous += 1
            job_id = f"<anonymous-{anonymous}>"
        labeled_results.append((job_id, result if isinstance(result, dict) else {}))
    for job_id, result in sorted(labeled_results, key=lambda item: item[0]):
        failures_value = result.get("oracleFailures", [])
        failures = "; ".join(str(item) for item in failures_value) if isinstance(failures_value, list) else str(failures_value)
        cells = [
            job_id, result.get("group", "—"), result.get("relation", "—"),
            result.get("status", "other/unadjudicated"), result.get("durationSeconds", 0),
            failures or "—",
        ]
        rows.append("| " + " | ".join(markdown_cell(cell) for cell in cells) + " |")
    evidence_entries = ["run-manifest.json", "image-inspect.json", "summary.json", report_name]
    if (run_root / "image-build.log").is_file():
        evidence_entries.append("image-build.log")
    jobs_root = run_root / "jobs"
    if jobs_root.is_dir() and not jobs_root.is_symlink():
        for path in sorted(jobs_root.rglob("*")):
            if path.is_file() and not path.is_symlink():
                evidence_entries.append(str(path.relative_to(run_root)))
    evidence_lines = "\n".join(f"- `{markdown_code(entry)}`" for entry in evidence_entries)
    report = f"""# Apple Container検証レポート: {markdown_inline(manifest['claim'])}

## ステータス

- Preflight/report disposition: **READY**
- Disposition note: host preflight passed and the runner emitted this report; READY does not mean execution completed or the claim was supported.
- Run ID: `{markdown_inline(summary['runId'])}`
- Claim outcome: **{markdown_inline(summary['claimOutcome'])}**
- Execution status: **{markdown_inline(summary['executionStatus'])}**
- 判定済みジョブ: {summary['counts'].get('oracle-pass', 0) + summary['counts'].get('oracle-fail', 0)} / {summary['jobs']}
- オラクル成立: {summary['counts'].get('oracle-pass', 0)}
- オラクル不成立: {summary['counts'].get('oracle-fail', 0)}
- タイムアウト: {summary['counts'].get('timeout', 0)}
- 基盤エラー: {summary['counts'].get('infrastructure-error', 0)}
- Dry runジョブ: {summary['counts'].get('dry-run', 0)}
- 未判定・未知状態: {summary['counts'].get('other/unadjudicated', 0)}

## 仮説

{markdown_inline(manifest['hypothesis'])}

### 棄却条件

""" + "\n".join(
        f"- `{markdown_inline(item['id'])}`: {markdown_inline(item['description'])}"
        for item in manifest["falsificationCriteria"]
    ) + f"""

## 環境と来歴

- Apple Container: `{markdown_inline(summary['provenance']['containerVersion'])}`
- Host: `{markdown_inline(summary['provenance']['host'])}`
- Image: `{markdown_inline(manifest['image']['tag'])}`
- Image inspect SHA-256: `{markdown_inline(summary['provenance']['imageInspectSha256'])}`
- Manifest SHA-256: `{markdown_inline(summary['provenance']['manifestSha256'])}`
- Tree hash exclusions: `{markdown_inline(json.dumps(summary['provenance'].get('treeHashExclusions', {}), ensure_ascii=False, sort_keys=True))}`
- 実行開始: `{markdown_inline(summary['startedAt'])}`
- 実行終了: `{markdown_inline(summary['completedAt'])}`
- 並列度: {markdown_inline(summary['concurrency'])}
- Agent CLI: `{markdown_inline(', '.join(sorted({case.get('agentCli') for case in manifest['cases'] if isinstance(case.get('agentCli'), str)})) or 'none')}`
- Authentication verification: `{markdown_inline(summary.get('authenticationVerification', 'NOT VERIFIED BY RUNNER'))}`
- Launcher-origin verification: `{markdown_inline(summary.get('launcherOriginVerification', 'NOT VERIFIED BY RUNNER'))}`
- Claim evaluation qualification: `{markdown_inline(summary.get('claimEvaluationQualification', 'PROVISIONAL'))}`

`claimOutcome`はrelation/oracle集約だが、launcher由来が検証済みでない限り暫定評価である。CIは`claimOutcome`単独を主張真偽のgateにせず、完了確認には`executionStatus`を使い、主張受理には外部または記録済みのlauncher-origin attestationを必須とする。

## ケース結果

| Job | Group | Relation | Status | Seconds | Oracle failure |
|---|---|---|---:|---:|---|
""" + "\n".join(rows) + """

## 観察

自動判定結果と `jobs/*/attempts/*/stdout.log`、`jobs/*/attempts/*/stderr.log` を照合し、観察事実を記述する。`jobs/*/stdout.log`と`jobs/*/stderr.log`は最終attemptの写しであり、以前のtimeout証跡は`attempts/`配下に残る。

## 推論

観察から支持される範囲だけを記述する。一意な期待`falsify`の`oracle-pass`は未完了runでも反証になる。支持には、全`support`の`oracle-pass`、全`falsify`の判定済み`oracle-fail`、および重複・期待外・匿名結果がないことを要する。`neutral`だけの欠損や未判定は支持証拠を消さない。

## 反証・限界・未検証事項

対象外の環境、測定誤差、並列干渉、外部依存、未実行ケースを記述する。

## 再実行

```bash
python3 scripts/run-matrix.py path/to/manifest.json --run-id NEW_RUN_ID --concurrency auto
```

## 証跡

""" + evidence_lines + "\n"
    return report


def write_report(
    manifest: dict[str, Any], summary: dict[str, Any], run_root: Path,
    inherited_names: set[str] | None = None,
) -> None:
    """互換用convenience reportを安全に生成する。権威あるpublishはmainが行う。"""
    atomic_write_text(
        run_root / "report.md", render_report(manifest, summary, run_root), root=run_root,
        inherited_names=inherited_names or set(),
    )


def assert_no_inherited_values_in_files(root: Path, inherited_names: set[str]) -> None:
    secrets_to_find = [value.encode("utf-8") for value in inherited_values(inherited_names)]
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        if any(secret in data for secret in secrets_to_find):
            raise RuntimeError(f"known inherited value remains in runner-owned file: {path}")


def publish_authoritative_summary_report(
    manifest: dict[str, Any], summary: dict[str, Any], run_root: Path,
    inherited_names: set[str] | None = None,
    diagnostic_sink: Callable[[str], None] | None = None,
) -> tuple[dict[str, Any], Path]:
    names = inherited_names or set()
    values = inherited_values(names)
    safe_manifest = redact_inherited_structure(manifest, names)
    safe_summary = redact_inherited_structure(summary, names)
    # This audit is deliberately before either authoritative commit point.
    assert_no_inherited_values_in_files(run_root, names)
    report_path: Path | None = None
    report_text = ""
    committed: dict[str, Any] = {}
    summary_bytes = b""
    report_bytes = b""
    for _ in range(1024):
        generation = secrets.token_hex(16)
        report_name = f"report.{generation}.md"
        if any(value in report_name for value in values):
            continue
        report_text = render_report(safe_manifest, safe_summary, run_root, report_name)
        report_bytes = safe_text_bytes(report_text, names)
        report_hash = sha256_bytes(report_bytes)
        if any(value in report_hash for value in values):
            continue
        committed = {
            **safe_summary,
            "reportArtifact": {"path": report_name, "sha256": report_hash},
        }
        # JSON punctuation may recreate a secret across fields; fail before report creation.
        summary_bytes = safe_json_bytes(committed, names)
        candidate = run_root / report_name
        try:
            atomic_create_bytes(candidate, report_bytes, root=run_root)
        except FileExistsError:
            continue
        report_path = candidate
        break
    if report_path is None:
        raise RuntimeError("could not allocate a secret-free immutable report generation")
    atomic_write_json(
        run_root / "summary.json", committed, root=run_root, inherited_names=names
    )
    # summary.json replacement is the authoritative commit. Only best-effort work follows.
    try:
        atomic_write_bytes(run_root / "report.md", report_bytes, root=run_root)
    except (OSError, RuntimeError) as exc:
        warning = (
            "WARNING: authoritative summary/report committed, but convenience report.md update failed: "
            + str(exc)
        )
        try:
            if diagnostic_sink is not None:
                diagnostic_sink(warning)
            else:
                # Standalone callers still check payload plus its final newline.
                payload = safe_text_bytes(warning + "\n", names)
                sys.stderr.write(payload.decode("utf-8"))
        except Exception:
            pass
    return committed, report_path


def _main(diagnostics: BufferedDiagnostics) -> int:
    argv = sys.argv[1:]
    inherited_names: set[str] = set()
    for token in argv:
        if token.startswith("-"):
            continue
        try:
            parsed_for_names = json.loads(Path(token).read_text(encoding="utf-8"))
            reject_lone_surrogates(parsed_for_names)
            inherited_names = extract_inherited_env_names(parsed_for_names)
            break
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
    diagnostics.set_inherited_names(inherited_names)

    parser = SilentArgumentParser(
        description="Apple Container検証行列を並列実行する", add_help=False
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--concurrency", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    try:
        args = parser.parse_args(argv)
    except CliArgumentError:
        diagnostics.add("ERROR: invalid arguments", stderr=True)
        return 2
    manifest_path = args.manifest.resolve()

    def safe_print(value: Any = "", *, file: Any = None) -> None:
        diagnostics.add(value, stderr=(file is sys.stderr))

    if any(ord(char) < 32 or 0x7F <= ord(char) <= 0x9F for char in str(args.manifest) + str(args.results_dir)):
        safe_print("ERROR: manifest/results pathに制御文字は使えない", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}", args.run_id):
        safe_print("ERROR: run-idが不正", file=sys.stderr)
        return 2

    try:
        manifest, errors, warnings = validate_manifest(manifest_path)
    except ValueError as exc:
        safe_print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            safe_print("ERROR: " + str(error), file=sys.stderr)
        return 1
    inherited_names = extract_inherited_env_names(manifest)
    diagnostics.set_inherited_names(inherited_names)

    for warning in warnings:
        safe_print("WARNING: " + redact_inherited_text(str(warning), inherited_names), file=sys.stderr)
    try:
        results_lexical = reject_lexical_symlinks(args.results_dir)
    except RuntimeError as exc:
        safe_print(
            "ERROR: " + redact_inherited_text(str(exc), inherited_names),
            file=sys.stderr,
        )
        return 2
    uses_inherited_environment = any(
        case.get("inheritEnv") for case in manifest.get("cases", []) if isinstance(case, dict)
    )
    if args.resume and uses_inherited_environment:
        safe_print(redact_inherited_text(
            "ERROR: --resume is disabled when any case uses inheritEnv; "
            "credential/config values are not persisted, so use a new run-id",
            inherited_names), file=sys.stderr)
        return 2
    if shutil.which("container") is None:
        safe_print(redact_inherited_text("ERROR: Apple Container CLI unavailable", inherited_names), file=sys.stderr)
        return 2
    if run_capture(["container", "--version"]).returncode != 0:
        safe_print(redact_inherited_text("ERROR: Apple Container CLI unavailable", inherited_names), file=sys.stderr)
        return 2
    status = run_capture(["container", "system", "status"])
    if status.returncode != 0 or "running" not in status.stdout:
        safe_print(redact_inherited_text("ERROR: Apple Container system is not running", inherited_names), file=sys.stderr)
        safe_print(redact_inherited_text(status.stdout + status.stderr, inherited_names), file=sys.stderr)
        return 2

    jobs = [
        (case, repeat)
        for case in manifest["cases"]
        for repeat in range(1, case.get("repeats", manifest["defaults"].get("repeats", 1)) + 1)
    ]
    expected_jobs = [
        {
            "jobId": f"{case['id']}-r{repeat}",
            "caseId": case["id"],
            "repeat": repeat,
            "group": case["group"],
            "relation": case["relation"],
            "criterionIds": case["criterionIds"],
        }
        for case, repeat in jobs
    ]
    if args.concurrency == "auto":
        concurrency = recommended_concurrency(manifest, len(jobs))
    else:
        try:
            concurrency = int(args.concurrency)
        except ValueError:
            safe_print(redact_inherited_text("ERROR: concurrencyはautoまたは正整数", inherited_names), file=sys.stderr)
            return 2
        if concurrency < 1:
            safe_print(redact_inherited_text("ERROR: concurrencyは1以上", inherited_names), file=sys.stderr)
            return 2
        concurrency = min(concurrency, manifest["defaults"].get("maxConcurrency", concurrency), len(jobs))
    if any(mount.get("readonly", True) is not True for mount in manifest.get("mounts", [])):
        concurrency = 1
        safe_print(redact_inherited_text("WARNING: shared writable mount forces concurrency=1", inherited_names), file=sys.stderr)

    try:
        results_root = create_results_directory(results_lexical)
    except (OSError, RuntimeError) as exc:
        safe_print(
            "ERROR: could not prepare results directory: "
            + redact_inherited_text(str(exc), inherited_names),
            file=sys.stderr,
        )
        return 2
    run_root = results_root / args.run_id
    run_manifest_path = run_root / "run-manifest.json"
    existing: dict[str, Any] | None = None
    if args.resume:
        if not os.path.lexists(run_root):
            safe_print(redact_inherited_text(
                f"ERROR: resume requires an existing committed run; use a new run-id: {run_root}",
                inherited_names), file=sys.stderr)
            return 2
        try:
            require_real_directory(run_root, run_root, "run directory")
            existing = load_json_object(
                run_manifest_path, root=run_root, label="committed run manifest"
            )
        except RuntimeError as exc:
            safe_print(
                "ERROR: " + redact_inherited_text(str(exc), inherited_names)
                + "; preserve this state and use a new run-id",
                file=sys.stderr,
            )
            return 2
    elif os.path.lexists(run_root):
        safe_print(redact_inherited_text(
            f"ERROR: run directory exists; preserve it and use a new run-id: {run_root}",
            inherited_names), file=sys.stderr)
        return 2
    base = manifest_path.parent
    container_version = redact_inherited_text(
        run_capture(["container", "--version"]).stdout.strip(), inherited_names
    )
    skill_root = Path(__file__).resolve().parent.parent
    try:
        manifest_hash = sha256_file(manifest_path)
        mount_inputs = {
            mount["source"]: resolve_mount_input(base, mount["source"], f"mount source {index}")
            for index, mount in enumerate(manifest.get("mounts", []))
        }
        image_context = (
            resolve_manifest_input(base, manifest["image"]["context"], directory=True, label="image.context")
            if "context" in manifest["image"] else None
        )
        containerfile = (
            resolve_manifest_input(base, manifest["image"]["file"], directory=False, label="image.file")
            if "file" in manifest["image"] else None
        )
        if image_context is not None and containerfile is not None:
            containerfile.relative_to(image_context)
        input_directories = [path for path in mount_inputs.values() if path.is_dir()]
        if image_context is not None:
            input_directories.append(image_context)
        validate_results_hash_layout(skill_root, results_root, input_directories)
        mount_hashes = {
            source: tree_sha256_excluding_results(input_path, results_root)
            for source, input_path in mount_inputs.items()
        }
        build_context_hash = (
            tree_sha256_excluding_results(image_context, results_root)
            if image_context is not None else None
        )
        tree_hash_exclusions = {
            "skillBundle": tree_hash_exclusion(skill_root, results_root),
            "imageContext": (
                tree_hash_exclusion(image_context, results_root) if image_context is not None else None
            ),
            "mountSources": {
                source: tree_hash_exclusion(input_path, results_root)
                for source, input_path in mount_inputs.items()
            },
        }
        static_provenance = {
            "version": 1,
            "runId": args.run_id,
            "manifest": redact_inherited_text(str(manifest_path), inherited_names),
            "manifestSha256": manifest_hash,
            "image": redact_inherited_structure(manifest["image"], inherited_names),
            "mountInputSha256": redact_inherited_structure(mount_hashes, inherited_names),
            "skillBundleSha256": tree_sha256_excluding_results(skill_root, results_root),
            "treeHashExclusions": tree_hash_exclusions,
            "containerfileSha256": sha256_file(containerfile) if containerfile is not None else None,
            "buildContextSha256": build_context_hash,
            "jobs": [{"caseId": case["id"], "repeat": repeat} for case, repeat in jobs],
            "concurrency": concurrency,
            "containerVersion": container_version,
            "host": f"{platform.system()} {platform.release()} {platform.machine()}",
        }
    except (OSError, RuntimeError, ValueError) as exc:
        safe_print(
            "ERROR: input/provenance validation failed: " + str(exc),
            file=sys.stderr,
        )
        return 2
    if existing is not None:
        created_at = existing.get("createdAt")
        if not isinstance(created_at, str):
            safe_print(
                "ERROR: existing committed run manifest lacks createdAt; "
                "preserve this state and use a new run-id",
                file=sys.stderr,
            )
            return 2
    else:
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            run_root.mkdir(mode=0o700, exist_ok=False)
            run_root.chmod(0o700)
            build_image(manifest, base, run_root, args.dry_run, inherited_names)
        except (OSError, RuntimeError) as exc:
            safe_print(
                "ERROR: could not initialize run state: "
                + redact_inherited_text(str(exc), inherited_names) + "; "
                "preserve any partial state and use a new run-id",
                file=sys.stderr,
            )
            return 2
    if args.dry_run:
        image_inspect_text = "dry-run: image not inspected\n"
    else:
        image_inspect = run_capture(["container", "image", "inspect", manifest["image"]["tag"]])
        image_inspect_text = redact_inherited_text(
            image_inspect.stdout + image_inspect.stderr, inherited_names
        )
        if image_inspect.returncode != 0:
            if existing is None:
                try:
                    atomic_write_text(
                        run_root / "image-inspect.json", image_inspect_text, root=run_root,
                        inherited_names=inherited_names,
                    )
                except (OSError, RuntimeError):
                    pass
            safe_print(redact_inherited_text("ERROR: image inspect failed", inherited_names), file=sys.stderr)
            safe_print(image_inspect_text, file=sys.stderr)
            return 2
    image_inspect_hash = sha256_bytes(image_inspect_text.encode("utf-8"))
    run_manifest = redact_inherited_structure({
        **static_provenance,
        "createdAt": created_at,
        "imageInspectSha256": image_inspect_hash,
    }, inherited_names)
    image_inspect_path = run_root / "image-inspect.json"
    if existing is not None:
        try:
            verify_persisted_image_inspect(run_root, existing, image_inspect_hash)
        except RuntimeError as exc:
            safe_print(
                "ERROR: " + redact_inherited_text(str(exc), inherited_names)
                + "; preserve this state and use a new run-id",
                file=sys.stderr,
            )
            return 2
        if existing != run_manifest:
            safe_print(redact_inherited_text("ERROR: resume provenance mismatch; use a new run-id", inherited_names), file=sys.stderr)
            return 2
    else:
        try:
            atomic_write_text(
                image_inspect_path, image_inspect_text, root=run_root,
                inherited_names=inherited_names,
            )
            atomic_write_json(
                run_manifest_path, run_manifest, root=run_root,
                inherited_names=inherited_names,
            )
        except (OSError, RuntimeError) as exc:
            safe_print(
                "ERROR: could not commit run provenance: "
                + redact_inherited_text(str(exc), inherited_names) + "; "
                "preserve this partial state and use a new run-id",
                file=sys.stderr,
            )
            return 2
    started_at = created_at
    expected_job_ids = {item["jobId"] for item in expected_jobs}
    try:
        create_or_validate_directory(run_root, run_root / "jobs", "jobs directory")
        inventory_job_tree(run_root, expected_job_ids)
    except RuntimeError as exc:
        safe_print(redact_inherited_text(
            "ERROR: invalid job tree: " + str(exc)
            + f"; move partial state outside {run_root} or use a new run-id",
            inherited_names), file=sys.stderr)
        return 2

    if args.resume:
        # Validate every pre-existing completed job before scheduling any new
        # work. A rejection leaves the entire existing jobs tree byte-for-byte
        # unchanged and leaves any old authoritative summary/report untouched.
        try:
            for case, repeat in jobs:
                completed_result = run_root / "jobs" / f"{case['id']}-r{repeat}" / "result.json"
                if os.path.lexists(completed_result):
                    execute_job(
                        manifest, case, repeat, args.run_id, run_root, base, False,
                        inherited_names, persist_resume_rebind=False,
                    )
        except RuntimeError:
            safe_print(
                "ERROR: resume evidence integrity rejection; existing job tree was preserved",
                file=sys.stderr,
            )
            return 2

    results: list[dict[str, Any]] = []
    shared_writable_mount = any(mount.get("readonly", True) is not True for mount in manifest.get("mounts", []))
    lock_groups = {case.get("exclusiveGroup") for case, _ in jobs if case.get("exclusiveGroup")}
    if shared_writable_mount:
        lock_groups.add("__shared_writable_mount__")
    exclusive_locks = {group: threading.Lock() for group in lock_groups}

    def scheduled_job(case: dict[str, Any], repeat: int) -> dict[str, Any]:
        def invoke() -> dict[str, Any]:
            try:
                return execute_job(
                    manifest, case, repeat, args.run_id, run_root, base, args.dry_run,
                    inherited_names, persist_resume_rebind=not args.resume,
                )
            except RuntimeError as exc:
                result_path = run_root / "jobs" / f"{case['id']}-r{repeat}" / "result.json"
                if args.resume and os.path.lexists(result_path):
                    raise ResumeIntegrityError("completed resume evidence failed integrity validation") from exc
                raise

        group = "__shared_writable_mount__" if shared_writable_mount else case.get("exclusiveGroup")
        if group is None:
            return invoke()
        with exclusive_locks[group]:
            return invoke()

    resume_integrity_rejected = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        future_jobs = {
            pool.submit(scheduled_job, case, repeat): (case, repeat)
            for case, repeat in jobs
        }
        for future in concurrent.futures.as_completed(future_jobs):
            case, repeat = future_jobs[future]
            try:
                result = future.result()
            except ResumeIntegrityError:
                # Never synthesize over a completed job rejected during resume.
                resume_integrity_rejected = True
                safe_print(
                    "ERROR: resume evidence integrity rejection; existing job tree was preserved",
                    file=sys.stderr,
                )
                continue
            except Exception as exc:  # job-level infrastructure failure must remain visible
                redacted_exception = redact_inherited_text(
                    str(exc), set(case.get("inheritEnv", []))
                )
                safe_print(redact_inherited_text(f"ERROR: job infrastructure failure: {redacted_exception}", inherited_names), file=sys.stderr)
                result = {
                    "jobId": f"{case['id']}-r{repeat}",
                    "caseId": case["id"],
                    "group": case["group"],
                    "relation": case["relation"],
                    "criterionIds": case["criterionIds"],
                    "agentCli": case.get("agentCli"),
                    "status": "infrastructure-error",
                    "oracleFailures": [redacted_exception],
                }
                job_root = run_root / "jobs" / f"{case['id']}-r{repeat}"
                create_or_validate_directory(run_root / "jobs", job_root, "infrastructure job directory")
                atomic_write_json(
                    job_root / "result.json", result, root=job_root,
                    inherited_names=inherited_names,
                )
            results.append(result)
            safe_print(redact_inherited_text(f"{result['status']}: {result['jobId']}", inherited_names))

    if resume_integrity_rejected:
        return 2

    completed_at = datetime.now(timezone.utc).isoformat()
    evaluation, run_exit_code = aggregate_run_results(results, expected_jobs, args.dry_run)
    has_agent_cli = any(case.get("agentCli") for case in manifest["cases"])
    has_claim_bearing = any(
        case.get("relation") in {"support", "falsify"} for case in manifest["cases"]
    )
    authentication_verification = (
        "NOT APPLICABLE" if not has_agent_cli else "NOT VERIFIED BY RUNNER"
    )
    launcher_origin_verification = (
        "NOT APPLICABLE"
        if args.dry_run or not has_claim_bearing
        else "NOT VERIFIED BY RUNNER"
    )
    claim_qualification = (
        "PROVISIONAL"
        if launcher_origin_verification == "NOT VERIFIED BY RUNNER"
        else "NOT APPLICABLE"
    )
    summary = {
        **evaluation,
        "runId": args.run_id,
        "concurrency": concurrency,
        "startedAt": started_at,
        "completedAt": completed_at,
        "authenticationVerification": authentication_verification,
        "launcherOriginVerification": launcher_origin_verification,
        "claimEvaluationQualification": claim_qualification,
        "provenance": {
            "manifestSha256": manifest_hash,
            "imageInspectSha256": image_inspect_hash,
            "mountInputSha256": mount_hashes,
            "buildContextSha256": build_context_hash,
            "skillBundleSha256": run_manifest["skillBundleSha256"],
            "treeHashExclusions": tree_hash_exclusions,
            "containerVersion": container_version,
            "host": run_manifest["host"],
        },
        "results": results,
    }
    try:
        inventory_job_tree(run_root, expected_job_ids, require_complete=True)
        inventory_run_root(run_root)
        _, authoritative_report = publish_authoritative_summary_report(
            manifest, summary, run_root, inherited_names,
            diagnostic_sink=lambda message: safe_print(message, file=sys.stderr),
        )
    except (OSError, RuntimeError) as exc:
        safe_error = redact_inherited_text(str(exc), inherited_names)
        safe_print(redact_inherited_text(
            f"ERROR: could not publish authoritative summary/report: {safe_error}; "
            f"move partial state outside {run_root} or use a new run-id",
            inherited_names), file=sys.stderr)
        return 2
    safe_print(redact_inherited_text(f"SUMMARY: {run_root / 'summary.json'}", inherited_names))
    safe_print(redact_inherited_text(f"REPORT: {authoritative_report}", inherited_names))
    return run_exit_code


def main() -> int:
    diagnostics = BufferedDiagnostics()
    exit_code = 2
    try:
        exit_code = _main(diagnostics)
    except (UnicodeEncodeError, UnicodeDecodeError):
        diagnostics.records = ["ERROR: invalid Unicode scalar value"]
        exit_code = 2
    finally:
        diagnostics.flush(success=exit_code == 0)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
