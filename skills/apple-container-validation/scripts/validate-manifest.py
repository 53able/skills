#!/usr/bin/env python3
"""Apple Container検証マニフェストを決定的に検査する。"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
MEM_RE = re.compile(r"^[1-9][0-9]*(?:K|M|G|T|P)?$")
NETWORK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
ROOT_KEYS = {"version", "slug", "claim", "hypothesis", "falsificationCriteria", "image", "defaults", "mounts", "cases"}
IMAGE_KEYS = {"tag", "context", "file", "pull"}
DEFAULT_KEYS = {"network", "cpus", "memory", "timeoutSeconds", "retries", "repeats", "maxConcurrency", "readOnlyRoot", "allowWritableMounts"}
MOUNT_KEYS = {"source", "target", "readonly"}
CASE_KEYS = {"id", "group", "description", "relation", "criterionIds", "exclusiveGroup", "agentCli", "command", "env", "inheritEnv", "network", "cpus", "memory", "timeoutSeconds", "retries", "repeats", "readOnlyRoot", "oracle"}
AGENT_CLIS = {"claude-code-subscription", "codex-subscription"}
ARTIFACT_KEYS = {"path", "exists", "contains"}
RELATIONS = {"support", "falsify", "neutral"}
ALLOWED_ORACLES = {
    "exitCode",
    "stdoutContains",
    "stdoutNotContains",
    "stderrContains",
    "stderrNotContains",
    "artifacts",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"manifestを読めない: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifestのルートはobjectである必要がある")
    return value


def validate_manifest(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    manifest = load_manifest(path)
    errors: list[str] = []
    warnings: list[str] = []

    unknown_root = set(manifest) - ROOT_KEYS
    if unknown_root:
        fail(errors, f"rootに未知キー: {', '.join(sorted(unknown_root))}")
    if manifest.get("version") != 1:
        fail(errors, "versionは1である必要がある")
    slug = manifest.get("slug")
    if not isinstance(slug, str) or not ID_RE.fullmatch(slug):
        fail(errors, "slugは小文字英数字と単一ハイフンで構成する")
    for field in ("claim", "hypothesis"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            fail(errors, f"{field}は空でない文字列にする")
    criteria = manifest.get("falsificationCriteria")
    criterion_ids: set[str] = set()
    if not isinstance(criteria, list) or not criteria:
        fail(errors, "falsificationCriteriaは1件以上の配列にする")
    else:
        for index, criterion in enumerate(criteria):
            if not isinstance(criterion, dict) or set(criterion) != {"id", "description"}:
                fail(errors, f"falsificationCriteria[{index}]はidとdescriptionだけを持つobjectにする")
                continue
            criterion_id = criterion.get("id")
            if not isinstance(criterion_id, str) or not ID_RE.fullmatch(criterion_id) or criterion_id in criterion_ids:
                fail(errors, f"falsificationCriteria[{index}].idが不正または重複")
            else:
                criterion_ids.add(criterion_id)
            if not isinstance(criterion.get("description"), str) or not criterion["description"].strip():
                fail(errors, f"falsificationCriteria[{index}].descriptionを指定する")

    image = manifest.get("image")
    if not isinstance(image, dict):
        fail(errors, "imageはobjectにする")
    else:
        unknown_image = set(image) - IMAGE_KEYS
        if unknown_image:
            fail(errors, f"imageに未知キー: {', '.join(sorted(unknown_image))}")
        if not isinstance(image.get("tag"), str) or not image["tag"].strip():
            fail(errors, "image.tagを指定する")
        if ("context" in image) != ("file" in image):
            fail(errors, "image.contextとimage.fileは両方指定するか、両方省略する")
        for field in ("context", "file"):
            if field in image and (not isinstance(image[field], str) or not image[field].strip()):
                fail(errors, f"image.{field}は空でない文字列にする")
        if "pull" in image and not isinstance(image["pull"], bool):
            fail(errors, "image.pullはbooleanにする")
        if "context" in image and isinstance(image.get("context"), str) and isinstance(image.get("file"), str):
            context_path = (path.parent / image["context"]).resolve()
            file_path = (path.parent / image["file"]).resolve()
            if not context_path.is_dir():
                fail(errors, f"image.contextが存在するディレクトリではない: {context_path}")
            if not file_path.is_file():
                fail(errors, f"image.fileが存在するファイルではない: {file_path}")

    defaults = manifest.get("defaults")
    if not isinstance(defaults, dict):
        fail(errors, "defaultsはobjectにする")
        defaults = {}
    unknown_defaults = set(defaults) - DEFAULT_KEYS
    if unknown_defaults:
        fail(errors, f"defaultsに未知キー: {', '.join(sorted(unknown_defaults))}")
    network = defaults.get("network", "none")
    if not isinstance(network, str) or not NETWORK_RE.fullmatch(network):
        fail(errors, "defaults.networkが不正")
    cpus = defaults.get("cpus", 1)
    if not isinstance(cpus, (int, float)) or isinstance(cpus, bool) or cpus <= 0:
        fail(errors, "defaults.cpusは正数にする")
    memory = defaults.get("memory", "2G")
    if not isinstance(memory, str) or not MEM_RE.fullmatch(memory):
        fail(errors, "defaults.memoryは例 512M / 2G の形式にする")
    for field in ("readOnlyRoot", "allowWritableMounts"):
        if field in defaults and not isinstance(defaults[field], bool):
            fail(errors, f"defaults.{field}はbooleanにする")
    for field, minimum in (("timeoutSeconds", 1), ("retries", 0), ("repeats", 1), ("maxConcurrency", 1)):
        value = defaults.get(field, {"timeoutSeconds": 120, "retries": 0, "repeats": 1, "maxConcurrency": 8}[field])
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            fail(errors, f"defaults.{field}は{minimum}以上の整数にする")

    mounts = manifest.get("mounts", [])
    if not isinstance(mounts, list):
        fail(errors, "mountsは配列にする")
        mounts = []
    targets: set[str] = {"/evidence"}
    has_writable_mount = False
    for index, mount in enumerate(mounts):
        prefix = f"mounts[{index}]"
        if not isinstance(mount, dict):
            fail(errors, f"{prefix}はobjectにする")
            continue
        unknown_mount = set(mount) - MOUNT_KEYS
        if unknown_mount:
            fail(errors, f"{prefix}に未知キー: {', '.join(sorted(unknown_mount))}")
        source, target = mount.get("source"), mount.get("target")
        if not isinstance(source, str) or not source.strip():
            fail(errors, f"{prefix}.sourceを指定する")
        else:
            lexical_source = Path(source)
            if "," in source:
                fail(errors, f"{prefix}.sourceにcommaは使えない")
            resolved_source = (path.parent / lexical_source).resolve()
            if lexical_source.is_absolute() or ".." in lexical_source.parts:
                fail(errors, f"{prefix}.sourceはmanifest配下の相対パスにする")
            elif not resolved_source.exists():
                fail(errors, f"{prefix}.sourceが存在しない: {resolved_source}")
            else:
                try:
                    resolved_source.relative_to(path.parent.resolve())
                except ValueError:
                    fail(errors, f"{prefix}.sourceがmanifest配下から外れる: {resolved_source}")
        if not isinstance(target, str) or not target.startswith("/"):
            fail(errors, f"{prefix}.targetは絶対パスにする")
        else:
            normalized_target = posixpath.normpath(target)
            if "," in target or normalized_target != target:
                fail(errors, f"{prefix}.targetは正規化済みでcommaを含まない絶対パスにする")
            elif (
                normalized_target == "/evidence"
                or normalized_target.startswith("/evidence/")
                or "/evidence".startswith(normalized_target.rstrip("/") + "/")
            ):
                fail(errors, f"{prefix}.targetは予約領域/evidenceと重複できない")
            elif normalized_target in targets:
                fail(errors, f"{prefix}.targetが重複している: {normalized_target}")
            else:
                targets.add(normalized_target)
        if "readonly" in mount and not isinstance(mount["readonly"], bool):
            fail(errors, f"{prefix}.readonlyはbooleanにする")
        if mount.get("readonly", True) is not True:
            has_writable_mount = True
            if defaults.get("allowWritableMounts", False) is not True:
                fail(errors, f"{prefix}は書き込み可能: defaults.allowWritableMounts=trueの明示が必要")
            else:
                warnings.append(f"{prefix}は書き込み可能: 必要性と競合防止をレポートへ記録する")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        fail(errors, "casesは1件以上の配列にする")
        cases = []
    ids: set[str] = set()
    groups: set[str] = set()
    command_fingerprints: dict[str, str] = {}
    total_jobs = 0
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            fail(errors, f"{prefix}はobjectにする")
            continue
        unknown_case = set(case) - CASE_KEYS
        if unknown_case:
            fail(errors, f"{prefix}に未知キー: {', '.join(sorted(unknown_case))}")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not ID_RE.fullmatch(case_id):
            fail(errors, f"{prefix}.idが不正")
            case_id = f"invalid-{index}"
        elif case_id in ids:
            fail(errors, f"case idが重複: {case_id}")
        ids.add(case_id)
        group = case.get("group")
        if not isinstance(group, str) or not ID_RE.fullmatch(group):
            fail(errors, f"{prefix}.groupが不正")
        else:
            groups.add(group)
        if not isinstance(case.get("description"), str) or not case["description"].strip():
            fail(errors, f"{prefix}.descriptionを指定する")
        relation = case.get("relation")
        if relation not in RELATIONS:
            fail(errors, f"{prefix}.relationはsupport/falsify/neutralのいずれかにする")
        case_criterion_ids = case.get("criterionIds")
        if not isinstance(case_criterion_ids, list) or not all(isinstance(x, str) for x in case_criterion_ids):
            fail(errors, f"{prefix}.criterionIdsは文字列配列にする")
            case_criterion_ids = []
        unknown_criteria = set(case_criterion_ids) - criterion_ids
        if unknown_criteria:
            fail(errors, f"{prefix}.criterionIdsに未知ID: {', '.join(sorted(unknown_criteria))}")
        if relation == "falsify" and not case_criterion_ids:
            fail(errors, f"{prefix}のrelation=falsifyにはcriterionIdsが必要")
        exclusive_group = case.get("exclusiveGroup")
        if exclusive_group is not None and (not isinstance(exclusive_group, str) or not ID_RE.fullmatch(exclusive_group)):
            fail(errors, f"{prefix}.exclusiveGroupが不正")
        command = case.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            fail(errors, f"{prefix}.commandは空でない文字列配列にする")
        else:
            fingerprint = json.dumps(command, ensure_ascii=False)
            previous = command_fingerprints.get(fingerprint)
            if previous is not None:
                warnings.append(f"同一command: {previous} と {case_id}; オラクル差が意図的か確認する")
            command_fingerprints[fingerprint] = case_id
        repeats = case.get("repeats", defaults.get("repeats", 1))
        if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats < 1:
            fail(errors, f"{prefix}.repeatsは1以上の整数にする")
        else:
            total_jobs += repeats
        timeout = case.get("timeoutSeconds", defaults.get("timeoutSeconds", 120))
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
            fail(errors, f"{prefix}.timeoutSecondsは1以上の整数にする")
        retries = case.get("retries", defaults.get("retries", 0))
        if not isinstance(retries, int) or isinstance(retries, bool) or retries < 0:
            fail(errors, f"{prefix}.retriesは0以上の整数にする")
        case_cpus = case.get("cpus", cpus)
        if not isinstance(case_cpus, (int, float)) or isinstance(case_cpus, bool) or case_cpus <= 0:
            fail(errors, f"{prefix}.cpusは正数にする")
        case_memory = case.get("memory", memory)
        if not isinstance(case_memory, str) or not MEM_RE.fullmatch(case_memory):
            fail(errors, f"{prefix}.memoryが不正")
        if "readOnlyRoot" in case and not isinstance(case["readOnlyRoot"], bool):
            fail(errors, f"{prefix}.readOnlyRootはbooleanにする")
        case_network = case.get("network", network)
        if not isinstance(case_network, str) or not NETWORK_RE.fullmatch(case_network):
            fail(errors, f"{prefix}.networkが不正")
        env = case.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
            fail(errors, f"{prefix}.envは文字列値のobjectにする")
        inherit = case.get("inheritEnv", [])
        if not isinstance(inherit, list) or not all(isinstance(x, str) and x for x in inherit):
            fail(errors, f"{prefix}.inheritEnvは文字列配列にする")
            inherit = []
        agent_cli = case.get("agentCli")
        if agent_cli is not None and agent_cli not in AGENT_CLIS:
            fail(errors, f"{prefix}.agentCliが不正")
        supplied_auth_names = set(inherit) | (set(env) if isinstance(env, dict) else set())
        if agent_cli == "claude-code-subscription":
            if "CLAUDE_CODE_OAUTH_TOKEN" not in inherit:
                fail(errors, f"{prefix}はsubscription用CLAUDE_CODE_OAUTH_TOKENをinheritEnvへ指定する")
            if "ANTHROPIC_API_KEY" in supplied_auth_names:
                fail(errors, f"{prefix}はANTHROPIC_API_KEYを渡せない")
        if agent_cli == "codex-subscription":
            forbidden_codex_keys = {"OPENAI_API_KEY", "CODEX_API_KEY"} & supplied_auth_names
            if forbidden_codex_keys:
                fail(errors, f"{prefix}はAPI keyを渡せない: {', '.join(sorted(forbidden_codex_keys))}")
            has_access_token = "CODEX_ACCESS_TOKEN" in inherit
            codex_home = env.get("CODEX_HOME") if isinstance(env, dict) else None
            has_auth_cache = isinstance(codex_home, str) and any(
                mount.get("target") == codex_home and mount.get("readonly", True) is False
                for mount in mounts if isinstance(mount, dict)
            )
            if has_access_token == has_auth_cache:
                fail(errors, f"{prefix}はCODEX_ACCESS_TOKENまたは書き込み可能CODEX_HOMEのどちらか一方を指定する")
            if has_auth_cache and case.get("exclusiveGroup") != "codex-auth-cache":
                fail(errors, f"{prefix}のauth cache方式はexclusiveGroup=codex-auth-cacheにする")
        oracle = case.get("oracle")
        if not isinstance(oracle, dict) or not oracle:
            fail(errors, f"{prefix}.oracleを指定する")
            continue
        unknown = set(oracle) - ALLOWED_ORACLES
        if unknown:
            fail(errors, f"{prefix}.oracleに未知キー: {', '.join(sorted(unknown))}")
        effective_predicates = int("exitCode" in oracle)
        if "exitCode" in oracle and (not isinstance(oracle["exitCode"], int) or isinstance(oracle["exitCode"], bool)):
            fail(errors, f"{prefix}.oracle.exitCodeは整数にする")
        for key in ("stdoutContains", "stdoutNotContains", "stderrContains", "stderrNotContains"):
            value = oracle.get(key, [])
            if not isinstance(value, list) or not all(isinstance(x, str) and x for x in value):
                fail(errors, f"{prefix}.oracle.{key}は文字列配列にする")
            elif value:
                effective_predicates += 1
        artifacts = oracle.get("artifacts", [])
        if not isinstance(artifacts, list):
            fail(errors, f"{prefix}.oracle.artifactsは配列にする")
        else:
            if artifacts:
                effective_predicates += 1
            for aindex, artifact in enumerate(artifacts):
                aprefix = f"{prefix}.oracle.artifacts[{aindex}]"
                if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
                    fail(errors, f"{aprefix}.pathを指定する")
                    continue
                unknown_artifact = set(artifact) - ARTIFACT_KEYS
                if unknown_artifact:
                    fail(errors, f"{aprefix}に未知キー: {', '.join(sorted(unknown_artifact))}")
                artifact_path = Path(artifact["path"])
                if not artifact["path"] or artifact["path"] == "." or artifact_path.is_absolute() or ".." in artifact_path.parts:
                    fail(errors, f"{aprefix}.pathは/evidence相対の空でない安全なファイルパスにする")
                if "exists" in artifact and not isinstance(artifact["exists"], bool):
                    fail(errors, f"{aprefix}.existsはbooleanにする")
                if "contains" in artifact and (not isinstance(artifact["contains"], str) or not artifact["contains"]):
                    fail(errors, f"{aprefix}.containsは空でない文字列にする")
        if effective_predicates == 0:
            fail(errors, f"{prefix}.oracleには実効的な判定条件が必要")

    referenced_criteria = {
        criterion_id
        for case in cases if isinstance(case, dict)
        for criterion_id in case.get("criterionIds", []) if isinstance(criterion_id, str)
    }
    uncovered_criteria = criterion_ids - referenced_criteria
    if uncovered_criteria:
        fail(errors, f"ケースに接続されていないfalsificationCriteria: {', '.join(sorted(uncovered_criteria))}")
    if has_writable_mount and defaults.get("maxConcurrency", 8) > 1:
        warnings.append("共有書き込みmountがあるためrunnerは全ジョブを直列化する")
    if len(groups) < 3:
        warnings.append("ケース群が3未満: 正例・負例・境界/失敗系の分離を確認する")
    if total_jobs < 6:
        warnings.append("総ジョブ数が6未満: 独立な失敗モードの追加を検討する")
    if all(case.get("network", network) != "none" for case in cases if isinstance(case, dict)):
        warnings.append("全ケースでネットワーク有効: 不要なケースはnoneへ隔離する")
    return manifest, errors, warnings


def recommended_concurrency(manifest: dict[str, Any], total_jobs: int) -> int:
    defaults = manifest.get("defaults", {})
    maximum = defaults.get("maxConcurrency", 8)
    cpus_per_job = max(
        [float(defaults.get("cpus", 1))]
        + [float(case.get("cpus", defaults.get("cpus", 1))) for case in manifest.get("cases", []) if isinstance(case, dict)]
    )
    cpu_bound = max(1, int((os.cpu_count() or 1) // cpus_per_job))
    return max(1, min(total_jobs, maximum, cpu_bound))


def main() -> int:
    parser = argparse.ArgumentParser(description="Apple Container検証マニフェストを検査する")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        manifest, errors, warnings = validate_manifest(args.manifest.resolve())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    total_jobs = sum(
        case.get("repeats", manifest.get("defaults", {}).get("repeats", 1))
        for case in manifest.get("cases", [])
        if isinstance(case, dict)
    )
    result = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "cases": len(manifest.get("cases", [])),
        "groups": sorted({case.get("group") for case in manifest.get("cases", []) if isinstance(case, dict)}),
        "jobs": total_jobs,
        "recommendedConcurrency": recommended_concurrency(manifest, total_jobs) if not errors else None,
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
        else:
            print(
                f"OK: cases={result['cases']} jobs={total_jobs} groups={','.join(result['groups'])} "
                f"recommended_concurrency={result['recommendedConcurrency']}"
            )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
