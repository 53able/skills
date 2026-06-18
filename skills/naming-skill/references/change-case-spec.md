# change-case spec 参照メモ

このスキルのローカル整形スクリプト `scripts/format_name.py` は、`change-case` の公開テスト仕様を参考にする。

## 主要な期待値

`test string` は次のように変換される。

| 形式 | 期待値 |
|---|---:|
| `camelCase` | `testString` |
| `capitalCase` | `Test String` |
| `constantCase` | `TEST_STRING` |
| `dotCase` | `test.string` |
| `kebabCase` | `test-string` |
| `noCase` | `test string` |
| `pascalCase` | `TestString` |
| `pascalSnakeCase` | `Test_String` |
| `pathCase` | `test/string` |
| `sentenceCase` | `Test string` |
| `snakeCase` | `test_string` |
| `trainCase` | `Test-String` |

## 分割ルールの要点

- 空文字は空の名前になる。
- 空白や句読点などの非単語文字は区切りとして扱う。
- `TestV2` は通常 `test-v2` のように、`V2` を1語として扱う。
- `--separate-numbers` 相当では `TestV2` を `test-v-2` のように、数字をより細かく分ける。
- `version 1.2.10` は `version-1-2-10` のように数字を区切る。
- `camelCase` と `pascalCase` では、数字語が途中に来る場合、曖昧性回避のため `_` が入る。例: `version 1.2.10` → `version_1_2_10`, `Version_1_2_10`。
- `--merge-ambiguous-characters` 相当では、`version 1.2.10` → `version1210`, `Version1210` のように結合する。
- `prefixCharacters` / `suffixCharacters` 相当では、指定された先頭・末尾文字を保持する。例: `__typename` + prefix `_` → `__typename`。

## このスキルでの扱い

- 命名候補の意味づけはエージェントが行う。
- 最終的なケース変換・区切り変換は、原則として `scripts/format_name.py` で行う。
- 変換ロジックを変更した場合は、`scripts/verify_format_name.py` で代表ケースを検証する。
- `change-case` 本体を依存関係として要求せず、ローカルスクリプトで再現可能な範囲を実装する。
