# change-case 由来の命名形式

このスキルでは、`change-case` パッケージの README にある命名形式を参考にする。同 README では、`camelCase`, `PascalCase`, `Capital Case`, `snake_case`, `kebab-case`, `CONSTANT_CASE` などの相互変換が説明されている。

## 対応する形式名

| ユーザー指定 | 出力例 | 備考 |
|---|---:|---|
| `kebab`, `kebab-case`, `param-case` | `two-words` | 移植性の高い名前やWebスラッグ向けの標準候補。 |
| `snake`, `snake_case` | `two_words` | Python、データ処理、設定値などで使いやすい。 |
| `camel`, `camelCase` | `twoWords` | JavaScript系の慣習に合わせたい場合に使う。 |
| `pascal`, `PascalCase` | `TwoWords` | クラス名風、生成コード風の名前に使う。 |
| `constant`, `CONSTANT_CASE` | `TWO_WORDS` | 環境変数や定数風の名前に使う。通常の名前では多用しない。 |
| `dot`, `dot.case` | `two.words` | 名前空間風の設定名などに使う。 |
| `path`, `path/case` | `two/words` | ディレクトリ分割を意図する場合だけ提案する。 |
| `train`, `Train-Case` | `Two-Words` | 技術的な名前では珍しい。明示指定された場合だけ使う。 |
| `capital`, `Capital Case` | `Two Words` | スペースを含めてよい場合だけ使う。 |
| `sentence`, `Sentence case` | `Two words` | 文章風の名前が必要な場合だけ使う。 |
| `no`, `no case` | `two words` | 中間表現。スペース区切りが指定された場合だけ使う。 |
| `pascal-snake`, `Pascal_Snake_Case` | `Two_Words` | 明示指定された場合だけ使う。 |

## 安全性メモ

- 大文字が必要な形式を除き、ASCII小文字を優先する。
- 形式で必要な区切り文字以外の句読点は避ける。
- 拡張子は、ユーザーが指定した場合または求めた場合だけ維持する。
- 1つの名前を作る場合はパス区切りを避ける。`path/case` はディレクトリを作る。
