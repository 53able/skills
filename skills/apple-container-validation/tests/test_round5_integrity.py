#!/usr/bin/env python3
"""Regression tests for round-5 oracle and filesystem integrity fixes."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

_RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "run-matrix.py"
_SPEC = importlib.util.spec_from_file_location("apple_container_run_matrix_round5", _RUNNER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"runnerを読み込めない: {_RUNNER_PATH}")
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)


def expected(job_id: str, relation: str) -> dict[str, Any]:
    return {"jobId": job_id, "relation": relation}


def result(job_id: str, status: str) -> dict[str, Any]:
    return {"jobId": job_id, "status": status}


class RawOracleRedactionTests(unittest.TestCase):
    @staticmethod
    def manifest() -> dict[str, Any]:
        return {
            "image": {"tag": "example:1"},
            "defaults": {"timeoutSeconds": 10, "retries": 0},
            "mounts": [],
        }

    @staticmethod
    def case(secret: str) -> dict[str, Any]:
        return {
            "id": "secret-case",
            "group": "target",
            "description": "secret must not leak",
            "relation": "support",
            "criterionIds": ["criterion-secret"],
            "command": ["true"],
            "inheritEnv": ["TOKEN"],
            "oracle": {
                "exitCode": 0,
                "stdoutContains": ["payload-ready"],
                "stdoutNotContains": [secret],
            },
        }

    def execute(self, root: Path, stdout: str, secret: str) -> dict[str, Any]:
        completed = mock.Mock(returncode=0, stdout=stdout, stderr="")
        with (
            mock.patch.dict(os.environ, {"TOKEN": secret}, clear=True),
            mock.patch.object(_RUNNER, "run_capture", return_value=completed),
        ):
            return _RUNNER.execute_job(
                self.manifest(), self.case(secret), 1, "raw-oracle", root, root, False
            )

    def test_raw_secret_leak_fails_oracle_but_persisted_evidence_is_redacted(self) -> None:
        secret = "TOPSECRET"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = self.execute(root, f"payload-ready {secret}\n", secret)
            job_root = root / "jobs" / "secret-case-r1"
            persisted_result = (job_root / "result.json").read_text(encoding="utf-8")
            attempt_log = (job_root / "attempts" / "1" / "stdout.log").read_text(
                encoding="utf-8"
            )
            top_log = (job_root / "stdout.log").read_text(encoding="utf-8")
        self.assertEqual("oracle-fail", actual["status"])
        self.assertEqual(attempt_log, top_log)
        self.assertNotIn(secret, attempt_log)
        self.assertNotIn(secret, persisted_result)
        self.assertNotIn(secret, json.dumps(actual))

    def test_normal_non_leaking_output_still_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            actual = self.execute(Path(directory), "payload-ready\n", "TOPSECRET")
        self.assertEqual("oracle-pass", actual["status"])
        self.assertEqual([], actual["oracleFailures"])


class DirectoryContainmentTests(unittest.TestCase):
    @staticmethod
    def manifest() -> dict[str, Any]:
        return {
            "image": {"tag": "example:1"},
            "defaults": {"timeoutSeconds": 10, "retries": 0},
            "mounts": [],
        }

    @staticmethod
    def case() -> dict[str, Any]:
        return {
            "id": "case",
            "group": "target",
            "description": "containment",
            "relation": "neutral",
            "criterionIds": ["criterion"],
            "command": ["true"],
            "oracle": {"exitCode": 0},
        }

    def test_symlinked_jobs_ancestor_with_absent_child_is_rejected(self) -> None:
        for dry_run in (True, False):
            with self.subTest(dry_run=dry_run), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                run_root = base / "run"
                outside = base / "outside"
                run_root.mkdir()
                outside.mkdir()
                (run_root / "jobs").symlink_to(outside, target_is_directory=True)
                with (
                    mock.patch.object(_RUNNER, "run_capture") as capture,
                    self.assertRaisesRegex(RuntimeError, "jobs directory.*symlink"),
                ):
                    _RUNNER.execute_job(
                        self.manifest(), self.case(), 1, "containment", run_root, base, dry_run
                    )
                capture.assert_not_called()
                self.assertFalse((outside / "case-r1").exists())
                self.assertTrue((run_root / "jobs").is_symlink())


class AtomicPublicationTests(unittest.TestCase):
    def test_legacy_predictable_temp_symlink_cannot_modify_victim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "summary.json"
            victim = root / "victim.txt"
            victim.write_text("victim-old\n", encoding="utf-8")
            legacy_temp = root / (
                f".summary.json.{os.getpid()}.{_RUNNER.threading.get_ident()}.tmp"
            )
            legacy_temp.symlink_to(victim)
            _RUNNER.atomic_write_text(destination, "published\n", root=root)
            self.assertEqual("victim-old\n", victim.read_text(encoding="utf-8"))
            self.assertEqual("published\n", destination.read_text(encoding="utf-8"))
            self.assertTrue(legacy_temp.is_symlink())

    def test_existing_destination_symlink_is_replaced_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "victim.txt"
            victim.write_text("victim-old\n", encoding="utf-8")
            destination = root / "summary.json"
            destination.symlink_to(victim)
            _RUNNER.atomic_write_text(destination, "published\n", root=root)
            self.assertFalse(destination.is_symlink())
            self.assertEqual("published\n", destination.read_text(encoding="utf-8"))
            self.assertEqual("victim-old\n", victim.read_text(encoding="utf-8"))

    def test_fdopen_failure_cleans_exclusive_temp_and_preserves_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "summary.json"
            destination.write_text("old\n", encoding="utf-8")
            with mock.patch.object(_RUNNER.os, "fdopen", side_effect=OSError("write failed")):
                with self.assertRaisesRegex(OSError, "write failed"):
                    _RUNNER.atomic_write_text(destination, "new\n", root=root)
            self.assertEqual("old\n", destination.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(".summary.json.*.tmp")))

    def test_ordinary_atomic_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "report.md"
            _RUNNER.atomic_write_text(destination, "report\n", root=root)
            self.assertEqual("report\n", destination.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(".report.md.*.tmp")))


class ConservativeSupportTests(unittest.TestCase):
    def test_support_outcome_integrity_matrix(self) -> None:
        expected_jobs = [
            expected("support-r1", "support"),
            expected("falsify-r1", "falsify"),
            expected("neutral-r1", "neutral"),
        ]
        cases = (
            (
                "complete",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail"), result("neutral-r1", "oracle-pass")],
                ("COMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 0),
            ),
            (
                "neutral-missing",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail")],
                ("INCOMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 1),
            ),
            (
                "neutral-timeout",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail"), result("neutral-r1", "timeout")],
                ("INCOMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 1),
            ),
            (
                "falsify-missing",
                [result("support-r1", "oracle-pass"), result("neutral-r1", "oracle-pass")],
                ("INCOMPLETE", "UNVERIFIED", 1),
            ),
            (
                "falsify-timeout",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "timeout"), result("neutral-r1", "oracle-pass")],
                ("INCOMPLETE", "UNVERIFIED", 1),
            ),
            (
                "unexpected-extra",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail"), result("neutral-r1", "oracle-pass"), result("extra-r1", "oracle-pass")],
                ("INCOMPLETE", "UNVERIFIED", 1),
            ),
            (
                "anonymous-extra",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail"), result("neutral-r1", "oracle-pass"), {"status": "oracle-pass"}],
                ("INCOMPLETE", "UNVERIFIED", 1),
            ),
            (
                "duplicate-neutral",
                [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail"), result("neutral-r1", "oracle-pass"), result("neutral-r1", "oracle-pass")],
                ("INCOMPLETE", "UNVERIFIED", 1),
            ),
        )
        for name, results, outcome in cases:
            with self.subTest(name=name):
                self.assertEqual(outcome, _RUNNER.evaluate_run(results, expected_jobs, False))

    def test_unique_falsify_pass_takes_precedence_over_integrity_anomaly(self) -> None:
        expected_jobs = [
            expected("support-r1", "support"),
            expected("falsify-r1", "falsify"),
        ]
        results = [
            result("support-r1", "timeout"),
            result("falsify-r1", "oracle-pass"),
            {"status": "oracle-pass"},
        ]
        self.assertEqual(
            ("INCOMPLETE", "FALSIFIED", 1),
            _RUNNER.evaluate_run(results, expected_jobs, False),
        )

    def test_duplicate_falsify_pass_does_not_falsify(self) -> None:
        expected_jobs = [expected("falsify-r1", "falsify")]
        results = [
            result("falsify-r1", "oracle-pass"),
            result("falsify-r1", "oracle-pass"),
        ]
        self.assertEqual(
            ("INCOMPLETE", "UNVERIFIED", 1),
            _RUNNER.evaluate_run(results, expected_jobs, False),
        )


if __name__ == "__main__":
    unittest.main()
