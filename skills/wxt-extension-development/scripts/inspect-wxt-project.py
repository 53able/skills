#!/usr/bin/env python3
"""WXTプロジェクトを調査し、短く決定的なレポートを出力する。"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str, code: int = 1) -> None:
    print(f"エラー: {message}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} のJSONを解析できません: {exc}")


def find_wxt_config(root: Path) -> list[str]:
    names = [
        "wxt.config.ts",
        "wxt.config.js",
        "wxt.config.mjs",
        "wxt.config.cjs",
        "wxt.config.mts",
    ]
    return [name for name in names if (root / name).exists()]


def detect_ui_framework(all_deps: dict[str, str]) -> str:
    checks = [
        ("react", "React"),
        ("@wxt-dev/module-react", "React (WXT module)"),
        ("vue", "Vue"),
        ("@wxt-dev/module-vue", "Vue (WXT module)"),
        ("svelte", "Svelte"),
        ("@wxt-dev/module-svelte", "Svelte (WXT module)"),
        ("solid-js", "Solid"),
        ("@wxt-dev/module-solid", "Solid (WXT module)"),
    ]
    found = [label for key, label in checks if key in all_deps]
    return ", ".join(found) if found else "<未検出（Vanilla または未インストール）>"


def detect_messaging(all_deps: dict[str, str]) -> str:
    if "webext-bridge" in all_deps:
        return "webext-bridge"
    if "@webext-core/messaging" in all_deps:
        return "@webext-core/messaging"
    return "<未検出（vanilla messaging の可能性）>"


def list_entrypoints(root: Path) -> list[str]:
    candidates = []
    for base in [root / "entrypoints", root / "src" / "entrypoints"]:
        if not base.exists():
            continue
        for item in sorted(base.iterdir(), key=lambda p: p.name):
            if item.name.startswith("."):
                continue
            if item.is_file():
                candidates.append(str(item.relative_to(root)))
            elif item.is_dir():
                candidates.append(str(item.relative_to(root)) + "/")
    return candidates


def manifest_definition_hint(wxt_configs: list[str]) -> str:
    if not wxt_configs:
        return "<wxt.config.* 未検出>"
    parts = [f"{name} の manifest ブロック" for name in wxt_configs]
    parts.append("各 entrypoint の defineContentScript / defineBackground 等")
    return "; ".join(parts)


def collect_risks(
    wxt_version: str | None,
    wxt_configs: list[str],
    entrypoints: list[str],
    all_deps: dict[str, str],
) -> list[str]:
    risks: list[str] = []
    if not wxt_version and not wxt_configs:
        risks.append("WXT 依存関係と wxt.config.* のどちらも未検出")
    if not entrypoints:
        risks.append("entrypoints/ が空または未検出")
    if "webext-bridge" not in all_deps and "@webext-core/messaging" not in all_deps:
        risks.append("messaging ラッパー未検出（チーム既定は webext-bridge）")
    risks.append("permissions / host_permissions 変更は人間レビュー必須")
    risks.append("entrypoint トップレベルの browser.* / document / window 呼び出しは build 失敗の原因")
    return risks


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    if not root.exists():
        fail(f"パスが存在しません: {root}")
    if not root.is_dir():
        fail(f"パスがディレクトリではありません: {root}")

    package_path = root / "package.json"
    if not package_path.exists():
        fail("package.json が見つかりません。Node/WXTプロジェクトではない可能性があります")

    pkg = load_json(package_path)
    deps = pkg.get("dependencies", {}) or {}
    dev_deps = pkg.get("devDependencies", {}) or {}
    all_deps = {**deps, **dev_deps}
    scripts = pkg.get("scripts", {}) or {}

    wxt_version = all_deps.get("wxt") or all_deps.get("@wxt-dev/module-react")
    wxt_configs = find_wxt_config(root)
    entrypoints = list_entrypoints(root)
    web_ext_config = (root / "web-ext.config.ts").exists()
    src_dir = (root / "src").is_dir()

    print("WXTプロジェクト調査結果")
    print(f"ルート: {root}")
    print(f"パッケージ名: {pkg.get('name', '<未指定>')}")
    print(f"パッケージマネージャ: {pkg.get('packageManager', '<未指定>')}")
    print(f"WXT依存関係: {wxt_version if wxt_version else '<未検出>'}")
    print(f"UIフレームワーク: {detect_ui_framework(all_deps)}")
    print(f"messaging: {detect_messaging(all_deps)}")
    print(f"WXT設定ファイル: {', '.join(wxt_configs) if wxt_configs else '<未検出>'}")
    print(f"web-ext.config.ts: {'あり' if web_ext_config else 'なし'}")
    print(f"src/ ディレクトリ: {'あり' if src_dir else 'なし'}")
    print(f"manifest定義の想定場所: {manifest_definition_hint(wxt_configs)}")
    print(f"entrypoints: {', '.join(entrypoints) if entrypoints else '<未検出>'}")

    interesting = [
        "dev",
        "dev:firefox",
        "build",
        "build:firefox",
        "zip",
        "zip:firefox",
        "typecheck",
        "lint",
        "test",
        "postinstall",
    ]
    found_scripts = [f"{name}={scripts[name]}" for name in interesting if name in scripts]
    print(f"主要scripts: {', '.join(found_scripts) if found_scripts else '<一般的なscriptは未検出>'}")

    generated = [name for name in [".wxt", ".output"] if (root / name).exists()]
    print(f"生成物ディレクトリ: {', '.join(generated) if generated else '<未検出>'}")

    risks = collect_risks(wxt_version, wxt_configs, entrypoints, all_deps)
    print("変更前リスク:")
    for risk in risks:
        print(f"- {risk}")

    if not wxt_version and not wxt_configs:
        print(
            "警告: WXT依存関係と wxt.config.* のどちらも見つかりません。WXTプロジェクトか確認してください",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
