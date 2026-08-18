#!/usr/bin/env python3
"""Round-9 CLI-boundary regressions."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load(ROOT / "scripts" / "run-matrix.py", "acv_round9_runner")
VALIDATOR = load(ROOT / "scripts" / "validate-manifest.py", "acv_round9_validator")


def manifest(overrides=None):
    case = {
        "id": "falsify-case", "group": "negative", "description": "description",
        "relation": "falsify", "criterionIds": ["criterion"], "command": ["true"],
        "oracle": {"stdoutContains": ["payload-marker"]},
    }
    case.update(overrides or {})
    return {
        "version": 1, "slug": "round-nine", "claim": "claim", "hypothesis": "hypothesis",
        "falsificationCriteria": [{"id": "criterion", "description": "criterion description"}],
        "image": {"tag": "example:1"}, "defaults": {"maxConcurrency": 1},
        "mounts": [], "cases": [case],
    }


def capture(args, **kwargs):
    if args == ["container", "--version"]:
        return mock.Mock(returncode=0, stdout="container 1\n", stderr="")
    if args == ["container", "system", "status"]:
        return mock.Mock(returncode=0, stdout="running\n", stderr="")
    if args[:3] == ["container", "image", "inspect"]:
        return mock.Mock(returncode=0, stdout="{}", stderr="")
    if args[:2] == ["container", "run"]:
        return mock.Mock(returncode=0, stdout="payload-marker\n", stderr="")
    raise AssertionError(args)


def tree_bytes_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root)).encode()
        digest.update(relative + b"\0" + oct(path.lstat().st_mode).encode() + b"\0")
        if path.is_file() and not path.is_symlink():
            digest.update(path.read_bytes())
    return digest.hexdigest()


class CompleteDiagnosticStreamTests(unittest.TestCase):
    def test_validator_payload_newline_and_cross_record_redaction(self):
        for secret, as_json in (("する\n", False), ("}\n", True)):
            with self.subTest(secret=repr(secret)), tempfile.TemporaryDirectory() as directory:
                value = manifest({"inheritEnv": ["TOKEN"]})
                if not as_json:
                    value["cases"][0]["relation"] = None
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                stdout, stderr = io.StringIO(), io.StringIO()
                argv = ["validate-manifest.py", str(path)] + (["--json"] if as_json else [])
                with mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False), mock.patch.object(
                    sys, "argv", argv
                ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    VALIDATOR.main()
                self.assertNotIn(secret, stdout.getvalue())
                self.assertNotIn(secret, stderr.getvalue())
                if as_json and stdout.getvalue():
                    json.loads(stdout.getvalue())

        secret = "first\nERROR"
        with tempfile.TemporaryDirectory() as directory:
            value = manifest({"inheritEnv": ["TOKEN"]})
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            stderr = io.StringIO()
            argv = ["validate-manifest.py", str(path)]
            with mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False), mock.patch.object(
                sys, "argv", argv
            ), mock.patch.object(
                VALIDATOR, "validate_manifest", return_value=(value, ["second"], ["first"])
            ), contextlib.redirect_stderr(stderr):
                self.assertEqual(1, VALIDATOR.main())
            self.assertNotIn(secret, stderr.getvalue())

    def test_runner_buffers_complete_stream(self):
        secret = "first\nERROR"
        value = manifest({"inheritEnv": ["TOKEN"]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            stderr = io.StringIO()
            argv = ["run-matrix.py", str(path), "--run-id", "run"]
            with mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False), mock.patch.object(
                sys, "argv", argv
            ), mock.patch.object(
                RUNNER, "validate_manifest", return_value=(value, [], ["first"])
            ), mock.patch.object(RUNNER.shutil, "which", return_value=None), contextlib.redirect_stderr(stderr):
                self.assertEqual(2, RUNNER.main())
            self.assertNotIn(secret, stderr.getvalue())


class InvalidManifestTests(unittest.TestCase):
    def test_malformed_metadata_and_criterion_ids_are_controlled(self):
        variants = [
            ("defaults-list", lambda value: value.__setitem__("defaults", [])),
            ("defaults-null", lambda value: value.__setitem__("defaults", None)),
            ("defaults-scalar", lambda value: value.__setitem__("defaults", 4)),
            ("repeats-list", lambda value: value["cases"][0].__setitem__("repeats", [])),
            ("group-list", lambda value: value["cases"][0].__setitem__("group", [])),
            ("cases-object", lambda value: value.__setitem__("cases", {})),
        ]
        variants += [
            (f"criterion-{index}", lambda value, invalid=invalid: value["cases"][0].__setitem__("criterionIds", invalid))
            for index, invalid in enumerate((None, "criterion", {}, ["criterion", 1]))
        ]
        for name, mutate in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                value = manifest()
                mutate(value)
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                for as_json in (False, True):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    argv = ["validate-manifest.py", str(path)] + (["--json"] if as_json else [])
                    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        code = VALIDATOR.main()
                    self.assertEqual(1, code)
                    self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())
                output = io.StringIO()
                argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(Path(directory) / "results")]
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(output):
                    self.assertEqual(1, RUNNER.main())
                self.assertNotIn("Traceback", output.getvalue())
                self.assertFalse((Path(directory) / "results").exists())

    def test_read_decode_failures_are_controlled(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, content in (("bad.json", b"{"), ("bad-utf8.json", b"\xff")):
                path = Path(directory) / name
                path.write_bytes(content)
                for module, argv in (
                    (VALIDATOR, ["validate-manifest.py", str(path)]),
                    (RUNNER, ["run-matrix.py", str(path), "--run-id", "run"]),
                ):
                    stderr = io.StringIO()
                    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                        self.assertEqual(2, module.main())
                    self.assertNotIn("Traceback", stderr.getvalue())


class InputHashTests(unittest.TestCase):
    def test_nested_fifo_and_socket_are_controlled_before_run_state(self):
        for kind in ("fifo", "socket"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                source = base / "input"
                source.mkdir()
                special = source / kind
                sock = None
                if kind == "fifo":
                    os.mkfifo(special)
                else:
                    sock = socket.socket(socket.AF_UNIX)
                    sock.bind(str(special))
                try:
                    value = manifest()
                    value["mounts"] = [{"source": "input", "target": "/input", "readonly": True}]
                    path = base / "manifest.json"
                    path.write_text(json.dumps(value), encoding="utf-8")
                    results = base / "results"
                    stderr = io.StringIO()
                    argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve()), "--dry-run"]
                    with mock.patch.object(sys, "argv", argv), mock.patch.object(
                        RUNNER.shutil, "which", return_value="/bin/container"
                    ), mock.patch.object(RUNNER, "run_capture", side_effect=capture), contextlib.redirect_stderr(stderr):
                        self.assertEqual(2, RUNNER.main())
                    self.assertIn("input/provenance validation failed", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertFalse((results / "run").exists())
                finally:
                    if sock is not None:
                        sock.close()


class ResumePreservationTests(unittest.TestCase):
    def test_tampered_completed_job_is_never_rewritten(self):
        def tamper_result_hash(job):
            path = job / "result.json"
            value = json.loads(path.read_text())
            value["stdoutSha256"] = "0" * 64
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

        tamperers = {
            "stdout": lambda job: (job / "stdout.log").write_text("tampered"),
            "stderr": lambda job: (job / "stderr.log").write_text("tampered"),
            "result-hash": tamper_result_hash,
            "attempt-hash": lambda job: (job / "attempts" / "1" / "stdout.log").write_text("tampered"),
            "evidence-hash": lambda job: (job / "attempts" / "1" / "evidence" / "rogue").write_text("tampered"),
        }
        for name, tamper in tamperers.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                path = base / "manifest.json"
                path.write_text(json.dumps(manifest()), encoding="utf-8")
                results = base / "results"
                argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve())]
                common = (
                    mock.patch.object(RUNNER.shutil, "which", return_value="/bin/container"),
                    mock.patch.object(RUNNER, "run_capture", side_effect=capture),
                )
                with mock.patch.object(sys, "argv", argv), common[0], common[1]:
                    self.assertEqual(0, RUNNER.main())
                run_root = results / "run"
                job = run_root / "jobs" / "falsify-case-r1"
                tamper(job)
                before_tree = tree_bytes_hash(run_root)
                old_summary = (run_root / "summary.json").read_bytes()
                stderr = io.StringIO()
                with mock.patch.object(sys, "argv", argv + ["--resume"]), mock.patch.object(
                    RUNNER.shutil, "which", return_value="/bin/container"
                ), mock.patch.object(RUNNER, "run_capture", side_effect=capture), contextlib.redirect_stderr(stderr):
                    self.assertEqual(2, RUNNER.main())
                self.assertEqual(before_tree, tree_bytes_hash(run_root))
                self.assertEqual(old_summary, (run_root / "summary.json").read_bytes())
                diagnostic = stderr.getvalue().lower()
                self.assertIn("error:", diagnostic)
                self.assertTrue("preserv" in diagnostic or "new run-id" in diagnostic)


class TimeoutCleanupAndMarkdownTests(unittest.TestCase):
    def test_timeout_cleanup_spawn_failure_is_bound_and_published(self):
        def timeout_capture(args, **kwargs):
            if args[:2] == ["container", "run"]:
                raise subprocess.TimeoutExpired(args, 1, output=b"partial", stderr=b"late")
            return capture(args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "manifest.json"
            path.write_text(json.dumps(manifest()), encoding="utf-8")
            results = base / "results"
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve())]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                RUNNER.shutil, "which", return_value="/bin/container"
            ), mock.patch.object(RUNNER, "run_capture", side_effect=timeout_capture), mock.patch.object(
                RUNNER.subprocess, "run", side_effect=OSError("delete spawn failed")
            ):
                self.assertEqual(1, RUNNER.main())
            run_root = results / "run"
            summary = json.loads((run_root / "summary.json").read_text())
            result = json.loads((run_root / "jobs" / "falsify-case-r1" / "result.json").read_text())
            self.assertEqual("INCOMPLETE", summary["executionStatus"])
            self.assertEqual(1, summary["counts"]["infrastructure-error"])
            self.assertEqual("infrastructure-error", result["status"])
            self.assertTrue(result["attempts"][0]["infrastructureError"])
            self.assertFalse(result["attempts"][0]["timedOut"])
            self.assertIn("cleanup failure", result["attempts"][0]["failures"][0])
            RUNNER.inventory_job_tree(run_root, {"falsify-case-r1"}, require_complete=True)

    def test_dynamic_report_text_is_strictly_inert(self):
        attack = "![img](https://x) [link](https://x) *em* _em_ <https://x> <b>x</b> # h `c` \\ |"
        value = manifest()
        value["claim"] = attack
        value["hypothesis"] = attack
        value["falsificationCriteria"][0]["description"] = attack
        report_summary = {
            "runId": "run", "claimOutcome": "UNVERIFIED", "executionStatus": "INCOMPLETE",
            "counts": {key: 0 for key in (*RUNNER.JOB_STATUS_KEYS, "other/unadjudicated")},
            "jobs": 1, "startedAt": "s", "completedAt": "e", "concurrency": 1,
            "provenance": {"containerVersion": "v", "host": "h", "imageInspectSha256": "i", "manifestSha256": "m"},
            "results": [{"jobId": attack, "status": "oracle-fail", "oracleFailures": [attack]}],
        }
        report = RUNNER.render_report(value, report_summary, Path("."))
        self.assertEqual(1, report.count("## ステータス"))
        for active in ("![", "](", "*em*", "_em_", "<https://", "<b>", "# h", "`c`"):
            self.assertNotIn(active, report)
        self.assertIn("&#33;&#91;img&#93;&#40;https&#58;&#47;&#47;x&#41;", report)


if __name__ == "__main__":
    unittest.main()
