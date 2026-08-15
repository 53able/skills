---
name: apple-container-validation
description: Apple Container上に再現可能な技術検証環境を構築し、コンテキストから論点・反証条件・オラクル・ケース行列を定義して、独立ケースを安全な上限内で並列実行し、ログと来歴を伴うMarkdownレポートへ集約する。Use when macOS上で実装、設定、互換性、性能、障害系、エージェント挙動などの技術的主張を隔離環境で実測するとき。Don’t use for Apple Containerを利用できない環境、iOS/macOS GUI自動化、GPU学習、法務判断、または実行を伴わない机上レビュー。
compatibility: Requires an Apple silicon Mac running macOS 26, Apple Container CLI, and Python 3.10 or later. Python harnesses with dependencies also require uv; TypeScript harnesses require Node.js, npm, TypeScript 7, tsx, and pino.
---

# Apple Container技術検証

## 目的

コンテキスト中の技術的主張を、反証可能なケース行列へ変換する。Apple Containerで各ケースを隔離し、可能な範囲で並列実行する。観察・推論・未検証事項を分離し、再実行可能なMarkdownレポートを1つ残す。

## 手順

### 1. 検証対象を固定する

1. コンテキストから主張、対象実装、比較対象、前提条件、想定利用者を抽出する。
2. 主張を1文の仮説へ変換する。
3. 仮説を棄却する条件を、実行前に列挙する。
4. 各定量値または合否判定に対応する最小オラクルを定義する。
5. 各ケースで、オラクル成立時の仮説との関係を `support`、`falsify`、`neutral` のいずれかに固定する。オラクル成立と仮説支持を混同しない。
6. オラクルを定義できない論点を「観察的」「未検証」「環境外」のいずれかへ分類する。推測値を合格条件にしない。
7. 検証対象のリポジトリ、コミット、依存バージョン、ホスト情報を記録する。作業ツリーが汚れている場合は差分の有無も記録する。

### 2. Apple Containerを事前確認する

1. `container --version` と `container system status` を実行する。
2. サービスが停止している場合は、実行前に利用者の許可を得て `container system start` を実行する。
3. CLIの構文が不明な場合だけ `references/apple-container-commands.md` を読む。その後、必ずローカルの `container <subcommand> --help` を正とする。
4. Apple Containerを利用できない場合は実験を捏造せず、レポートを `Blocked / Unverified` として保存する。

### 3. ケース行列を設計する

1. `assets/manifest-template.json` を検証ワークスペースへコピーする。
2. `references/manifest-spec.md` を読み、`manifest.json` を作成する。
3. PythonまたはJavaScript/TypeScriptで検証ハーネスを作る場合は、`references/runtime-conventions.md` を読む。
   - Pythonに外部依存がある場合は`uv`で管理し、`pyproject.toml`と`uv.lock`を固定する。
   - JavaScript系はTypeScript 7で実装し、実行ランナーに`tsx`、構造化ロガーに`pino`を使う。
4. Claude Code CLIまたはCodex CLIを使う場合は、`references/agent-cli-subscriptions.md`を読む。
   - `assets/agent-cli-Containerfile`から版固定イメージを作る。
   - Claude Codeは`CLAUDE_CODE_OAUTH_TOKEN`、CodexはChatGPT認証または`CODEX_ACCESS_TOKEN`を使い、APIキーを渡さない。
   - ログインとブラウザ承認はホスト上で人間が行い、認証情報をイメージ、manifest、Git、ログ、成果物へ保存しない。
5. `references/case-design.md` を読み、最低限次の群を含める。
   - 仮説が成立する代表ケース
   - 仮説が成立しない負例
   - 境界値と欠損値
   - 失敗、タイムアウト、再試行、部分成功
   - バージョン、設定、依存、資源制約の差
   - 見かけ上似ているが対象外のケース
6. 独立な検証軸を増やす。ケース数だけを水増しせず、失敗モードまたは交互作用を追加で覆うケースを優先する。
7. 非決定性が疑われるケースには `repeats` を設定する。決定的なケースは原則1回にする。
8. ネットワークを必要としないケースは `network: "none"` にする。外部通信、秘密情報、書き込みマウントは必要なケースだけ明示する。
9. 入力を読み取り専用でマウントし、各ケース固有の `/evidence` だけを書き込み先にする。

### 4. マニフェストを検証する

1. 次を実行する。

```bash
python3 scripts/validate-manifest.py path/to/manifest.json
```

2. エラーをすべて修正し、終了コード0になるまで再実行する。
3. 出力されたジョブ数、ケース群、反復数、推奨並列数を確認する。
4. オラクルのないケース、重複ID、同一コマンドの無意味な複製を残さない。

### 5. スモーク検証を行う

1. 代表ケース、負例、失敗系をそれぞれ1件以上選ぶ。
2. `--dry-run` で実行コマンドとマウントを確認する。
3. 少数ケース用の一時マニフェストを作るか、ケースを絞ったマニフェストで実行する。
4. 入力、出力、タイムアウト、終了コード、オラクル判定、コンテナ削除を確認する。
5. ハーネス不良があれば、本行列を実行する前に修正する。

### 6. 行列を並列実行する

1. 一意な `run-id` を指定して次を実行する。

```bash
python3 scripts/run-matrix.py path/to/manifest.json \
  --run-id YYYYMMDD-hhmmss \
  --concurrency auto
```

2. CPU、メモリ、APIレート制限、外部サービス制約のうち最も厳しい上限を並列度に採用する。
3. 独立ケースを並列実行する。共有状態を変更するケースへ同じ `exclusiveGroup` を付け、その群だけ直列化する。全体上限には `maxConcurrency` を使う。
4. 本番認証情報をイメージへ焼き込まない。必要な環境変数だけ `inheritEnv` で渡し、値をレポートへ記録しない。
5. 中断後は、マニフェストとイメージが同一であることを確認して `--resume` を使う。
6. 失敗ケースを削除しない。タイムアウト再試行はattemptごとに証跡を分離し、初回失敗を残す。通常のオラクル不成立を都合よく再試行しない。

### 7. 結果を検証する

1. `results/<run-id>/summary.json` と各ジョブの `result.json`、`stdout.log`、`stderr.log` を読む。
2. `oracle-pass` は期待観察との一致であり、主張の支持とは限らない。`relation` とケース群別、環境別、反復別の結果から結論を分ける。
3. タイムアウト、コンテナ起動失敗、オラクル不備を、対象実装の失敗と区別する。
4. 予想より整いすぎた結果には、入力ハッシュ、コマンド、ログ、負例、失敗例を再確認する。
5. 少なくとも1件の合格、1件の不合格または棄却例、1件の境界ケースをログから手作業で照合する。
6. 性能比較ではウォームアップ、反復、中央値とばらつき、ホスト負荷、並列干渉を確認する。単発値を一般化しない。

### 8. Markdownレポートを仕上げる

1. 自動生成された `results/<run-id>/report.md` を `assets/report-template.md` に沿って補完する。
2. 最終成果物を利用者が指定した場所、未指定なら `outputs/apple-container-validation-<slug>.md` へ保存する。
3. 次を必ず含める。
   - 検証対象と結論
   - 仮説と棄却条件
   - 環境と来歴
   - ケース行列とオラクル
   - 観察結果
   - 観察から導く推論
   - 反証、限界、未検証事項
   - 再実行コマンド
   - 生ログと集計への相対パス
4. 実測していない値を書かない。未完了は `Blocked`、`Unverified`、`Not run` のいずれかで示す。
5. ファイルを再読し、成果物が存在すること、古い仮値や未完了のTODOがないことを確認する。

## 並列化方針

- ケース生成は検証軸ごとに分け、独立ケースを同時に設計する。
- 実行はケース×反復をジョブへ展開し、ワーカープールで処理する。
- 初回は小さなスモーク行列を通し、その後に広い行列を実行する。壊れたハーネスを大量並列しない。
- 並列度は「可能な限り大きく」ではなく「証拠の独立性を壊さない範囲で最大」にする。
- 同一外部API、同一ポート、同一書き込み先、同一レート制限を共有するケースは競合を避ける。

## エラー処理

- `container` が見つからない場合は、インストールを勝手に行わず `Blocked: Apple Container CLI unavailable` と記録する。
- `container system status` が失敗した場合は、ローカルのヘルプを確認し、サービス状態とエラー全文をレポートする。
- イメージビルドに失敗した場合は、ビルドログを保存し、ケース実行へ進まない。
- ケースがタイムアウトした場合は、対象コンテナだけを強制削除し、他ケースを継続する。
- ディスク不足、メモリ不足、レート制限が発生した場合は並列度を下げ、新しいrun-idで再実行する。失敗runを上書きしない。
- `validate-manifest.py` が失敗した場合はstderrの項目を修正する。検証を迂回しない。
- 一部結果が欠けた場合は `--resume` を使う。マニフェストのハッシュが異なる場合は新しいrun-idを使う。
- Claude CodeまたはCodexでAPIキー認証が検出された場合は、subscription検証として扱わず実行を止める。
- Codexの書き込み可能`auth.json`方式は同じ認証キャッシュを並列共有せず、`--resume`も使わない。新しいrun-idで実行する。
