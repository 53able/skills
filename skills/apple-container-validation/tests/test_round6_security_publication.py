#!/usr/bin/env python3
"""Round-6 security, filesystem, attestation, and publication regressions."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

_RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "run-matrix.py"
_SPEC = importlib.util.spec_from_file_location("apple_container_run_matrix_round6", _RUNNER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"runnerを読み込めない: {_RUNNER_PATH}")
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)


class SecurityAndTypeTests(unittest.TestCase):
    def test_atomic_files_and_owned_directories_are_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = _RUNNER.create_or_validate_directory(root, root / "child", "child")
            path = child / "value.txt"
            _RUNNER.atomic_write_text(path, "value", root=root)
            self.assertEqual(0o700, stat.S_IMODE(child.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))

    def test_text_and_binary_artifact_secrets_are_sanitized_before_hashing(self) -> None:
        secret = "round6-secret"
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TOKEN": secret}, clear=True
        ):
            evidence = Path(directory)
            text = evidence / "text.txt"
            binary = evidence / "binary.bin"
            text.write_text(f"before {secret} after", encoding="utf-8")
            binary.write_bytes(b"\x00" + secret.encode() + b"\xff")
            failures = _RUNNER.sanitize_artifacts(evidence, {"TOKEN"})
            hashes, hash_failures = _RUNNER.collect_artifact_hashes(evidence)
            self.assertNotIn(secret.encode(), text.read_bytes())
            self.assertNotIn(secret.encode(), binary.read_bytes())
            self.assertEqual(0o600, stat.S_IMODE(text.stat().st_mode))
            self.assertEqual([], hash_failures)
            self.assertEqual(hashlib.sha256(text.read_bytes()).hexdigest(), hashes["text.txt"])
            self.assertEqual(2, len(failures))
            self.assertNotIn(secret, " ".join(failures))

    def test_execute_job_directory_artifact_cannot_support_claim(self) -> None:
        manifest = {"image": {"tag": "example:1"}, "defaults": {"timeoutSeconds": 1, "retries": 0}, "mounts": []}
        case = {"id": "artifact", "group": "target", "description": "artifact", "relation": "support",
                "criterionIds": ["c"], "command": ["true"],
                "oracle": {"exitCode": 0, "artifacts": [{"path": "value", "exists": True}]}}

        def capture(args: list[str], **_: Any) -> Any:
            mount = args[args.index("--mount") + 1]
            evidence = Path(mount.split("source=", 1)[1].split(",target=", 1)[0])
            (evidence / "value").mkdir()
            return mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            _RUNNER, "run_capture", side_effect=capture
        ):
            root = Path(directory)
            result = _RUNNER.execute_job(manifest, case, 1, "run", root, root, False)
            aggregation, _ = _RUNNER.aggregate_run_results(
                [result], [{"jobId": "artifact-r1", "relation": "support"}], False
            )
        self.assertEqual("oracle-fail", result["status"])
        self.assertEqual("UNVERIFIED", aggregation["claimOutcome"])

    def test_expected_artifact_must_be_regular_file(self) -> None:
        case = {"oracle": {"artifacts": [{"path": "value", "exists": True}]}}
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "value").mkdir()
            passed, failures = _RUNNER.check_oracle(case, 0, False, "", "", evidence)
            self.assertFalse(passed)
            self.assertTrue(any("regular file" in item for item in failures))
            fifo = evidence / "pipe"
            os.mkfifo(fifo)
            hashes, artifact_failures = _RUNNER.collect_artifact_hashes(evidence)
            self.assertEqual({}, hashes)
            self.assertTrue(any("forbidden artifact type: pipe" in item for item in artifact_failures))

    def test_image_build_log_is_atomic_private_and_redacted(self) -> None:
        secret = "build-secret"
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TOKEN": secret}, clear=True
        ):
            root = Path(directory)
            manifest = {
                "image": {"tag": "example:1", "context": ".", "file": secret}
            }
            _RUNNER.build_image(manifest, root, root, True, {"TOKEN"})
            log = root / "image-build.log"
            self.assertNotIn(secret, log.read_text(encoding="utf-8"))
            self.assertNotIn(secret, log.read_text(encoding="utf-8"))
            self.assertEqual(0o600, stat.S_IMODE(log.stat().st_mode))

    def test_results_dir_symlink_component_is_rejected_before_child_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            outside = base / "outside"
            outside.mkdir()
            linked = base / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "must not contain symlinks"):
                _RUNNER.create_results_directory(linked / "absent")
            self.assertFalse((outside / "absent").exists())


class PublicationAndInventoryTests(unittest.TestCase):
    @staticmethod
    def manifest() -> dict[str, Any]:
        return {
            "claim": "claim", "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "c", "description": "bad"}],
            "image": {"tag": "example:1"}, "cases": [],
        }

    @staticmethod
    def summary() -> dict[str, Any]:
        return {
            "runId": "run", "claimOutcome": "UNVERIFIED", "executionStatus": "INCOMPLETE",
            "counts": {key: 0 for key in (*_RUNNER.JOB_STATUS_KEYS, "other/unadjudicated")},
            "jobs": 1, "startedAt": "start", "completedAt": "end", "concurrency": 1,
            "authenticationVerification": "NOT APPLICABLE",
            "launcherOriginVerification": "NOT VERIFIED BY RUNNER",
            "claimEvaluationQualification": "PROVISIONAL",
            "provenance": {"containerVersion": "v", "host": "h", "imageInspectSha256": "i", "manifestSha256": "m"},
            "results": [{"status": "infrastructure-error", "oracleFailures": ["bad"]}],
        }

    def test_anonymous_report_is_rendered_and_attestation_is_explicit(self) -> None:
        anonymous = {"status": "oracle-pass", "oracleFailures": []}
        aggregation, _ = _RUNNER.aggregate_run_results(
            [anonymous], [{"jobId": "expected-r1", "relation": "support"}], False
        )
        summary = {**self.summary(), **aggregation, "results": [anonymous]}
        with tempfile.TemporaryDirectory() as directory:
            report = _RUNNER.render_report(self.manifest(), summary, Path(directory))
        self.assertEqual("INCOMPLETE", summary["executionStatus"])
        self.assertEqual("UNVERIFIED", summary["claimOutcome"])
        self.assertIn("&#60;anonymous&#45;1&#62;", report)
        self.assertIn("NOT VERIFIED BY RUNNER", report)
        self.assertIn("claimOutcome`単独", report)

    def test_authoritative_summary_references_exact_generation_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            committed, report = _RUNNER.publish_authoritative_summary_report(
                self.manifest(), self.summary(), root
            )
            persisted = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(report.name, committed["reportArtifact"]["path"])
            self.assertEqual(_RUNNER.sha256_file(report), persisted["reportArtifact"]["sha256"])
            self.assertTrue((root / "report.md").is_file())

    def test_report_publish_failure_leaves_old_summary_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = {"old": True}
            (root / "summary.json").write_text(json.dumps(old), encoding="utf-8")
            with mock.patch.object(_RUNNER, "atomic_create_bytes", side_effect=OSError("report")):
                with self.assertRaisesRegex(OSError, "report"):
                    _RUNNER.publish_authoritative_summary_report(self.manifest(), self.summary(), root)
            self.assertEqual(old, json.loads((root / "summary.json").read_text(encoding="utf-8")))

    def test_publication_failures_leave_old_summary_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = {"old": True}
            (root / "summary.json").write_text(json.dumps(old), encoding="utf-8")
            with mock.patch.object(_RUNNER, "atomic_write_json", side_effect=OSError("summary")):
                with self.assertRaisesRegex(OSError, "summary"):
                    _RUNNER.publish_authoritative_summary_report(self.manifest(), self.summary(), root)
            self.assertEqual(old, json.loads((root / "summary.json").read_text(encoding="utf-8")))
            self.assertTrue(list(root.glob("report.*.md")))

    def test_job_inventory_rejects_rogue_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = root / "jobs"
            jobs.mkdir()
            (jobs / "expected-r1").mkdir()
            (jobs / "rogue-r1").mkdir()
            with self.assertRaisesRegex(RuntimeError, "unexpected job tree"):
                _RUNNER.inventory_job_tree(root, {"expected-r1"}, require_complete=True)


class MainRedactionTests(unittest.TestCase):
    def manifest(self) -> dict[str, Any]:
        return {
            "version": 1, "slug": "round6", "claim": "claim", "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "c", "description": "bad"}],
            "image": {"tag": "example:1"}, "defaults": {"maxConcurrency": 1}, "mounts": [],
            "cases": [{"id": "case", "group": "target", "description": "case", "relation": "support",
                       "criterionIds": ["c"], "command": ["true"], "inheritEnv": ["TOKEN"],
                       "oracle": {"exitCode": 0, "stdoutContains": ["ready"]}}],
        }

    def run_main(self, inspect_returncode: int, *, infrastructure: bool = False) -> tuple[int, str, Path, tempfile.TemporaryDirectory[str]]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name).resolve()
        manifest_path = root / "manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        results = root / "results"
        secret = "main-secret"

        def capture(args: list[str], **_: Any) -> Any:
            if args == ["container", "--version"]:
                return mock.Mock(returncode=0, stdout="container 1\n", stderr="")
            if args == ["container", "system", "status"]:
                return mock.Mock(returncode=0, stdout="running\n", stderr="")
            if args[:3] == ["container", "image", "inspect"]:
                return mock.Mock(returncode=inspect_returncode, stdout=f"inspect {secret}\n", stderr=f"failure {secret}\n")
            raise AssertionError(args)

        def execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            run_root = args[4]
            job = run_root / "jobs" / "case-r1"
            job.mkdir()
            if infrastructure:
                raise RuntimeError(f"infra {secret}")
            attempt = job / "attempts" / "1"
            evidence = attempt / "evidence"
            evidence.mkdir(parents=True)
            (attempt / "stdout.log").write_text("ready\n", encoding="utf-8")
            (attempt / "stderr.log").write_text("", encoding="utf-8")
            (job / "stdout.log").write_text("ready\n", encoding="utf-8")
            (job / "stderr.log").write_text("", encoding="utf-8")
            result = {"jobId": "case-r1", "caseId": "case", "group": "target", "relation": "support",
                      "criterionIds": ["c"], "status": "oracle-pass", "oracleFailures": [], "attempts": [{"artifactSha256": {}}]}
            _RUNNER.atomic_write_json(job / "result.json", result, root=job)
            return result

        argv = ["run-matrix.py", str(manifest_path), "--run-id", "run", "--results-dir", str(results)]
        output = io.StringIO()
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(_RUNNER, "validate_manifest", return_value=(self.manifest(), [], [])),
            mock.patch.object(_RUNNER.shutil, "which", return_value="/usr/bin/container"),
            mock.patch.object(_RUNNER, "run_capture", side_effect=capture),
            mock.patch.object(_RUNNER, "execute_job", side_effect=execute),
            mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False),
            contextlib.redirect_stdout(output), contextlib.redirect_stderr(output),
        ):
            code = _RUNNER.main()
        return code, output.getvalue(), results / "run", temporary

    def test_image_inspect_success_is_persisted_redacted(self) -> None:
        code, output, root, temporary = self.run_main(0)
        try:
            persisted = (root / "image-inspect.json").read_text(encoding="utf-8")
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(0, code)
            self.assertNotIn("main-secret", persisted + output)
            self.assertNotIn("main-secret", persisted)
            self.assertEqual("NOT APPLICABLE", summary["authenticationVerification"])
            self.assertEqual("NOT VERIFIED BY RUNNER", summary["launcherOriginVerification"])
            self.assertEqual("PROVISIONAL", summary["claimEvaluationQualification"])
        finally:
            temporary.cleanup()

    def test_image_inspect_failure_is_printed_and_persisted_redacted(self) -> None:
        code, output, root, temporary = self.run_main(1)
        try:
            persisted = (root / "image-inspect.json").read_text(encoding="utf-8")
            self.assertEqual(2, code)
            self.assertNotIn("main-secret", persisted + output)
            self.assertNotIn("main-secret", output)
        finally:
            temporary.cleanup()

    def test_infrastructure_exception_is_redacted_in_output_and_summary(self) -> None:
        code, output, root, temporary = self.run_main(0, infrastructure=True)
        try:
            summary = (root / "summary.json").read_text(encoding="utf-8")
            self.assertEqual(1, code)
            self.assertNotIn("main-secret", summary + output)
            self.assertNotIn("main-secret", summary)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
