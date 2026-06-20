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

    print("WXTプロジェクト調査結果")
    print(f"ルート: {root}")
    print(f"パッケージ名: {pkg.get('name', '<未指定>')}")
    print(f"パッケージマネージャ: {pkg.get('packageManager', '<未指定>')}")
    print(f"WXT依存関係: {wxt_version if wxt_version else '<未検出>'}")
    print(f"WXT設定ファイル: {', '.join(wxt_configs) if wxt_configs else '<未検出>'}")
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

    if not wxt_version and not wxt_configs:
        print("警告: WXT依存関係と wxt.config.* のどちらも見つかりません。WXTプロジェクトか確認してください", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
