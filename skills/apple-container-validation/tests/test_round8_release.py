#!/usr/bin/env python3
"""Round-8 release-blocker regressions."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import socket
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


RUNNER = load(ROOT / "scripts" / "run-matrix.py", "acv_round8_runner")
VALIDATOR = load(ROOT / "scripts" / "validate-manifest.py", "acv_round8_validator")


def manifest(case_overrides=None):
    case = {
        "id": "falsify-case", "group": "negative", "description": "description",
        "relation": "falsify", "criterionIds": ["criterion"], "command": ["true"],
        "oracle": {"stdoutContains": ["payload-marker"]},
    }
    case.update(case_overrides or {})
    return {
        "version": 1, "slug": "round-eight", "claim": "claim", "hypothesis": "hypothesis",
        "falsificationCriteria": [{"id": "criterion", "description": "criterion description"}],
        "image": {"tag": "example:1"}, "defaults": {"maxConcurrency": 1},
        "mounts": [], "cases": [case],
    }


def summary():
    return {
        "version": 2, "runId": "run", "claimOutcome": "UNVERIFIED",
        "executionStatus": "INCOMPLETE", "jobs": 1,
        "counts": {key: 0 for key in (*RUNNER.JOB_STATUS_KEYS, "other/unadjudicated")},
        "startedAt": "start", "completedAt": "end", "concurrency": 1,
        "provenance": {"containerVersion": "v", "host": "h", "imageInspectSha256": "i", "manifestSha256": "m"},
        "results": [],
    }


class FinalByteGateTests(unittest.TestCase):
    def test_json_punctuation_recreation_fails_before_authoritative_report(self):
        secret = 'a": "b'
        value = summary()
        value["a"] = "b"
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TOKEN": secret}, clear=True
        ):
            root = Path(directory)
            old = {"old": True}
            (root / "summary.json").write_text(json.dumps(old), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "cannot be published safely"):
                RUNNER.publish_authoritative_summary_report(manifest(), value, root, {"TOKEN"})
            self.assertEqual(old, json.loads((root / "summary.json").read_text()))
            self.assertEqual([], list(root.glob("report.*.md")))
            self.assertNotIn(secret.encode(), (root / "summary.json").read_bytes())

    def test_job_sinks_use_run_wide_inherited_value_set(self):
        secret = "OTHER-CASE-SECRET"
        value = manifest()
        case = value["cases"][0]
        case["oracle"] = {"stdoutNotContains": [secret]}
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"OTHER_TOKEN": secret}, clear=True
        ), mock.patch.object(
            RUNNER, "run_capture", return_value=mock.Mock(returncode=0, stdout=secret, stderr="")
        ):
            root = Path(directory)
            result = RUNNER.execute_job(
                value, case, 1, "run", root, root, False, {"OTHER_TOKEN"}
            )
            self.assertEqual("oracle-fail", result["status"])
            for path in root.rglob("*"):
                if path.is_file():
                    self.assertNotIn(secret.encode(), path.read_bytes())

    def test_post_commit_convenience_failure_does_not_invalidate_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = RUNNER.atomic_write_bytes

            def fail_convenience(path, value, **kwargs):
                if path.name == "report.md":
                    raise OSError("convenience")
                return real(path, value, **kwargs)

            stderr = io.StringIO()
            with mock.patch.object(RUNNER, "atomic_write_bytes", side_effect=fail_convenience), contextlib.redirect_stderr(stderr):
                committed, report = RUNNER.publish_authoritative_summary_report(manifest(), summary(), root)
            persisted = json.loads((root / "summary.json").read_text())
            self.assertEqual(committed["reportArtifact"], persisted["reportArtifact"])
            self.assertEqual(persisted["reportArtifact"]["sha256"], RUNNER.sha256_file(report))
            self.assertIn("convenience report.md update failed", stderr.getvalue())


class HashAndInputTests(unittest.TestCase):
    def test_lexical_exclusion_does_not_follow_escape_and_hashes_are_type_framed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            results = root / "results"
            results.mkdir(parents=True)
            outside = Path(directory) / "outside"
            outside.mkdir()
            (outside / "value").write_text("one")
            (results / "escape").symlink_to(outside, target_is_directory=True)
            first = RUNNER.tree_sha256_excluding_results(root, results)
            (outside / "value").write_text("two")
            self.assertEqual(first, RUNNER.tree_sha256_excluding_results(root, results))
            empty_file = Path(directory) / "empty-file"
            empty_file.write_bytes(b"")
            empty_dir = Path(directory) / "empty-dir"
            empty_dir.mkdir()
            self.assertNotEqual(RUNNER.tree_sha256(empty_file), RUNNER.tree_sha256(empty_dir))
            fifo = Path(directory) / "fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(RuntimeError, "regular file or real directory"):
                RUNNER.tree_sha256(fifo)

    def test_mount_sources_reject_symlink_fifo_and_socket(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            regular = base / "regular"
            regular.write_text("x")
            link = base / "link"
            link.symlink_to(regular)
            fifo = base / "fifo"
            os.mkfifo(fifo)
            sock_path = base / "sock"
            sock = socket.socket(socket.AF_UNIX)
            sock.bind(str(sock_path))
            try:
                for source in ("link", "fifo", "sock"):
                    with self.subTest(source=source):
                        value = manifest()
                        value["mounts"] = [{"source": source, "target": "/input", "readonly": True}]
                        path = base / f"{source}.json"
                        path.write_text(json.dumps(value))
                        _, errors, _ = VALIDATOR.validate_manifest(path)
                        self.assertTrue(any("mounts[0].source" in item for item in errors), errors)
            finally:
                sock.close()

    def test_image_paths_are_relative_contained_real_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            context = base / "ctx"
            context.mkdir()
            (context / "Containerfile").write_text("FROM scratch")
            outside = base / "outside"
            outside.write_text("FROM scratch")
            link = base / "linked"
            link.symlink_to(context, target_is_directory=True)
            values = [
                {"context": str(context), "file": "ctx/Containerfile"},
                {"context": "./", "file": "ctx/Containerfile"},
                {"context": "../ctx", "file": "ctx/Containerfile"},
                {"context": "linked", "file": "linked/Containerfile"},
                {"context": "ctx", "file": "outside"},
            ]
            for index, image_paths in enumerate(values):
                value = manifest()
                value["image"] = {"tag": "x", **image_paths}
                path = base / f"image-{index}.json"
                path.write_text(json.dumps(value))
                _, errors, _ = VALIDATOR.validate_manifest(path)
                self.assertTrue(any("image." in item for item in errors), errors)
            good = manifest()
            good["image"] = {"tag": "x", "context": "ctx", "file": "ctx/Containerfile"}
            path = base / "good.json"
            path.write_text(json.dumps(good))
            _, errors, _ = VALIDATOR.validate_manifest(path)
            self.assertEqual([], errors)

    def test_results_equality_rejected_and_exclusions_are_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "input"
            root.mkdir()
            results = root / "results"
            results.mkdir()
            with self.assertRaisesRegex(RuntimeError, "hashed input"):
                RUNNER.validate_results_hash_layout(Path(directory) / "skill", root, [root])
            self.assertEqual("results", RUNNER.tree_hash_exclusion(root, results))
            self.assertIsNone(RUNNER.tree_hash_exclusion(root, Path(directory) / "outside"))


class ContractTests(unittest.TestCase):
    def test_support_only_criterion_is_rejected(self):
        value = manifest({"relation": "support"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value))
            _, errors, _ = VALIDATOR.validate_manifest(path)
        self.assertTrue(any("relation=falsify" in item for item in errors))

    def test_markdown_dynamic_text_cannot_forge_structure(self):
        value = manifest()
        forged = "x\n## ステータス\n<script>alert(1)</script> ` ``` |"
        value["claim"] = forged
        value["hypothesis"] = forged
        value["falsificationCriteria"][0]["description"] = forged
        report = RUNNER.render_report(value, summary(), Path("."))
        self.assertEqual(1, report.count("## ステータス"))
        self.assertNotIn("<script>", report)
        self.assertNotIn("\n``` |", report)

    def test_run_root_schema_rejects_sibling_orphan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "jobs").mkdir()
            (root / "relocated-partial").mkdir()
            with self.assertRaisesRegex(RuntimeError, "unexpected run-root"):
                RUNNER.inventory_run_root(root)

    def test_enum_types_are_controlled_in_both_clis(self):
        for field in ("relation", "agentCli"):
            for invalid in ([], {}, 7, None):
                if field == "agentCli" and invalid is None:
                    continue
                with self.subTest(field=field, invalid=invalid), tempfile.TemporaryDirectory() as directory:
                    value = manifest({field: invalid})
                    path = Path(directory) / "manifest.json"
                    path.write_text(json.dumps(value))
                    _, errors, _ = VALIDATOR.validate_manifest(path)
                    self.assertTrue(errors)
                    output = io.StringIO()
                    argv = ["validate-manifest.py", str(path)]
                    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(output):
                        code = VALIDATOR.main()
                    self.assertEqual(1, code)
                    self.assertNotIn("Traceback", output.getvalue())

    def test_unsafe_inherit_env_name_is_rejected(self):
        value = manifest({"inheritEnv": ["TOKEN\nFORGED"]})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(value))
            _, errors, _ = VALIDATOR.validate_manifest(path)
        self.assertTrue(any("inheritEnv" in item for item in errors))

    def test_invalid_manifest_diagnostic_redacts_path_secret(self):
        secret = "DIAGSECRET"
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ, {"TOKEN": secret}, clear=False):
            base = Path(directory) / secret
            base.mkdir()
            value = manifest({"inheritEnv": ["TOKEN"], "relation": []})
            path = base / "manifest.json"
            path.write_text(json.dumps(value))
            output = io.StringIO()
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(base / "results")]
            with mock.patch.object(sys, "argv", argv), contextlib.redirect_stderr(output):
                code = RUNNER.main()
            self.assertEqual(1, code)
            self.assertNotIn(secret, output.getvalue())
            self.assertNotIn("Traceback", output.getvalue())
            self.assertFalse((base / "results").exists())


class ProvenanceMainTests(unittest.TestCase):
    @staticmethod
    def capture(args, **kwargs):
        if args == ["container", "--version"]:
            return mock.Mock(returncode=0, stdout="container 1\n", stderr="")
        if args == ["container", "system", "status"]:
            return mock.Mock(returncode=0, stdout="running\n", stderr="")
        raise AssertionError(args)

    def test_nested_results_exclusions_recorded_and_input_change_breaks_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_root = base / "input"
            input_root.mkdir()
            (input_root / "data").write_text("one")
            value = manifest()
            value["mounts"] = [{"source": "input", "target": "/input", "readonly": True}]
            path = base / "manifest.json"
            path.write_text(json.dumps(value))
            results = input_root / "results"
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve()), "--dry-run"]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(RUNNER.shutil, "which", return_value="/bin/container"),
                mock.patch.object(RUNNER, "run_capture", side_effect=self.capture),
            ):
                self.assertEqual(0, RUNNER.main())
            committed = json.loads((results / "run" / "run-manifest.json").read_text())
            exclusions = committed["treeHashExclusions"]
            self.assertEqual("results", exclusions["mountSources"]["input"])
            self.assertIsNone(exclusions["imageContext"])
            persisted_summary = json.loads((results / "run" / "summary.json").read_text())
            self.assertEqual(exclusions, persisted_summary["provenance"]["treeHashExclusions"])
            (input_root / "data").write_text("two")
            resume_argv = argv + ["--resume"]
            output = io.StringIO()
            with (
                mock.patch.object(sys, "argv", resume_argv),
                mock.patch.object(RUNNER.shutil, "which", return_value="/bin/container"),
                mock.patch.object(RUNNER, "run_capture", side_effect=self.capture),
                contextlib.redirect_stderr(output), contextlib.redirect_stdout(output),
            ):
                self.assertEqual(2, RUNNER.main())
            self.assertIn("provenance mismatch", output.getvalue())


class InfrastructureMainTests(unittest.TestCase):
    @staticmethod
    def capture(args, **kwargs):
        if args == ["container", "--version"]:
            return mock.Mock(returncode=0, stdout="container 1\n", stderr="")
        if args == ["container", "system", "status"]:
            return mock.Mock(returncode=0, stdout="running\n", stderr="")
        if args[:3] == ["container", "image", "inspect"]:
            return mock.Mock(returncode=0, stdout="{}", stderr="")
        if args[:2] == ["container", "run"]:
            raise OSError("spawn failed")
        raise AssertionError(args)

    def test_spawn_error_after_attempt_is_hash_bound_and_published(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "manifest.json"
            path.write_text(json.dumps(manifest()))
            results = base / "results"
            argv = ["run-matrix.py", str(path), "--run-id", "run", "--results-dir", str(results.resolve())]
            output = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(RUNNER.shutil, "which", return_value="/bin/container"),
                mock.patch.object(RUNNER, "run_capture", side_effect=self.capture),
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output),
            ):
                code = RUNNER.main()
            self.assertEqual(1, code, output.getvalue())
            run_root = results / "run"
            persisted = json.loads((run_root / "summary.json").read_text())
            self.assertEqual("INCOMPLETE", persisted["executionStatus"])
            self.assertEqual(1, persisted["counts"]["infrastructure-error"])
            result = json.loads((run_root / "jobs" / "falsify-case-r1" / "result.json").read_text())
            self.assertTrue(result["attempts"][0]["infrastructureError"])
            RUNNER.inventory_job_tree(run_root, {"falsify-case-r1"}, require_complete=True)
            RUNNER.inventory_run_root(run_root)


if __name__ == "__main__":
    unittest.main()
