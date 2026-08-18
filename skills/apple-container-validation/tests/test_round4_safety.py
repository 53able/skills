#!/usr/bin/env python3
"""Safety and persistence contract tests for the round-4 fixes."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

_RUNNER_PATH = Path(__file__).parents[1] / "scripts" / "run-matrix.py"
_SPEC = importlib.util.spec_from_file_location("apple_container_run_matrix_round4", _RUNNER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"runnerを読み込めない: {_RUNNER_PATH}")
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)


class SecretRedactionTests(unittest.TestCase):
    def test_overlapping_values_are_redacted_longest_first(self) -> None:
        with mock.patch.dict(os.environ, {"SHORT": "token", "LONG": "token-suffix"}, clear=True):
            redacted = _RUNNER.redact_inherited_text(
                "token-suffix then token", {"SHORT", "LONG"}
            )
        self.assertEqual(" then ", redacted)

    def test_equal_values_use_stable_combined_label(self) -> None:
        with mock.patch.dict(os.environ, {"B_NAME": "same-value", "A_NAME": "same-value"}, clear=True):
            first = _RUNNER.redact_inherited_text("same-value", {"B_NAME", "A_NAME"})
            second = _RUNNER.redact_inherited_text("same-value", {"A_NAME", "B_NAME"})
        self.assertEqual("", first)
        self.assertEqual(first, second)

    def test_unicode_multiline_and_empty_values(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"UNICODE": "秘密🔐", "MULTILINE": "line1\nline2", "EMPTY": ""},
            clear=True,
        ):
            redacted = _RUNNER.redact_inherited_text(
                "秘密🔐\nline1\nline2\nvisible", {"UNICODE", "MULTILINE", "EMPTY"}
            )
        self.assertEqual("\n\nvisible", redacted)


class ContainedEvidenceTests(unittest.TestCase):
    def test_equal_content_external_file_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            root.mkdir()
            outside = base / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            link = root / "run-manifest.json"
            link.symlink_to(outside)
            with self.assertRaisesRegex(RuntimeError, "must not contain symlinks"):
                _RUNNER.require_real_file(root, link, "committed run manifest")

    def test_ancestor_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "run"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            (outside / "stdout.log").write_text("same", encoding="utf-8")
            ancestor = root / "attempts"
            ancestor.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "must not contain symlinks"):
                _RUNNER.require_real_file(root, ancestor / "stdout.log", "attempt log")

    def test_persisted_image_inspect_missing_tampered_and_symlinked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run_root = base / "run"
            run_root.mkdir()
            content = "inspect payload\n"
            expected_hash = _RUNNER.sha256_bytes(content.encode("utf-8"))
            existing = {"imageInspectSha256": expected_hash}
            inspect_path = run_root / "image-inspect.json"
            with self.assertRaisesRegex(RuntimeError, "persisted image inspect"):
                _RUNNER.verify_persisted_image_inspect(run_root, existing, expected_hash)
            inspect_path.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "provenance mismatch"):
                _RUNNER.verify_persisted_image_inspect(run_root, existing, expected_hash)
            inspect_path.unlink()
            outside = base / "outside-inspect.json"
            outside.write_text(content, encoding="utf-8")
            inspect_path.symlink_to(outside)
            with self.assertRaisesRegex(RuntimeError, "must not contain symlinks"):
                _RUNNER.verify_persisted_image_inspect(run_root, existing, expected_hash)

    def test_json_object_loader_rejects_malformed_and_non_object(self) -> None:
        for name, content, message in (
            ("malformed", "{", "malformed"),
            ("array", "[]", "JSON object"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "run-manifest.json"
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, message):
                    _RUNNER.load_json_object(path, root=root, label="committed run manifest")

    def test_atomic_text_failure_preserves_destination_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "summary.json"
            path.write_text("old\n", encoding="utf-8")
            with mock.patch.object(_RUNNER.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    _RUNNER.atomic_write_text(path, "new\n")
            self.assertEqual("old\n", path.read_text(encoding="utf-8"))
            self.assertEqual([], list(root.glob(".summary.json.*.tmp")))


class MainResumeGuardTests(unittest.TestCase):
    def manifest(self, *, inherit: bool = False) -> dict[str, Any]:
        case: dict[str, Any] = {
            "id": "guard-case",
            "group": "target",
            "description": "guard",
            "relation": "support",
            "criterionIds": ["criterion-main"],
            "command": ["true"],
            "oracle": {"stdoutContains": ["payload-marker"]},
        }
        if inherit:
            case["inheritEnv"] = ["ACV_GUARD_SECRET"]
        return {
            "version": 1,
            "slug": "guard-test",
            "claim": "claim",
            "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad"}],
            "image": {"tag": "example:1"},
            "defaults": {"maxConcurrency": 1},
            "mounts": [],
            "cases": [case],
        }

    @staticmethod
    def fake_preflight(args: list[str], **_: Any) -> Any:
        if args == ["container", "--version"]:
            return mock.Mock(returncode=0, stdout="container 1.2.2\n", stderr="")
        if args == ["container", "system", "status"]:
            return mock.Mock(returncode=0, stdout="running\n", stderr="")
        raise AssertionError(f"unexpected command: {args}")

    def call_main(self, manifest: dict[str, Any], root: Path) -> tuple[int, str]:
        manifest_path = root / "manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")
        argv = [
            "run-matrix.py", str(manifest_path), "--run-id", "resume-test",
            "--results-dir", str((root / "results").resolve()), "--resume",
        ]
        stderr = io.StringIO()
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(_RUNNER, "validate_manifest", return_value=(manifest, [], [])),
            contextlib.redirect_stderr(stderr),
            contextlib.redirect_stdout(stdout),
        ):
            return _RUNNER.main(), stderr.getvalue() + stdout.getvalue()

    def test_inherit_env_resume_rejected_before_preflight_or_job_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            completed = root / "results" / "resume-test" / "jobs" / "guard-case-r1"
            completed.mkdir(parents=True)
            (completed / "result.json").write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(_RUNNER, "run_capture") as capture,
                mock.patch.object(_RUNNER, "execute_job") as execute,
            ):
                exit_code, output = self.call_main(self.manifest(inherit=True), root)
        self.assertEqual(2, exit_code)
        self.assertIn("--resume is disabled when any case uses inheritEnv", output)
        self.assertIn("new run-id", output)
        capture.assert_not_called()
        execute.assert_not_called()

    def test_existing_run_without_committed_manifest_is_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results" / "resume-test").mkdir(parents=True)
            with (
                mock.patch.object(_RUNNER.shutil, "which", return_value="/usr/bin/container"),
                mock.patch.object(_RUNNER, "run_capture", side_effect=self.fake_preflight),
            ):
                exit_code, output = self.call_main(self.manifest(), root)
        self.assertEqual(2, exit_code)
        self.assertIn("committed run manifest", output)
        self.assertIn("new run-id", output)
        self.assertNotIn("Traceback", output)

    def test_malformed_and_non_object_run_manifest_are_controlled(self) -> None:
        for name, content in (("malformed", "{"), ("array", "[]")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run_root = root / "results" / "resume-test"
                run_root.mkdir(parents=True)
                (run_root / "run-manifest.json").write_text(content, encoding="utf-8")
                with (
                    mock.patch.object(_RUNNER.shutil, "which", return_value="/usr/bin/container"),
                    mock.patch.object(_RUNNER, "run_capture", side_effect=self.fake_preflight),
                ):
                    exit_code, output = self.call_main(self.manifest(), root)
                self.assertEqual(2, exit_code)
                self.assertIn("committed run manifest", output)
                self.assertIn("new run-id", output)
                self.assertNotIn("Traceback", output)


class PayloadOriginValidatorTests(unittest.TestCase):
    def validate(self, relation: str, oracle: dict[str, Any]) -> tuple[list[str], list[str]]:
        manifest = {
            "version": 1,
            "slug": "payload-test",
            "claim": "claim",
            "hypothesis": "hypothesis",
            "falsificationCriteria": [{"id": "criterion-main", "description": "bad"}],
            "image": {"tag": "example:1"},
            "defaults": {},
            "mounts": [],
            "cases": [{
                "id": "payload-case",
                "group": "target",
                "description": "payload",
                "relation": relation,
                "criterionIds": ["criterion-main"],
                "command": ["true"],
                "oracle": oracle,
            }],
        }
        if relation != "falsify":
            manifest["cases"].append({
                "id": "coverage-falsify", "group": "negative", "description": "coverage",
                "relation": "falsify", "criterionIds": ["criterion-main"],
                "command": ["true"], "oracle": {"stdoutContains": ["coverage-marker"]},
            })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            _, errors, warnings = _RUNNER.validate_manifest(path)
        return errors, warnings

    def test_negative_forms_and_omitted_exit_code_warn(self) -> None:
        negative_forms = (
            {"stdoutNotContains": ["bad"]},
            {"stderrContains": ["text"]},
            {"stderrNotContains": ["panic"]},
            {"artifacts": [{"path": "missing.txt", "exists": False}]},
            {"artifacts": [{"path": "implicit-present.txt"}]},
        )
        for oracle in negative_forms:
            with self.subTest(oracle=oracle):
                errors, warnings = self.validate("support", oracle)
                self.assertEqual([], errors)
                self.assertTrue(any("正のpayload-origin discriminatorがない" in item for item in warnings))

    def test_positive_stdout_or_explicit_present_artifact_suppresses_warning(self) -> None:
        for oracle in (
            {"stdoutContains": ["unique-payload-marker"]},
            {"artifacts": [{"path": "measurement.json", "exists": True}]},
        ):
            with self.subTest(oracle=oracle):
                errors, warnings = self.validate("falsify", oracle)
                self.assertEqual([], errors)
                self.assertFalse(any("payload-origin discriminator" in item for item in warnings))

    def test_neutral_control_does_not_warn(self) -> None:
        errors, warnings = self.validate("neutral", {"stderrNotContains": ["panic"]})
        self.assertEqual([], errors)
        self.assertFalse(any("payload-origin discriminator" in item for item in warnings))

    def test_absent_artifact_with_contains_is_rejected(self) -> None:
        errors, _ = self.validate(
            "support",
            {"artifacts": [{"path": "missing.txt", "exists": False, "contains": "ignored"}]},
        )
        self.assertTrue(any("exists=falseとcontainsを併用できない" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
