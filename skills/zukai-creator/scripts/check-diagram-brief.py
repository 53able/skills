#!/usr/bin/env python3
"""図解ブリーフ JSON が最小限の利用可能な構造を満たすか検証する。"""
import json
import sys
from pathlib import Path

REQUIRED_TOP = ["purpose", "audience", "message", "elements", "relationships", "selected_pattern"]


def fail(msg: str) -> None:
    print(f"エラー: {msg}", file=sys.stderr)
    sys.exit(1)


def required_text(data: dict, key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{context}.{key} は空でない文字列である必要があります")
    return value.strip()


def required_list(data: dict, key: str, context: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{context}.{key} は空でないリストである必要があります")
    return value


def check_explanation(explanation: object, element_ids: set) -> None:
    if not isinstance(explanation, dict):
        fail("explanation はオブジェクトである必要があります")
    for key in ["reader_question", "understanding_gap", "visual_strategy"]:
        required_text(explanation, key, "explanation")
    output_format = required_text(explanation, "output_format", "explanation")
    if output_format not in ["mermaid", "svg"]:
        fail("explanation.output_format は mermaid または svg である必要があります")

    source_ids = set()
    for idx, source in enumerate(required_list(explanation, "source_basis", "explanation"), 1):
        context = f"explanation.source_basis[{idx}]"
        if not isinstance(source, dict):
            fail(f"{context} はオブジェクトである必要があります")
        source_id = required_text(source, "id", context)
        required_text(source, "text", context)
        if source_id in source_ids:
            fail(f"ソース id が重複しています: {source_id}")
        source_ids.add(source_id)

    for idx, mapping in enumerate(required_list(explanation, "claim_visual_map", "explanation"), 1):
        context = f"explanation.claim_visual_map[{idx}]"
        if not isinstance(mapping, dict):
            fail(f"{context} はオブジェクトである必要があります")
        required_text(mapping, "claim", context)
        for key, known_ids in [("source_ids", source_ids), ("element_ids", element_ids)]:
            for reference in required_list(mapping, key, context):
                if not isinstance(reference, str) or not reference.strip():
                    fail(f"{context}.{key} の参照は空でない文字列である必要があります")
                if reference.strip() not in known_ids:
                    fail(f"{context}.{key} が未知の id を参照しています: {reference}")


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
    except (OSError, UnicodeError) as exc:
        fail(f"ファイルを読み込めません: {exc}")

    if not isinstance(data, dict):
        fail("ブリーフは JSON オブジェクトである必要があります")

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

    if "explanation" in data:
        check_explanation(data["explanation"], ids)

    print(f"OK: {path} は利用可能な図解ブリーフです（要素 {len(ids)} 件、関係 {len(relationships or [])} 件、グループ {len(groups or [])} 件）。")
    for warning in warnings:
        print(f"警告: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
