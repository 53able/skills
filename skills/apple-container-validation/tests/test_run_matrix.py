#!/usr/bin/env python3
"""Contract tests for apple-container-validation run aggregation and resume."""
from __future__ import annotations

import importlib.util
import json
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

_RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "run-matrix.py"
_RUNNER_SPEC = importlib.util.spec_from_file_location("apple_container_run_matrix", _RUNNER_PATH)
if _RUNNER_SPEC is None or _RUNNER_SPEC.loader is None:
    raise RuntimeError(f"runnerを読み込めない: {_RUNNER_PATH}")
_RUNNER = importlib.util.module_from_spec(_RUNNER_SPEC)
_RUNNER_SPEC.loader.exec_module(_RUNNER)


def expected(job_id: str, relation: str) -> dict[str, Any]:
    return {"jobId": job_id, "relation": relation}


def result(job_id: str, status: str, relation: str = "neutral") -> dict[str, Any]:
    return {"jobId": job_id, "status": status, "relation": relation}


class EvaluateRunTests(unittest.TestCase):
    def assert_evaluation(
        self,
        results: list[dict[str, Any]],
        expected_jobs: list[dict[str, Any]],
        outcome: tuple[str, str, int],
        *,
        dry_run: bool = False,
    ) -> None:
        self.assertEqual(outcome, _RUNNER.evaluate_run(results, expected_jobs, dry_run))

    def test_complete_supported_requires_all_expected_support_jobs(self) -> None:
        expected_jobs = [expected("support-r1", "support"), expected("falsify-r1", "falsify")]
        self.assert_evaluation(
            [result("support-r1", "oracle-pass"), result("falsify-r1", "oracle-fail")],
            expected_jobs,
            ("COMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 0),
        )

    def test_incomplete_falsified_preserves_available_evidence(self) -> None:
        expected_jobs = [expected("falsify-r1", "falsify"), expected("other-r1", "neutral")]
        for incomplete_status in ("timeout", "infrastructure-error"):
            with self.subTest(status=incomplete_status):
                self.assert_evaluation(
                    [
                        result("falsify-r1", "oracle-pass", "support"),
                        result("other-r1", incomplete_status),
                    ],
                    expected_jobs,
                    ("INCOMPLETE", "FALSIFIED", 1),
                )

    def test_incomplete_neutral_does_not_erase_complete_support(self) -> None:
        expected_jobs = [expected("support-r1", "support"), expected("neutral-r1", "neutral")]
        self.assert_evaluation(
            [result("support-r1", "oracle-pass"), result("neutral-r1", "timeout")],
            expected_jobs,
            ("INCOMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 1),
        )
        self.assert_evaluation(
            [result("support-r1", "oracle-pass")],
            expected_jobs,
            ("INCOMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 1),
        )

    def test_missing_or_unadjudicated_support_is_unverified(self) -> None:
        expected_jobs = [expected("support-r1", "support"), expected("neutral-r1", "neutral")]
        for results in (
            [result("neutral-r1", "oracle-pass")],
            [result("support-r1", "timeout"), result("neutral-r1", "oracle-pass")],
            [result("support-r1", "unknown"), result("neutral-r1", "oracle-pass")],
            [{"jobId": "support-r1"}, result("neutral-r1", "oracle-pass")],
        ):
            with self.subTest(results=results):
                self.assert_evaluation(results, expected_jobs, ("INCOMPLETE", "UNVERIFIED", 1))

    def test_duplicate_missing_and_unexpected_ids_are_incomplete(self) -> None:
        expected_jobs = [expected("support-r1", "support")]
        unverified_cases = (
            [result("support-r1", "oracle-pass"), result("support-r1", "oracle-pass")],
            [],
            [{"status": "oracle-pass"}],
        )
        for results in unverified_cases:
            with self.subTest(results=results):
                self.assert_evaluation(results, expected_jobs, ("INCOMPLETE", "UNVERIFIED", 1))
        for results in (
            [result("support-r1", "oracle-pass"), result("unexpected-r1", "oracle-pass")],
            [result("support-r1", "oracle-pass"), {"status": "oracle-pass"}],
        ):
            with self.subTest(extra_results=results):
                self.assert_evaluation(
                    results,
                    expected_jobs,
                    ("INCOMPLETE", "UNVERIFIED", 1),
                )

    def test_duplicate_falsify_evidence_is_not_counted(self) -> None:
        expected_jobs = [expected("falsify-r1", "falsify")]
        self.assert_evaluation(
            [result("falsify-r1", "oracle-pass"), result("falsify-r1", "oracle-pass")],
            expected_jobs,
            ("INCOMPLETE", "UNVERIFIED", 1),
        )

    def test_no_support_is_unverified(self) -> None:
        expected_jobs = [expected("neutral-r1", "neutral"), expected("falsify-r1", "falsify")]
        self.assert_evaluation(
            [result("neutral-r1", "oracle-pass"), result("falsify-r1", "oracle-fail")],
            expected_jobs,
            ("COMPLETE", "UNVERIFIED", 0),
        )

    def test_falsify_precedes_failed_support_and_uses_expected_relation(self) -> None:
        expected_jobs = [expected("support-r1", "support"), expected("falsify-r1", "falsify")]
        self.assert_evaluation(
            [
                result("support-r1", "oracle-fail", "falsify"),
                result("falsify-r1", "oracle-pass", "support"),
            ],
            expected_jobs,
            ("COMPLETE", "FALSIFIED", 0),
        )

    def test_order_independent_with_repeats(self) -> None:
        expected_jobs = [expected("support-r1", "support"), expected("support-r2", "support")]
        passing = [result("support-r2", "oracle-pass"), result("support-r1", "oracle-pass")]
        self.assert_evaluation(passing, expected_jobs, ("COMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 0))
        self.assert_evaluation(list(reversed(passing)), list(reversed(expected_jobs)), ("COMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 0))
        self.assert_evaluation(
            [result("support-r1", "oracle-pass"), result("support-r2", "oracle-fail")],
            expected_jobs,
            ("COMPLETE", "UNVERIFIED", 0),
        )

    def test_duplicate_expected_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate expected job IDs"):
            _RUNNER.evaluate_run(
                [result("same-r1", "oracle-pass")],
                [expected("same-r1", "support"), expected("same-r1", "support")],
                False,
            )

    def test_dry_run_requires_every_expected_job_exactly_once(self) -> None:
        expected_jobs = [expected("support-r1", "support")]
        self.assert_evaluation(
            [result("support-r1", "dry-run")],
            expected_jobs,
            ("DRY RUN", "UNVERIFIED", 0),
            dry_run=True,
        )
        failing_results = (
            [],
            [result("support-r1", "infrastructure-error")],
            [result("support-r1", "future-status")],
            [result("support-r1", "dry-run"), result("support-r1", "dry-run")],
            [result("support-r1", "dry-run"), result("unexpected-r1", "dry-run")],
        )
        for results in failing_results:
            with self.subTest(results=results):
                self.assert_evaluation(
                    results,
                    expected_jobs,
                    ("INCOMPLETE", "UNVERIFIED", 1),
                    dry_run=True,
                )


class AggregationContractTests(unittest.TestCase):
    def test_status_outcome_exit_contract_matrix(self) -> None:
        matrix = (
            ("complete-supported", [expected("s", "support")], [result("s", "oracle-pass")], False, "COMPLETE", "SUPPORTED WITHIN TESTED SCOPE", 0),
            ("complete-falsified", [expected("f", "falsify")], [result("f", "oracle-pass")], False, "COMPLETE", "FALSIFIED", 0),
            ("complete-unverified", [expected("s", "support")], [result("s", "oracle-fail")], False, "COMPLETE", "UNVERIFIED", 0),
            ("incomplete-falsified", [expected("f", "falsify"), expected("n", "neutral")], [result("f", "oracle-pass"), result("n", "timeout")], False, "INCOMPLETE", "FALSIFIED", 1),
            ("incomplete-unverified", [expected("s", "support")], [result("s", "infrastructure-error")], False, "INCOMPLETE", "UNVERIFIED", 1),
            ("dry-run", [expected("s", "support")], [result("s", "dry-run")], True, "DRY RUN", "UNVERIFIED", 0),
        )
        stable_keys = {*_RUNNER.JOB_STATUS_KEYS, "other/unadjudicated"}
        for name, expected_jobs, results, dry_run, execution, claim, exit_code in matrix:
            with self.subTest(name=name):
                aggregation, actual_exit = _RUNNER.aggregate_run_results(results, expected_jobs, dry_run)
                self.assertEqual(2, aggregation["version"])
                self.assertEqual(execution, aggregation["executionStatus"])
                self.assertEqual(claim, aggregation["claimOutcome"])
                self.assertEqual(exit_code, actual_exit)
                self.assertEqual(stable_keys, set(aggregation["counts"]))
                self.assertEqual(len(results), sum(aggregation["counts"].values()))

    def test_unknown_status_uses_other_unadjudicated_count(self) -> None:
        aggregation, _ = _RUNNER.aggregate_run_results(
            [result("s", "future-status")], [expected("s", "support")], False
        )
        self.assertEqual(1, aggregation["counts"]["other/unadjudicated"])
        self.assertEqual(0, aggregation["counts"]["oracle-pass"])

    def test_generated_report_uses_contract_fields_and_all_statuses(self) -> None:
        manifest = {
            "claim": "example claim",
            "hypothesis": "example hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad observation"}],
            "image": {"tag": "example:1"},
            "cases": [],
        }
        aggregation, _ = _RUNNER.aggregate_run_results(
            [result("support-r1", "oracle-pass")], [expected("support-r1", "support")], False
        )
        summary = {
            **aggregation,
            "runId": "test-run",
            "provenance": {
                "containerVersion": "test-version",
                "host": "test-host",
                "imageInspectSha256": "inspect-hash",
                "manifestSha256": "manifest-hash",
            },
            "startedAt": "2026-08-17T00:00:00+00:00",
            "completedAt": "2026-08-17T00:00:01+00:00",
            "concurrency": 1,
            "results": [{**result("support-r1", "oracle-pass", "support"), "group": "target"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            _RUNNER.write_report(manifest, summary, run_root)
            report = (run_root / "report.md").read_text(encoding="utf-8")
        self.assertIn("Preflight/report disposition: **READY**", report)
        self.assertIn("Execution status: **COMPLETE**", report)
        self.assertIn("判定済みジョブ: 1 / 1", report)
        self.assertIn("未判定・未知状態: 0", report)
        self.assertIn("| Job | Group | Relation | Status |", report)
        self.assertIn("`jobs/*/attempts/*/stdout.log`", report)
        self.assertIn("最終attemptの写し", report)


class ResumeResultTests(unittest.TestCase):
    def case(self) -> dict[str, Any]:
        return {
            "id": "resume-case",
            "group": "target",
            "description": "current description",
            "relation": "support",
            "criterionIds": ["criterion-current"],
            "command": ["sh", "-lc", "printf 'ok\\n'"],
            "oracle": {"exitCode": 0, "stdoutContains": ["ok"]},
        }

    def manifest(self) -> dict[str, Any]:
        return {
            "image": {"tag": "example:1"},
            "defaults": {"timeoutSeconds": 10, "retries": 0},
            "mounts": [],
        }

    def seed_resume_result(
        self,
        run_root: Path,
        *,
        status: str | None = None,
        run_id: str = "test-run",
        attempt_timeouts: tuple[bool, ...] = (False,),
    ) -> Path:
        job_root = run_root / "jobs" / "resume-case-r1"
        attempts = []
        stdout = "ok\n"
        stderr = ""
        for attempt_number, timed_out in enumerate(attempt_timeouts, start=1):
            attempt_root = job_root / "attempts" / str(attempt_number)
            evidence = attempt_root / "evidence"
            evidence.mkdir(parents=True)
            (attempt_root / "stdout.log").write_text(stdout, encoding="utf-8")
            (attempt_root / "stderr.log").write_text(stderr, encoding="utf-8")
            attempt_name = _RUNNER.safe_name(
                f"acv-{run_root}-{run_id}-resume-case-r1-a{attempt_number}"
            )
            args, inherited = _RUNNER.build_container_args(
                self.manifest(), self.case(), attempt_name, evidence, run_root
            )
            failures = ["timeout"] if timed_out else []
            attempts.append({
                "attempt": attempt_number,
                "containerName": attempt_name,
                "command": _RUNNER.redact_command(args, inherited),
                "exitCode": None if timed_out else 0,
                "timedOut": timed_out,
                "durationSeconds": 0.001,
                "passed": not timed_out,
                "failures": failures,
                "stdoutSha256": _RUNNER.sha256_file(attempt_root / "stdout.log"),
                "stderrSha256": _RUNNER.sha256_file(attempt_root / "stderr.log"),
                "artifactSha256": {},
            })
        final_attempt = attempts[-1]
        final_failures = final_attempt["failures"]
        (job_root / "stdout.log").write_text(stdout, encoding="utf-8")
        (job_root / "stderr.log").write_text(stderr, encoding="utf-8")
        stored = {
            "jobId": "resume-case-r1",
            "caseId": "resume-case",
            "repeat": 1,
            "group": "stale-group",
            "relation": "falsify",
            "criterionIds": ["criterion-stale"],
            "agentCli": "stale-cli",
            "description": "stale description",
            "status": status or ("timeout" if final_attempt["timedOut"] else "oracle-pass"),
            "command": final_attempt["command"],
            "exitCode": final_attempt["exitCode"],
            "durationSeconds": 0.001,
            "attempts": attempts,
            "oracleFailures": final_failures,
            "stdoutSha256": _RUNNER.sha256_file(job_root / "stdout.log"),
            "stderrSha256": _RUNNER.sha256_file(job_root / "stderr.log"),
            "artifactSha256": {},
        }
        result_path = job_root / "result.json"
        result_path.write_text(json.dumps(stored), encoding="utf-8")
        return result_path

    def test_resume_rebinds_outcome_metadata_from_current_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            resumed = _RUNNER.execute_job(
                self.manifest(), self.case(), 1, "test-run", run_root, Path(directory), False
            )
            persisted = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual("target", resumed["group"])
        self.assertEqual("support", resumed["relation"])
        self.assertEqual(["criterion-current"], resumed["criterionIds"])
        self.assertIsNone(resumed["agentCli"])
        self.assertEqual("current description", resumed["description"])
        self.assertEqual("oracle-pass", resumed["status"])
        self.assertEqual("support", persisted["relation"])
        self.assertEqual(["criterion-current"], persisted["criterionIds"])

    def test_resume_rejects_inconsistent_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root, status="oracle-fail")
            with self.assertRaisesRegex(RuntimeError, "resume result outcome mismatch"):
                _RUNNER.execute_job(
                    self.manifest(), self.case(), 1, "test-run", run_root, Path(directory), False
                )

    def test_resume_rejects_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            stored = json.loads(result_path.read_text(encoding="utf-8"))
            stored["jobId"] = "other-r1"
            result_path.write_text(json.dumps(stored), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "resume result identity mismatch"):
                _RUNNER.execute_job(
                    self.manifest(), self.case(), 1, "test-run", run_root, Path(directory), False
                )

    def test_resume_rejects_inconsistent_attempt_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            stored = json.loads(result_path.read_text(encoding="utf-8"))
            stored["attempts"][0]["passed"] = False
            result_path.write_text(json.dumps(stored), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "resume attempt outcome mismatch"):
                _RUNNER.execute_job(
                    self.manifest(), self.case(), 1, "test-run", run_root, Path(directory), False
                )

    def test_resume_rejects_timeout_with_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            stored = json.loads(result_path.read_text(encoding="utf-8"))
            stored["attempts"][0]["timedOut"] = True
            with result_path.open("w", encoding="utf-8") as handle:
                json.dump(stored, handle)
            with self.assertRaisesRegex(RuntimeError, "resume attempt outcome is invalid"):
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_rejects_non_timeout_without_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            stored = json.loads(result_path.read_text(encoding="utf-8"))
            stored["attempts"][0]["exitCode"] = None
            result_path.write_text(json.dumps(stored), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "resume attempt outcome is invalid"):
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_rejects_missing_or_mismatched_provenance(self) -> None:
        mutations = (
            ("command", lambda stored: stored["attempts"][0].pop("command"), "sequence or provenance mismatch"),
            ("duration", lambda stored: stored["attempts"][0].pop("durationSeconds"), "sequence or provenance mismatch"),
            ("container", lambda stored: stored["attempts"][0].__setitem__("containerName", "wrong"), "container identity mismatch"),
            ("top-command", lambda stored: stored.__setitem__("command", ["wrong"]), "result outcome mismatch"),
        )
        for name, mutate, message in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                run_root = Path(directory)
                result_path = self.seed_resume_result(run_root)
                stored = json.loads(result_path.read_text(encoding="utf-8"))
                mutate(stored)
                result_path.write_text(json.dumps(stored), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, message):
                    _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_requires_real_evidence_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root)
            evidence = run_root / "jobs" / "resume-case-r1" / "attempts" / "1" / "evidence"
            evidence.rmdir()
            with self.assertRaisesRegex(RuntimeError, "resume attempt evidence root"):
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_rejects_symlink_evidence_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root)
            evidence = run_root / "jobs" / "resume-case-r1" / "attempts" / "1" / "evidence"
            evidence.rmdir()
            target = run_root / "outside-evidence"
            target.mkdir()
            evidence.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "resume attempt evidence root"):
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_requires_timeout_to_exhaust_retries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root, attempt_timeouts=(True,))
            manifest = self.manifest()
            manifest["defaults"]["retries"] = 1
            with self.assertRaisesRegex(RuntimeError, "before retries were exhausted"):
                _RUNNER.execute_job(manifest, self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_requires_intermediate_attempts_to_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root, attempt_timeouts=(False, False))
            manifest = self.manifest()
            manifest["defaults"]["retries"] = 1
            with self.assertRaisesRegex(RuntimeError, "resume retry sequence mismatch"):
                _RUNNER.execute_job(manifest, self.case(), 1, "test-run", run_root, run_root, False)

    def test_resume_accepts_writer_shaped_exhausted_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            self.seed_resume_result(run_root, attempt_timeouts=(True, True))
            manifest = self.manifest()
            manifest["defaults"]["retries"] = 1
            resumed = _RUNNER.execute_job(
                manifest, self.case(), 1, "test-run", run_root, run_root, False
            )
        self.assertEqual("timeout", resumed["status"])
        self.assertIsNone(resumed["exitCode"])
        self.assertEqual(2, len(resumed["attempts"]))

    def test_partial_job_state_is_preserved_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            partial = run_root / "jobs" / "resume-case-r1" / "attempts" / "1"
            partial.mkdir(parents=True)
            marker = partial / "partial.log"
            marker.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "partial job state preserved.*move.*new run-id"):
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)
            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))

    def test_resume_rewrite_is_atomic_and_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_root = Path(directory)
            result_path = self.seed_resume_result(run_root)
            with mock.patch.object(_RUNNER.os, "replace", wraps=os.replace) as replace:
                _RUNNER.execute_job(self.manifest(), self.case(), 1, "test-run", run_root, run_root, False)
            replace.assert_called_once()
            self.assertTrue(result_path.is_file())
            self.assertEqual([], list(result_path.parent.glob(".result.json.*.tmp")))


class ValidatorWarningTests(unittest.TestCase):
    def test_claim_bearing_exit_code_only_oracle_warns(self) -> None:
        manifest = {
            "version": 1,
            "slug": "warning-test",
            "claim": "claim",
            "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad"}],
            "image": {"tag": "alpine:3.22"},
            "defaults": {},
            "mounts": [],
            "cases": [{
                "id": "support-only-exit",
                "group": "target",
                "description": "support",
                "relation": "support",
                "criterionIds": ["criterion-main"],
                "command": ["true"],
                "oracle": {"exitCode": 0},
            }, {
                "id": "coverage-falsify", "group": "negative", "description": "coverage",
                "relation": "falsify", "criterionIds": ["criterion-main"],
                "command": ["true"], "oracle": {"stdoutContains": ["coverage-marker"]},
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            _, errors, warnings = _RUNNER.validate_manifest(path)
        self.assertEqual([], errors)
        self.assertTrue(any("claim-bearing case" in warning and "payload-origin discriminator" in warning for warning in warnings))

    def test_neutral_exit_code_only_oracle_does_not_get_payload_warning(self) -> None:
        manifest = {
            "version": 1,
            "slug": "warning-test",
            "claim": "claim",
            "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad"}],
            "image": {"tag": "alpine:3.22"},
            "defaults": {},
            "mounts": [],
            "cases": [{
                "id": "neutral-only-exit",
                "group": "target",
                "description": "neutral",
                "relation": "neutral",
                "criterionIds": ["criterion-main"],
                "command": ["true"],
                "oracle": {"exitCode": 0},
            }, {
                "id": "coverage-falsify", "group": "negative", "description": "coverage",
                "relation": "falsify", "criterionIds": ["criterion-main"],
                "command": ["true"], "oracle": {"stdoutContains": ["coverage-marker"]},
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            _, errors, warnings = _RUNNER.validate_manifest(path)
        self.assertEqual([], errors)
        self.assertFalse(any("claim-bearing case" in warning for warning in warnings))


class DryRunMainTests(unittest.TestCase):
    def manifest(self, *, missing_env: bool) -> dict[str, Any]:
        case = {
            "id": "dry-case",
            "group": "target",
            "description": "dry run",
            "relation": "falsify",
            "criterionIds": ["criterion-main"],
            "command": ["sh", "-lc", "printf 'payload-origin\\n'"],
            "oracle": {"exitCode": 0, "stdoutContains": ["payload-origin"]},
        }
        if missing_env:
            case["inheritEnv"] = ["ACV_TEST_MISSING_ENV"]
        return {
            "version": 1,
            "slug": "dry-main",
            "claim": "claim",
            "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad"}],
            "image": {"tag": "alpine:3.22"},
            "defaults": {"maxConcurrency": 1},
            "mounts": [],
            "cases": [case],
        }

    @staticmethod
    def fake_capture(args: list[str], **_: Any) -> Any:
        if args == ["container", "--version"]:
            return mock.Mock(returncode=0, stdout="container 1.2.2\n", stderr="")
        if args == ["container", "system", "status"]:
            return mock.Mock(returncode=0, stdout="running\n", stderr="")
        raise AssertionError(f"unexpected command in dry run: {args}")

    def run_main(self, missing_env: bool) -> tuple[int, dict[str, Any], str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(self.manifest(missing_env=missing_env)), encoding="utf-8")
            results = root / "results"
            argv = [
                "run-matrix.py", str(manifest_path), "--run-id", "dry-test",
                "--results-dir", str(results.resolve()), "--dry-run",
            ]
            stderr = io.StringIO()
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(_RUNNER.shutil, "which", return_value="/usr/bin/container"),
                mock.patch.object(_RUNNER, "run_capture", side_effect=self.fake_capture),
                mock.patch.dict(os.environ, {}, clear=False),
                contextlib.redirect_stderr(stderr),
                contextlib.redirect_stdout(stdout),
            ):
                os.environ.pop("ACV_TEST_MISSING_ENV", None)
                exit_code = _RUNNER.main()
            run_root = results / "dry-test"
            summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))
            report = (run_root / "report.md").read_text(encoding="utf-8")
        return exit_code, summary, report + stderr.getvalue() + stdout.getvalue()

    def test_healthy_dry_run_main_contract(self) -> None:
        exit_code, summary, output = self.run_main(False)
        self.assertEqual(0, exit_code)
        self.assertEqual("DRY RUN", summary["executionStatus"])
        self.assertEqual("UNVERIFIED", summary["claimOutcome"])
        self.assertEqual(1, summary["counts"]["dry-run"])
        self.assertIn("Preflight/report disposition: **READY**", output)
        self.assertIn("READY does not mean execution completed or the claim was supported", output)

    def test_failing_dry_run_main_contract(self) -> None:
        exit_code, summary, output = self.run_main(True)
        self.assertEqual(1, exit_code)
        self.assertEqual("INCOMPLETE", summary["executionStatus"])
        self.assertEqual("UNVERIFIED", summary["claimOutcome"])
        self.assertEqual(1, summary["counts"]["infrastructure-error"])
        self.assertIn("missing inherited environment variables", output)
        self.assertIn("Preflight/report disposition: **READY**", output)
        self.assertIn("Execution status: **INCOMPLETE**", output)

    def test_top_level_outputs_use_atomic_text_helper(self) -> None:
        with mock.patch.object(
            _RUNNER, "atomic_write_text", wraps=_RUNNER.atomic_write_text
        ) as atomic_writer:
            exit_code, _, _ = self.run_main(False)
        self.assertEqual(0, exit_code)
        published_names = {call.args[0].name for call in atomic_writer.call_args_list}
        self.assertTrue(
            {"image-inspect.json", "run-manifest.json", "summary.json"}
            <= published_names
        )


if __name__ == "__main__":
    unittest.main()
