#!/usr/bin/env python3
"""Round-7 redaction, immutable publication, schema, and rendering regressions."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).parents[1]
_RUNNER_PATH = _ROOT / "scripts" / "run-matrix.py"
_VALIDATOR_PATH = _ROOT / "scripts" / "validate-manifest.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load(_RUNNER_PATH, "acv_round7_runner")
VALIDATOR = load(_VALIDATOR_PATH, "acv_round7_validator")


class SecretRemovalTests(unittest.TestCase):
    def test_fixed_point_deletion_handles_collisions_and_transforms(self) -> None:
        values = {
            "NAME": "NAME", "SHORT": "x", "LONG": "abc", "TAIL": "bc",
            "JOIN": "X", "CREATED": "aa", "MULTI": "line1\nline2",
            "SLASH": r"a\\b", "UNICODE": "秘密", "CONTROL": "\x01",
        }
        text = "NAME x abc bc aXa line1\nline2 a\\b 秘密 \x01"
        with mock.patch.dict(os.environ, values, clear=True):
            redacted = RUNNER.redact_inherited_text(text, set(values))
        for value in values.values():
            self.assertNotIn(value, redacted)
        self.assertNotIn("aa", redacted)  # created only after deleting X from aXa

    def test_binary_artifact_fixed_point_and_symlink_target_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"JOIN": "X", "CREATED": "aa", "BINARY": "\x01"}, clear=True
        ):
            root = Path(directory)
            evidence = root / "evidence"
            evidence.mkdir()
            artifact = evidence / "value.bin"
            artifact.write_bytes(b"aXa\x01")
            outside = root / "outside"
            outside.write_bytes(b"outside")
            outside.chmod(0o644)
            (evidence / "link").symlink_to(outside)
            failures = RUNNER.sanitize_artifacts(evidence, {"JOIN", "CREATED", "BINARY"})
            self.assertEqual(b"", artifact.read_bytes())
            self.assertEqual(b"outside", outside.read_bytes())
            self.assertEqual(0o644, stat.S_IMODE(outside.stat().st_mode))
            self.assertTrue(any("symlink" in item for item in failures))
            self.assertFalse(any(name in " ".join(failures) for name in ("JOIN", "CREATED", "BINARY")))

    def test_multiline_backslash_secret_never_reappears_in_job_or_report(self) -> None:
        secret = "line1\nline2\\tail"
        manifest = {"claim": "claim", "hypothesis": "hypothesis", "image": {"tag": "i"},
                    "falsificationCriteria": [{"id": "c", "description": "d"}],
                    "defaults": {"timeoutSeconds": 1, "retries": 0}, "mounts": [], "cases": []}
        case = {"id": "case", "group": "target", "description": "d", "relation": "support",
                "criterionIds": ["c"], "command": ["true"], "inheritEnv": ["TOKEN"],
                "oracle": {"exitCode": 0, "stdoutNotContains": [secret]}}
        manifest["cases"] = [case]
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TOKEN": secret}, clear=True
        ), mock.patch.object(
            RUNNER, "run_capture", return_value=mock.Mock(returncode=0, stdout=secret, stderr="")
        ):
            root = Path(directory)
            result = RUNNER.execute_job(manifest, case, 1, "run", root, root, False)
            summary = {"runId": "run", "claimOutcome": "UNVERIFIED", "executionStatus": "COMPLETE",
                       "counts": {key: 0 for key in (*RUNNER.JOB_STATUS_KEYS, "other/unadjudicated")},
                       "jobs": 1, "startedAt": "s", "completedAt": "e", "concurrency": 1,
                       "provenance": {"containerVersion": "v", "host": "h", "imageInspectSha256": "i", "manifestSha256": "m"},
                       "results": [result]}
            RUNNER.publish_authoritative_summary_report(manifest, summary, root, {"TOKEN"})
            for path in root.rglob("*"):
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes(), str(path))
                    self.assertNotIn(repr(secret).encode(), path.read_bytes(), str(path))

    def test_oracle_failures_never_echo_needles_or_repr(self) -> None:
        secret = "line1\nline2\\tail"
        case = {"oracle": {
            "stdoutContains": [secret], "stdoutNotContains": ["present"],
            "stderrContains": [secret], "stderrNotContains": ["bad"],
            "artifacts": [{"path": "value", "contains": secret}],
        }}
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "value").write_text("other", encoding="utf-8")
            passed, failures = RUNNER.check_oracle(case, 0, False, "present", "bad", evidence)
        self.assertFalse(passed)
        joined = json.dumps(failures)
        self.assertNotIn("line1", joined)
        self.assertNotIn("\\\\tail", joined)
        self.assertIn("stdoutContains[0] failed", failures)
        self.assertIn("artifacts[0].contains failed", failures)


class PublicationTests(unittest.TestCase):
    @staticmethod
    def manifest():
        return {"claim": "claim", "hypothesis": "hypothesis", "image": {"tag": "i"},
                "falsificationCriteria": [{"id": "c", "description": "d"}], "cases": []}

    @staticmethod
    def summary():
        return {"runId": "r", "claimOutcome": "UNVERIFIED", "executionStatus": "INCOMPLETE",
                "counts": {key: 0 for key in (*RUNNER.JOB_STATUS_KEYS, "other/unadjudicated")},
                "jobs": 0, "startedAt": "s", "completedAt": "e", "concurrency": 1,
                "provenance": {"containerVersion": "v", "host": "h", "imageInspectSha256": "i", "manifestSha256": "m"},
                "results": []}

    def test_evidence_interpolation_and_markdown_cells(self) -> None:
        summary = self.summary()
        summary["results"] = [{"jobId": "x|y\nINJECT", "group": "g\rnext", "relation": "support",
                               "status": "oracle-pass\n| bad |", "oracleFailures": ["a|b\nrow"]}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "run-manifest.json").write_text("{}")
            report = RUNNER.render_report(self.manifest(), summary, root, "report.g.md")
        self.assertNotIn("{evidence_lines}", report)
        self.assertIn("- `run&#45;manifest&#46;json`", report)
        row = next(line for line in report.splitlines() if "x&#124;y INJECT" in line)
        self.assertEqual(
            "| x&#124;y INJECT | g next | support | oracle&#45;pass &#124; bad &#124; | 0 | a&#124;b row |",
            row,
        )
        self.assertNotIn("\nINJECT", row)

    def test_generation_collision_never_replaces_existing_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_report = root / ("report." + "a" * 32 + ".md")
            old_report.write_text("old", encoding="utf-8")
            old_summary = {"reportArtifact": {"path": old_report.name, "sha256": RUNNER.sha256_file(old_report)}}
            (root / "summary.json").write_text(json.dumps(old_summary), encoding="utf-8")
            with mock.patch.object(RUNNER.secrets, "token_hex", return_value="a" * 32):
                with self.assertRaisesRegex(RuntimeError, "could not allocate"):
                    RUNNER.publish_authoritative_summary_report(self.manifest(), self.summary(), root)
            self.assertEqual("old", old_report.read_text(encoding="utf-8"))
            self.assertEqual(old_summary, json.loads((root / "summary.json").read_text()))

    def test_collision_then_summary_failure_preserves_old_hash_pair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_report = root / ("report." + "a" * 32 + ".md")
            old_report.write_text("old", encoding="utf-8")
            old_summary = {"reportArtifact": {"path": old_report.name, "sha256": RUNNER.sha256_file(old_report)}}
            (root / "summary.json").write_text(json.dumps(old_summary), encoding="utf-8")
            with (mock.patch.object(RUNNER.secrets, "token_hex", side_effect=["a" * 32, "b" * 32]),
                  mock.patch.object(RUNNER, "atomic_write_json", side_effect=OSError("summary"))):
                with self.assertRaisesRegex(OSError, "summary"):
                    RUNNER.publish_authoritative_summary_report(self.manifest(), self.summary(), root)
            persisted = json.loads((root / "summary.json").read_text())
            self.assertEqual(old_summary, persisted)
            self.assertEqual(persisted["reportArtifact"]["sha256"], RUNNER.sha256_file(old_report))

    def test_atomic_replace_is_final_fallible_operation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "summary.json"
            with mock.patch.object(Path, "chmod", side_effect=OSError("must not run")) as chmod:
                RUNNER.atomic_write_text(target, "committed", root=root)
            chmod.assert_not_called()
            self.assertEqual("committed", target.read_text())


class InventoryAndHashTests(unittest.TestCase):
    def completed_job(self, root: Path) -> Path:
        job = root / "jobs" / "case-r1"
        evidence = job / "attempts" / "1" / "evidence"
        evidence.mkdir(parents=True)
        (evidence / "nested").mkdir()
        (evidence / "nested" / "ok").write_text("ok")
        for path in (job / "attempts" / "1" / "stdout.log", job / "attempts" / "1" / "stderr.log",
                     job / "stdout.log", job / "stderr.log"):
            path.write_text("")
        (job / "result.json").write_text(json.dumps({"status": "oracle-pass", "attempts": [{"artifactSha256": {}}]}))
        return job

    def test_closed_schema_rejects_nested_rogue_and_orphan_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job = self.completed_job(root)
            (job / "rogue").mkdir()
            with self.assertRaisesRegex(RuntimeError, "unexpected job"):
                RUNNER.inventory_job_tree(root, {"case-r1"}, require_complete=True)
            (job / "rogue").rmdir()
            orphan = job / "attempts" / "2"
            orphan.mkdir()
            with self.assertRaisesRegex(RuntimeError, "unexpected attempts"):
                RUNNER.inventory_job_tree(root, {"case-r1"}, require_complete=True)

    def test_results_subtree_exclusion_is_stable_and_layout_is_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            skill.mkdir()
            (skill / "code.py").write_text("code")
            results = skill / "results"
            (results / "run1").mkdir(parents=True)
            (results / "run1" / "summary.json").write_text("one")
            first = RUNNER.tree_sha256_excluding_results(skill, results)
            (results / "run2").mkdir()
            (results / "run2" / "summary.json").write_text("two")
            self.assertEqual(first, RUNNER.tree_sha256_excluding_results(skill, results))
            outside = Path(directory) / "outside"
            outside.mkdir()
            self.assertEqual(RUNNER.tree_sha256(skill), RUNNER.tree_sha256_excluding_results(skill, outside))
            with self.assertRaisesRegex(RuntimeError, "must not equal or contain"):
                RUNNER.validate_results_hash_layout(skill, skill)
            with self.assertRaisesRegex(RuntimeError, "must not equal or contain"):
                RUNNER.validate_results_hash_layout(skill, skill.parent)


class ValidationTests(unittest.TestCase):
    def manifest(self):
        return {"version": 1, "slug": "round-seven", "claim": "c", "hypothesis": "h",
                "falsificationCriteria": [{"id": "criterion", "description": "d"}],
                "image": {"tag": "i"}, "defaults": {}, "mounts": [],
                "cases": [{"id": "case", "group": "target", "description": "d", "relation": "support",
                           "criterionIds": ["criterion"], "command": ["true"],
                           "oracle": {"stdoutContains": ["ok"], "artifacts": [{"path": "ok", "exists": True}]}}]}

    def test_artifact_path_control_characters_rejected(self) -> None:
        for control in ("\0", "\r", "\n", "\x01", "\x7f"):
            with self.subTest(control=repr(control)), tempfile.TemporaryDirectory() as directory:
                manifest = self.manifest()
                manifest["cases"][0]["oracle"]["artifacts"][0]["path"] = "a" + control + "b"
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                _, errors, _ = VALIDATOR.validate_manifest(path)
                self.assertTrue(any("artifacts[0].path" in error for error in errors))

    def test_main_removes_path_value_from_all_owned_files_and_diagnostics(self) -> None:
        secret = "PATHSECRET"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve() / secret
            base.mkdir()
            manifest_path = base / "manifest.json"
            manifest_path.write_text("{}", encoding="utf-8")
            results = base / "results"
            manifest = self.manifest()
            manifest["cases"][0]["inheritEnv"] = ["TOKEN"]

            def capture(args, **kwargs):
                if args == ["container", "--version"]:
                    return mock.Mock(returncode=0, stdout="container 1\n", stderr="")
                if args == ["container", "system", "status"]:
                    return mock.Mock(returncode=0, stdout="running\n", stderr="")
                if args[:3] == ["container", "image", "inspect"]:
                    return mock.Mock(returncode=0, stdout="{}", stderr="")
                raise AssertionError(args)

            def execute(*args, **kwargs):
                run_root = args[4]
                job = run_root / "jobs" / "case-r1"
                attempt = job / "attempts" / "1"
                (attempt / "evidence").mkdir(parents=True)
                for path in (attempt / "stdout.log", attempt / "stderr.log", job / "stdout.log", job / "stderr.log"):
                    path.write_text("")
                result = {"jobId": "case-r1", "caseId": "case", "group": "target", "relation": "support",
                          "criterionIds": ["criterion"], "status": "oracle-pass", "oracleFailures": [], "attempts": [{"artifactSha256": {}}]}
                RUNNER.atomic_write_json(job / "result.json", result, root=job)
                return result

            output = io.StringIO()
            argv = ["run-matrix.py", str(manifest_path), "--run-id", "run", "--results-dir", str(results)]
            with (mock.patch.object(sys, "argv", argv),
                  mock.patch.object(RUNNER, "validate_manifest", return_value=(manifest, [], [])),
                  mock.patch.object(RUNNER.shutil, "which", return_value="/bin/container"),
                  mock.patch.object(RUNNER, "run_capture", side_effect=capture),
                  mock.patch.object(RUNNER, "execute_job", side_effect=execute),
                  mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False),
                  contextlib.redirect_stdout(output), contextlib.redirect_stderr(output)):
                code = RUNNER.main()
            self.assertEqual(0, code, output.getvalue())
            self.assertNotIn(secret.encode(), output.getvalue().encode())
            for path in (results / "run").rglob("*"):
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes(), str(path))

    def test_invalid_inherit_env_is_controlled_before_iteration_or_writes(self) -> None:
        for invalid in (7, None, {}):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                manifest = self.manifest()
                manifest["cases"][0]["inheritEnv"] = invalid
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                output = io.StringIO()
                argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(Path(directory) / "results")]
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(output):
                    code = RUNNER.main()
                self.assertEqual(1, code)
                self.assertNotIn("Traceback", output.getvalue())
                self.assertFalse((Path(directory) / "results").exists())


if __name__ == "__main__":
    unittest.main()
