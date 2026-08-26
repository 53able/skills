#!/usr/bin/env python3
"""完成したintake JSONからMCPガバナンスのリスクtierを分類する。"""

import argparse
import json
import sys
from pathlib import Path

FIELDS = [
    "publisher_identity_known", "deployment_identity_known", "arbitrary_shell",
    "unrestricted_host_read", "unrestricted_host_write", "shared_admin_credential",
    "principal_bound_credential", "arbitrary_egress", "side_effecting_action",
    "side_effect_actor_logged", "side_effect_target_logged", "side_effect_result_logged",
    "high_impact_capability", "high_impact_policy_blockable", "secret_access",
    "regulated_data_access", "destructive_action", "payment_action", "production_change",
    "external_nonpublic_data", "admin_credential", "broad_scope_credential",
    "critical_service_impact", "multi_tenant_impact", "organization_wide_impact",
    "irreversible_action", "internal_nonregulated_data_read", "bounded_reversible_write",
    "allowlisted_external_api", "personal_scoped_credential", "team_impact",
    "bounded_non_destructive_automation", "public_non_sensitive_only",
    "resource_limited_read_only", "single_user", "noncritical_resource",
]

CONTROLS = {
    "T0": ["本番接続を禁止する", "隔離環境でのみ調査する", "すべてのblockerと不明項目を解消する"],
    "T1": ["正規のsourceまたはendpoint", "固定versionまたは変更履歴", "接続時と変更時の承認", "基本的なtool decision log"],
    "T2": ["T1の全統制", "Digest／SBOMまたはremote drift統制", "Principalへ結び付いた短命credential", "引数単位の承認", "Rate／scope／destination上限", "Negative test", "Kill-switch test"],
    "T3": ["T2の全統制", "署名済みprovenanceまたは同等統制", "Callごとの承認または二者承認", "JIT privilege", "Blast-radius上限", "下流操作の追跡", "即時停止と失効", "SecurityとData Ownerの独立承認"],
}


def load_input(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"入力ファイルが存在しません: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSONが不正です: {path}（{exc.lineno}行{exc.colno}列: {exc.msg}）")
    if not isinstance(data, dict) or not isinstance(data.get("risk"), dict):
        raise ValueError("入力は'risk' objectを含むJSON objectにしてください。")
    return data


def validate(risk):
    unknown = []
    invalid = []
    for field in FIELDS:
        if field not in risk or risk[field] is None:
            unknown.append(field)
        elif not isinstance(risk[field], bool):
            invalid.append(f"{field}={risk[field]!r}")
    if invalid:
        raise ValueError("Risk項目にはtrue、false、nullだけを使用してください。不正な値: " + ", ".join(invalid))
    return unknown


def classify(risk, unknown):
    if unknown:
        return "T0", [f"unknown:{field}" for field in unknown]

    checks = {
        "publisher_identity_unknown": not risk["publisher_identity_known"],
        "deployment_identity_unknown": not risk["deployment_identity_known"],
        "arbitrary_shell": risk["arbitrary_shell"],
        "unrestricted_host_read": risk["unrestricted_host_read"],
        "unrestricted_host_write": risk["unrestricted_host_write"],
        "shared_admin_credential": risk["shared_admin_credential"],
        "credential_not_principal_bound": not risk["principal_bound_credential"],
        "arbitrary_egress": risk["arbitrary_egress"],
        "side_effect_actor_not_logged": risk["side_effecting_action"] and not risk["side_effect_actor_logged"],
        "side_effect_target_not_logged": risk["side_effecting_action"] and not risk["side_effect_target_logged"],
        "side_effect_result_not_logged": risk["side_effecting_action"] and not risk["side_effect_result_logged"],
        "high_impact_not_policy_blockable": risk["high_impact_capability"] and not risk["high_impact_policy_blockable"],
    }
    t0 = [name for name, triggered in checks.items() if triggered]
    if t0:
        return "T0", t0

    t3_fields = [
        "secret_access", "regulated_data_access", "destructive_action", "payment_action",
        "production_change", "external_nonpublic_data", "admin_credential",
        "broad_scope_credential", "critical_service_impact", "multi_tenant_impact",
        "organization_wide_impact", "irreversible_action",
    ]
    t3 = [field for field in t3_fields if risk[field]]
    if t3:
        return "T3", t3

    t2_fields = [
        "internal_nonregulated_data_read", "bounded_reversible_write",
        "allowlisted_external_api", "personal_scoped_credential", "team_impact",
        "bounded_non_destructive_automation",
    ]
    t2 = [field for field in t2_fields if risk[field]]
    if t2:
        return "T2", t2

    t1_conditions = [
        risk["public_non_sensitive_only"], risk["resource_limited_read_only"],
        risk["single_user"], risk["noncritical_resource"], not risk["side_effecting_action"],
    ]
    if all(t1_conditions):
        return "T1", ["all_t1_conditions_satisfied"]

    return "T2", ["known_no_match_fallback"]


def main():
    parser = argparse.ArgumentParser(description="MCPガバナンスのリスクをT0、T1、T2、T3へ分類する。")
    parser.add_argument("--input", required=True, help="完成したintake JSONのパス。")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="出力形式。")
    args = parser.parse_args()

    try:
        data = load_input(args.input)
        unknown = validate(data["risk"])
        tier, triggers = classify(data["risk"], unknown)
    except ValueError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    result = {
        "tier": tier,
        "triggers": triggers,
        "unknown_fields": unknown,
        "required_controls": CONTROLS[tier],
    }
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"TIER: {tier}")
        print("発火条件: " + (", ".join(triggers) if triggers else "なし"))
        print("不明項目: " + (", ".join(unknown) if unknown else "なし"))
        print("必須統制:")
        for control in CONTROLS[tier]:
            print(f"- {control}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
