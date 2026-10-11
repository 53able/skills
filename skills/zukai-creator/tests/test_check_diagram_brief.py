"""Exercise the public CLI without importing the validator implementation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-diagram-brief.py"


def legacy_brief():
    return {
        "purpose": "仕組みを理解する", "audience": "初学者", "message": "入力から出力へ進む",
        "selected_pattern": "flow", "elements": [{"id": "e1", "label": "入力"}, {"id": "e2", "label": "出力"}],
        "relationships": [{"from": "e1", "to": "e2", "direction": "one-way", "verb": "生成する"}],
        "groups": [{"label": "処理", "element_ids": ["e1", "e2"]}],
    }


def explanation():
    return {
        "reader_question": "入力はどこで出力に変わるか？",
        "understanding_gap": "処理の順序がわからない",
        "visual_strategy": "入力から出力への矢印で示す",
        "output_format": "mermaid",
        "source_basis": [{"id": "s1", "text": "説明用の仮定: 入力から出力を生成する。"}],
        "claim_visual_map": [{"claim": "入力から出力を生成する", "source_ids": ["s1"], "element_ids": ["e1", "e2"]}],
    }


class BriefCliTests(unittest.TestCase):
    def run_brief(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)

    def assert_invalid(self, data, message):
        result = self.run_brief(data)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_legacy_valid(self):
        result = self.run_brief(legacy_brief())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("要素 2 件、関係 1 件、グループ 1 件", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_legacy_optional_groups_and_null_relationships(self):
        data = legacy_brief()
        del data["groups"]
        data["relationships"] = None
        self.assertEqual(self.run_brief(data).returncode, 0)

    def test_missing_required_field(self):
        data = legacy_brief()
        del data["message"]
        self.assert_invalid(data, "必須フィールドが不足しています: message")

    def test_empty_required_text(self):
        data = legacy_brief()
        data["purpose"] = " "
        self.assert_invalid(data, "フィールドが空です: purpose")

    def test_empty_label(self):
        data = legacy_brief()
        data["elements"][0]["label"] = ""
        self.assert_invalid(data, "には id と label が必要です")

    def test_duplicate_element_id(self):
        data = legacy_brief()
        data["elements"][1]["id"] = "e1"
        self.assert_invalid(data, "要素 id が重複しています: e1")

    def test_unknown_relationship_endpoint(self):
        for endpoint in ("from", "to"):
            with self.subTest(endpoint=endpoint):
                data = legacy_brief()
                data["relationships"][0][endpoint] = "unknown"
                self.assert_invalid(data, f"未知の {endpoint} を参照しています")

    def test_unknown_group_reference(self):
        data = legacy_brief()
        data["groups"][0]["element_ids"] = ["unknown"]
        self.assert_invalid(data, "未知の要素 id を参照しています")

    def test_warnings_do_not_fail(self):
        data = legacy_brief()
        data["elements"][1]["label"] = "入力"
        data["relationships"][0]["verb"] = ""
        result = self.run_brief(data)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ラベルが重複しています", result.stderr)
        self.assertIn("verb が空です", result.stderr)

    def test_legacy_container_types(self):
        for key in ("elements", "relationships", "groups"):
            with self.subTest(key=key):
                data = legacy_brief()
                data[key] = "invalid"
                self.assert_invalid(data, key)

    def test_new_brief_formats(self):
        for output_format in ("mermaid", "svg"):
            with self.subTest(output_format=output_format):
                data = legacy_brief()
                data["explanation"] = explanation()
                data["explanation"]["output_format"] = output_format
                result = self.run_brief(data)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("OK:", result.stdout)

    def test_explanation_object_type(self):
        for value in (None, [], "text", 1, False):
            with self.subTest(value=value):
                data = legacy_brief()
                data["explanation"] = value
                self.assert_invalid(data, "explanation はオブジェクト")

    def test_explanation_missing_fields(self):
        for key in explanation():
            with self.subTest(key=key):
                data = legacy_brief()
                data["explanation"] = explanation()
                del data["explanation"][key]
                self.assert_invalid(data, f"explanation.{key}")

    def test_explanation_text_types(self):
        for key in ("reader_question", "understanding_gap", "visual_strategy", "output_format"):
            for value in (None, "", " ", 1, False, [], {}):
                with self.subTest(key=key, value=value):
                    data = legacy_brief()
                    data["explanation"] = explanation()
                    data["explanation"][key] = value
                    self.assert_invalid(data, f"explanation.{key}")

    def test_invalid_output_format(self):
        data = legacy_brief()
        data["explanation"] = explanation()
        data["explanation"]["output_format"] = "html"
        self.assert_invalid(data, "mermaid または svg")

    def test_explanation_list_types(self):
        for key in ("source_basis", "claim_visual_map"):
            for value in (None, [], {}, "text", 1, [None], ["text"]):
                with self.subTest(key=key, value=value):
                    data = legacy_brief()
                    data["explanation"] = explanation()
                    data["explanation"][key] = value
                    self.assert_invalid(data, f"explanation.{key}")

    def test_source_fields(self):
        for key in ("id", "text"):
            for value in (None, "", " ", 1, [], {}):
                with self.subTest(key=key, value=value):
                    data = legacy_brief()
                    data["explanation"] = explanation()
                    data["explanation"]["source_basis"][0][key] = value
                    self.assert_invalid(data, f"source_basis[1].{key}")
            data = legacy_brief()
            data["explanation"] = explanation()
            del data["explanation"]["source_basis"][0][key]
            self.assert_invalid(data, f"source_basis[1].{key}")

    def test_duplicate_source_ids(self):
        data = legacy_brief()
        data["explanation"] = explanation()
        source = copy.deepcopy(data["explanation"]["source_basis"][0])
        source["id"] = " s1 "
        data["explanation"]["source_basis"].append(source)
        self.assert_invalid(data, "ソース id が重複しています: s1")

    def test_claim_fields(self):
        for key in ("claim", "source_ids", "element_ids"):
            data = legacy_brief()
            data["explanation"] = explanation()
            del data["explanation"]["claim_visual_map"][0][key]
            self.assert_invalid(data, f"claim_visual_map[1].{key}")
        for value in (None, "", " ", 1, [], {}):
            with self.subTest(value=value):
                data = legacy_brief()
                data["explanation"] = explanation()
                data["explanation"]["claim_visual_map"][0]["claim"] = value
                self.assert_invalid(data, "claim_visual_map[1].claim")

    def test_claim_reference_types_and_unknown_ids(self):
        for key in ("source_ids", "element_ids"):
            for value in (None, [], {}, "s1", 1, [None], [""], [" "], [1], [{}], [["s1"]], ["unknown"]):
                with self.subTest(key=key, value=value):
                    data = legacy_brief()
                    data["explanation"] = explanation()
                    data["explanation"]["claim_visual_map"][0][key] = value
                    self.assert_invalid(data, f"claim_visual_map[1].{key}")

    def test_non_object_json_root(self):
        for value in (None, [], "text", 1, False):
            with self.subTest(value=value):
                self.assert_invalid(value, "JSON オブジェクト")

    def test_invalid_json_and_unreadable_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.json"
            for contents in (b"{", b"\xff"):
                with self.subTest(contents=contents):
                    path.write_bytes(contents)
                    result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("エラー:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
            result = subprocess.run([sys.executable, str(SCRIPT), directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
