#!/usr/bin/env python3
"""図解ブリーフ JSON が最小限の利用可能な構造を満たすか検証する。"""
import json
import sys
from pathlib import Path

REQUIRED_TOP = ["purpose", "audience", "message", "elements", "relationships", "selected_pattern"]


def fail(msg: str) -> None:
    print(f"エラー: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("使い方: check-diagram-brief.py path/to/brief.json")
    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"ファイルが見つかりません: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"不正な JSON: {exc.lineno} 行 {exc.colno} 列: {exc.msg}")

    missing = [key for key in REQUIRED_TOP if key not in data]
    if missing:
        fail("必須フィールドが不足しています: " + ", ".join(missing))
    for key in ["purpose", "audience", "message", "selected_pattern"]:
        if not str(data.get(key, "")).strip():
            fail(f"フィールドが空です: {key}")
    elements = data.get("elements")
    if not isinstance(elements, list) or not elements:
        fail("elements は空でないリストである必要があります")
    ids = set()
    labels_seen = {}
    warnings = []
    for idx, element in enumerate(elements, 1):
        if not isinstance(element, dict):
            fail(f"要素 {idx} はオブジェクトである必要があります")
        eid = str(element.get("id", "")).strip()
        label = str(element.get("label", "")).strip()
        if not eid or not label:
            fail(f"要素 {idx} には id と label が必要です")
        if eid in ids:
            fail(f"要素 id が重複しています: {eid}")
        ids.add(eid)
        # 図形と文字列の整合性: 同じラベル文字列が別要素に使われていないか（表記ゆれ・混同の温床）
        if label in labels_seen:
            warnings.append(
                f"ラベルが重複しています（図形と文字列の整合性に注意）: '{label}' (id={labels_seen[label]}, {eid})"
            )
        else:
            labels_seen[label] = eid
    relationships = data.get("relationships", [])
    if relationships is not None:
        if not isinstance(relationships, list):
            fail("relationships はリストである必要があります")
        for idx, rel in enumerate(relationships, 1):
            if not isinstance(rel, dict):
                fail(f"関係 {idx} はオブジェクトである必要があります")
            for endpoint in ["from", "to"]:
                value = str(rel.get(endpoint, "")).strip()
                if value and value not in ids:
                    fail(f"関係 {idx} が未知の {endpoint} を参照しています: {value}")
            # 図形と文字列の整合性: 矢印の向きに対応する動詞ラベルがないと、方向とラベルが矛盾しやすい
            direction = str(rel.get("direction", "")).strip()
            verb = str(rel.get("verb", "")).strip()
            if direction and direction != "none" and not verb:
                warnings.append(
                    f"関係 {idx} は方向 ({direction}) を持ちますが verb が空です。矢印の向きとラベルの矛盾チェックができません。"
                )

    groups = data.get("groups", [])
    if groups is not None:
        if not isinstance(groups, list):
            fail("groups はリストである必要があります")
        for idx, group in enumerate(groups, 1):
            if not isinstance(group, dict):
                fail(f"グループ {idx} はオブジェクトである必要があります")
            label = str(group.get("label", "")).strip()
            if not label:
                fail(f"グループ {idx} には label が必要です")
            element_ids = group.get("element_ids", [])
            if not isinstance(element_ids, list) or not element_ids:
                fail(f"グループ {idx} ('{label}') の element_ids は空でないリストである必要があります")
            for eid in element_ids:
                if str(eid).strip() not in ids:
                    fail(f"グループ {idx} ('{label}') が未知の要素 id を参照しています: {eid}")

    print(f"OK: {path} は利用可能な図解ブリーフです（要素 {len(ids)} 件、関係 {len(relationships or [])} 件、グループ {len(groups or [])} 件）。")
    for warning in warnings:
        print(f"警告: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
