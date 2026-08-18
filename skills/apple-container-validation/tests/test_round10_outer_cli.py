#!/usr/bin/env python3
"""Round-10 outer CLI regressions."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "scripts" / "run-matrix.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate-manifest.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load(RUNNER_PATH, "acv_round10_runner")
VALIDATOR = load(VALIDATOR_PATH, "acv_round10_validator")


def manifest(overrides=None):
    case = {
        "id": "falsify-case", "group": "negative", "description": "description",
        "relation": "falsify", "criterionIds": ["criterion"], "command": ["true"],
        "oracle": {"stdoutContains": ["payload-marker"]},
    }
    case.update(overrides or {})
    return {
        "version": 1, "slug": "round-ten", "claim": "claim", "hypothesis": "hypothesis",
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


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode() + b"\0")
        digest.update(str(path.lstat().st_mode).encode() + b"\0")
        if path.is_file() and not path.is_symlink():
            digest.update(path.read_bytes())
    return digest.hexdigest()


class SingleChannelAndArgumentTests(unittest.TestCase):
    def test_validator_and_runner_use_exactly_one_channel(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "manifest.json"
            path.write_text(json.dumps(manifest()), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(VALIDATOR_PATH), str(path)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(0, completed.returncode)
            self.assertTrue(completed.stdout)
            self.assertEqual("", completed.stderr)

            stdout, stderr = io.StringIO(), io.StringIO()
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--dry-run", "--results-dir", str((base / "results").resolve())]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                RUNNER.shutil, "which", return_value="/bin/container"
            ), mock.patch.object(RUNNER, "run_capture", side_effect=capture), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                self.assertEqual(0, RUNNER.main())
            self.assertTrue(stdout.getvalue())
            self.assertEqual("", stderr.getvalue())

    def test_shared_sink_is_safe_for_success_and_failure_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest({"inheritEnv": ["TOKEN"]})), encoding="utf-8")
            validator_code = f'''import importlib.util,json,os,sys
p={str(VALIDATOR_PATH)!r}; s=importlib.util.spec_from_file_location("v",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
value=json.load(open({str(path)!r})); m.validate_manifest=lambda p:(value,[],["first"]); sys.argv=[p,{str(path)!r}]; raise SystemExit(m.main())'''
            runner_code = f'''import importlib.util,json,os,sys
p={str(RUNNER_PATH)!r}; s=importlib.util.spec_from_file_location("r",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
value=json.load(open({str(path)!r})); m.validate_manifest=lambda p:(value,[],["first"]); m.shutil.which=lambda x:None; sys.argv=[p,{str(path)!r},"--run-id","run"]; raise SystemExit(m.main())'''
            for code, secret, expected in (
                (validator_code, "first\nOK:", 0),
                (runner_code, "first\nERROR: Apple", 2),
            ):
                completed = subprocess.run(
                    [sys.executable, "-c", code], stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True,
                    env={**os.environ, "TOKEN": secret}, check=False,
                )
                self.assertEqual(expected, completed.returncode)
                self.assertNotIn(secret, completed.stdout)

    def test_bogus_secret_is_silent_and_shared_sink_safe(self):
        secret = "former-stdout\nERROR: former-stderr"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest({"inheritEnv": ["TOKEN"]})), encoding="utf-8")
            env = {**os.environ, "TOKEN": secret}
            for script, extra in (
                (VALIDATOR_PATH, ["--json"]),
                (RUNNER_PATH, ["--run-id", "run"]),
            ):
                completed = subprocess.run(
                    [sys.executable, str(script), str(path), *extra, "--bogus", secret],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    env=env, check=False,
                )
                self.assertEqual(2, completed.returncode)
                self.assertNotIn(secret, completed.stdout)
                self.assertNotIn("--bogus", completed.stdout)
                self.assertNotIn("usage:", completed.stdout.lower())


class UnicodeAndJsonTests(unittest.TestCase):
    def test_lone_surrogates_are_rejected_everywhere(self):
        variants = []
        for surrogate in ("\ud800", "\udfff"):
            variants.extend([
                ("claim", lambda value, s=surrogate: value.__setitem__("claim", s)),
                ("unknown-key", lambda value, s=surrogate: value.__setitem__(s, "x")),
                ("criterion", lambda value, s=surrogate: value["cases"][0].__setitem__("criterionIds", [s])),
                ("path", lambda value, s=surrogate: value["cases"][0]["oracle"].__setitem__("artifacts", [{"path": s, "exists": True}])),
                ("oracle", lambda value, s=surrogate: value["cases"][0]["oracle"].__setitem__("stdoutContains", [s])),
            ])
        for name, mutate in variants:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                value = manifest()
                mutate(value)
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(value, ensure_ascii=True), encoding="utf-8")
                for argv, module in (
                    (["validate-manifest.py", str(path), "--json"], VALIDATOR),
                    (["run-matrix.py", str(path), "--run-id", "run"], RUNNER),
                ):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        self.assertEqual(2, module.main())
                    self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())
                    if module is VALIDATOR:
                        json.loads(stdout.getvalue())
                        self.assertEqual("", stderr.getvalue())
                    else:
                        self.assertEqual("", stdout.getvalue())

    def test_over_limit_integer_is_generic_in_both_clis(self):
        raw = '{"version":' + ("9" * 5000) + '}'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(raw, encoding="utf-8")
            for argv, module in (
                (["validate-manifest.py", str(path)], VALIDATOR),
                (["validate-manifest.py", str(path), "--json"], VALIDATOR),
                (["run-matrix.py", str(path), "--run-id", "run"], RUNNER),
            ):
                stdout, stderr = io.StringIO(), io.StringIO()
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    self.assertEqual(2, module.main())
                output = stdout.getvalue() + stderr.getvalue()
                self.assertNotIn("Traceback", output)
                self.assertNotIn("9999999999", output)
                if "--json" in argv:
                    json.loads(stdout.getvalue())


class ResumeAndCleanupTests(unittest.TestCase):
    def test_non_utf8_resume_logs_preserve_entire_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "manifest.json"
            path.write_text(json.dumps(manifest()), encoding="utf-8")
            results = base / "results"
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve())]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                RUNNER.shutil, "which", return_value="/bin/container"
            ), mock.patch.object(RUNNER, "run_capture", side_effect=capture):
                self.assertEqual(0, RUNNER.main())
            root = results / "run"
            job = root / "jobs" / "falsify-case-r1"
            result_path = job / "result.json"
            result = json.loads(result_path.read_text())
            for relative in (
                Path("stdout.log"), Path("stderr.log"),
                Path("attempts/1/stdout.log"), Path("attempts/1/stderr.log"),
            ):
                (job / relative).write_bytes(b"\xff")
            bad_hash = hashlib.sha256(b"\xff").hexdigest()
            for field in ("stdoutSha256", "stderrSha256"):
                result[field] = bad_hash
                result["attempts"][0][field] = bad_hash
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            before = tree_hash(root)
            old_summary = (root / "summary.json").read_bytes()
            stderr = io.StringIO()
            with mock.patch.object(sys, "argv", argv + ["--resume"]), mock.patch.object(
                RUNNER.shutil, "which", return_value="/bin/container"
            ), mock.patch.object(RUNNER, "run_capture", side_effect=capture), contextlib.redirect_stderr(stderr):
                self.assertEqual(2, RUNNER.main())
            self.assertEqual(before, tree_hash(root))
            self.assertEqual(old_summary, (root / "summary.json").read_bytes())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_cleanup_timeout_is_finite_and_bound_to_attempt(self):
        def timeout_capture(args, **kwargs):
            if args[:2] == ["container", "run"]:
                raise subprocess.TimeoutExpired(args, 1, output=b"partial", stderr=b"late")
            return capture(args, **kwargs)

        seen = []
        def cleanup_timeout(*args, **kwargs):
            seen.append(kwargs.get("timeout"))
            raise subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "manifest.json"
            path.write_text(json.dumps(manifest()), encoding="utf-8")
            results = base / "results"
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve())]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                RUNNER.shutil, "which", return_value="/bin/container"
            ), mock.patch.object(RUNNER, "run_capture", side_effect=timeout_capture), mock.patch.object(
                RUNNER, "CONTAINER_CLEANUP_TIMEOUT_SECONDS", 0.01
            ), mock.patch.object(RUNNER.subprocess, "run", side_effect=cleanup_timeout):
                self.assertEqual(1, RUNNER.main())
            self.assertEqual([0.01], seen)
            result = json.loads((results / "run/jobs/falsify-case-r1/result.json").read_text())
            self.assertEqual("infrastructure-error", result["status"])
            self.assertEqual(["runner timeout cleanup timed out"], result["attempts"][0]["failures"])
            summary = json.loads((results / "run/summary.json").read_text())
            self.assertEqual("INCOMPLETE", summary["executionStatus"])


if __name__ == "__main__":
    unittest.main()
