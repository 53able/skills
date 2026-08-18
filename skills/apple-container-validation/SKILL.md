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
4. Apple Containerを利用できない場合は実験を捏造せず、レポートのPreflight/report dispositionを `BLOCKED`、Claim outcomeを `UNVERIFIED` として保存する。ランナーを起動していないため、Execution statusは `not emitted (runner not invoked)` と記す。`executionStatus`はランナーが生成する`COMPLETE`、`INCOMPLETE`、`DRY RUN`だけに使う。

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
6. 独立な検証軸を増やす。ケース数だけを水増しせず、失敗モードまたは交互作用を追加で覆うケースを優先する。宣言した各棄却条件を最低1件の`relation: falsify`ケースへ接続し、`support`/`neutral`参照だけで済ませない。
7. 非決定性が疑われるケースには `repeats` を設定する。決定的なケースは原則1回にする。
8. ネットワークを必要としないケースは `network: "none"` にする。外部通信、秘密情報、書き込みマウントは必要なケースだけ明示する。
9. 入力を読み取り専用でマウントし、各ケース固有の `/evidence` だけを書き込み先にする。mount sourceはmanifest配下のsymlinkでない通常ファイルまたは実ディレクトリ、image context/fileはmanifest配下の相対パスに限定する。

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
4. 本番認証情報をイメージへ焼き込まない。必要な環境変数だけ `inheritEnv` で渡し、値をレポートへ記録しない。stdout/stderrオラクルはリダクト前の出力をメモリ内で判定し、ログ、image inspect/build log、failure記録にはホスト環境変数の空でない完全一致値を固定点まで削除した出力だけを保存する。runner/validatorの診断はイベント順に全recordと終端改行を1本のstreamへbufferし、固定点削除と最終byte検査後、1回のCLI invocationにつき1つの物理channelだけへ一度だけ出力する。runnerは終了コード0ならstdout、非0ならstderr、validatorは`--json`なら常にstdout、text modeはvalidならstdout、invalidならstderrを使い、もう一方のchannelは空にする。argparseのusageや未知引数値は直接出力せず、`invalid arguments`だけをbufferする。artifactの通常ファイルも判定・hash前に同じ値を固定点まで走査・削除し、検出時は`oracle-fail`にする。runner所有JSON/Markdown/textは最終bytesへserializeした後にも同じ値を検査し、JSON句読点などの境界で値が再構成されて安全に保存できない場合はpublish前にfail closedする。ただしエンコード、変形、分割された値は検出できず、post-process前の中断では0700のevidence内に生値が残り得る。`inheritEnv`を1件でも使うrunでは値を来歴へ保存しないため、`--resume`を禁止する。中断後は新しいrun-idで実行する。
5. `inheritEnv`を使わないrunの中断後は、マニフェストとイメージが同一であることを確認して `--resume` を使う。`--resume`が再利用するのは`result.json`まで原子的に保存された完成済みジョブだけである。既存jobのlog/result/attempt/artifact整合性を全件先に検証し、non-UTF-8の永続logを含め1件でも拒否した場合は既存job treeをbyte単位で変更せず、新しいsummary/reportもpublishしない。`result.json`がない部分attemptは証跡を保持したまま拒否するため、部分job状態を`results/<run-id>/`ツリー全体の外へ移すか、新しいrun-idを使う。run root内の別位置へ移さず、部分状態を削除・上書きしない。symlinkを含む`--results-dir`は使えない。
6. 失敗ケースを削除しない。タイムアウト再試行はattemptごとに証跡を分離し、初回失敗を残す。通常のオラクル不成立を都合よく再試行しない。

### 7. 結果を検証する

1. `results/<run-id>/summary.json` と、その`reportArtifact.path`が指す世代別report、各ジョブの `result.json`、`attempts/<n>/stdout.log`、`attempts/<n>/stderr.log`、`attempts/<n>/evidence/` を読む。権威あるpairは`summary.json`とSHA-256で結ばれた世代別reportであり、`report.md`は更新失敗時に古い可能性があるconvenience copyである。ジョブルートの`stdout.log`と`stderr.log`は最終attemptの写しであり、以前のtimeout証跡とattempt作成後の基盤例外証跡は`attempts/`配下に残る。timeout後のcontainer cleanupは10秒の有限timeoutで実行する。cleanupの起動失敗・非0終了・timeoutは、genericなcleanup failureを含むhash-boundな`infrastructure-error`として同じattemptに残る。入力tree配下へresultsを置いた場合は`run-manifest.json.treeHashExclusions`のskill bundle、image context、全mount sourceの除外も確認する。入力tree内のsymlink、FIFO、socketなど未対応型は来歴hashを作らず制御された入力エラーになる。
2. `oracle-pass` は期待観察との一致、`oracle-fail` は期待観察との不一致を示す。stdout/stderr条件は取得した生出力をメモリ内で判定するため、秘密値の漏えいを否定条件で検出できる。保存ログとfailure記録はその後にリダクトされる。どちらのstatusもジョブの観察と判定を完了した状態であり、主張の支持とは限らない。
3. 実行状態と仮説評価を分けて読む。
   - `COMPLETE`: 全ジョブが `oracle-pass` または `oracle-fail` まで到達した。
   - `INCOMPLETE`: タイムアウト、基盤エラー、結果欠損などで判定できないジョブがある。
   - `DRY RUN`: コマンド生成だけを行った。
4. `relation` と反復を含む期待ジョブから仮説を評価する。実行状態が`INCOMPLETE`でも、判定できた証拠は捨てない。
   - 期待ジョブIDと一意に対応する`falsify`の `oracle-pass` が1件でもあれば、ほかの欠損や未判定より優先して `FALSIFIED` とする。重複した結果は反証証拠に数えない。
   - `support`が1件以上あり、期待した全`support`ジョブが一意に存在して `oracle-pass`、期待した全`falsify`ジョブが一意に存在して判定済みの `oracle-fail`、かつ重複・期待外・匿名結果がない場合だけ `SUPPORTED WITHIN TESTED SCOPE` とする。
   - `support`または`falsify`の欠損、未判定、timeout、基盤エラー、期待外・匿名・重複結果、`support`の`oracle-fail`、または支持証拠なしなら `UNVERIFIED` とする。
   - `neutral`は仮説評価を直接動かさない。証拠整合性に異常がない限り、`neutral`だけの欠損や未判定は実行状態を`INCOMPLETE`にするが、完全な支持証拠を消さない。重複した`neutral`結果は証拠整合性の異常として支持を止める。
5. タイムアウト、コンテナ起動失敗、オラクル不備を、対象実装の失敗と区別する。Apple Container CLIはpayloadの終了コードを返す一方、起動・設定失敗とpayload終了を機械可読に区別する公開契約がないため、非ゼロ終了だけで基盤エラーに分類しない。起動失敗の終了コードや出力がオラクルへ偶然一致すると`oracle-fail`だけでなく`oracle-pass`にもなり、`SUPPORTED WITHIN TESTED SCOPE`または`FALSIFIED`へ影響し得る。claim-bearing caseにはpayloadだけが生成するstdout markerまたは`exists: true`の通常ファイルartifactを含め、stderrとApple Containerのsystem logも手作業で確認する。runnerの`launcherOriginVerification`が`NOT VERIFIED BY RUNNER`なら`claimOutcome`は暫定であり、CIは単独で主張真偽のgateに使わず、外部または記録済みattestationを要求する。Agent CLI intentがなければ認証確認は`NOT APPLICABLE`、あってもrunnerが証拠を記録しなければ`NOT VERIFIED BY RUNNER`である。
6. 予想より整いすぎた結果には、入力ハッシュ、コマンド、ログ、負例、失敗例を再確認する。
7. 少なくとも1件の合格、1件の不合格または棄却例、1件の境界ケースをログから手作業で照合する。
8. 性能比較ではウォームアップ、反復、中央値とばらつき、ホスト負荷、並列干渉を確認する。単発値を一般化しない。

### 8. Markdownレポートを仕上げる

1. `summary.json.reportArtifact.path`がrun root直下の世代別reportを指すことを確認し、そのファイルのSHA-256が`summary.json.reportArtifact.sha256`と一致することを検証する。
2. 検証済みの世代別reportを、利用者が指定した場所、未指定なら `outputs/apple-container-validation-<slug>.md` へコピーする。証拠である世代別reportやconvenience copyの`report.md`を直接編集しない。
3. コピーした利用者向けファイルだけを `assets/report-template.md` に沿って補完する。
4. 次を必ず含める。
   - 検証対象と結論
   - 仮説と棄却条件
   - 環境と来歴
   - ケース行列とオラクル
   - 観察結果
   - 観察から導く推論
   - 反証、限界、未検証事項
   - 再実行コマンド
   - 生ログと集計への相対パス
5. 実測していない値を書かない。`READY`はホストpreflightを通過してrunnerがレポートを出力したことだけを示し、実行完了や主張支持を意味しない。`READY`と`INCOMPLETE`は両立する。runner起動前の停止はPreflight/report dispositionで`BLOCKED`または`NOT RUN`とし、`executionStatus`は「runner未起動のため未出力」と記す。架空のenum値を作らない。
6. ファイルを再読し、成果物が存在すること、古い仮値や未完了のTODOがないことを確認する。

## 並列化方針

- ケース生成は検証軸ごとに分け、独立ケースを同時に設計する。
- 実行はケース×反復をジョブへ展開し、ワーカープールで処理する。
- 初回は小さなスモーク行列を通し、その後に広い行列を実行する。壊れたハーネスを大量並列しない。
- 並列度は「可能な限り大きく」ではなく「証拠の独立性を壊さない範囲で最大」にする。
- 同一外部API、同一ポート、同一書き込み先、同一レート制限を共有するケースは競合を避ける。

## エラー処理

- `container` が見つからない場合は、インストールを勝手に行わず `BLOCKED: Apple Container CLI unavailable` と記録する。
- `container system status` が失敗した場合は、ローカルのヘルプを確認し、サービス状態とエラー全文をレポートする。
- イメージビルドに失敗した場合は、ビルドログを保存し、ケース実行へ進まない。
- ケースがタイムアウトした場合は、対象コンテナだけを強制削除し、他ケースを継続する。
- ディスク不足、メモリ不足、レート制限が発生した場合は並列度を下げ、新しいrun-idで再実行する。失敗runを上書きしない。
- `validate-manifest.py` が失敗した場合は、text modeではstderr、`--json`ではstdoutの`errors`を修正する。JSON不正・巨大整数・引数不正は文書内容や未知引数値をechoしないgeneric errorになる。JSON内の全文字列とobject keyはUnicode scalar値だけを許可し、lone surrogateを拒否する。検証を迂回しない。
- `inheritEnv`を使わないrunで一部結果が欠けた場合だけ`--resume`を使う。マニフェストのハッシュが異なる場合、または`inheritEnv`を1件でも使う場合は新しいrun-idを使う。
- Claude CodeまたはCodexでAPIキー認証が検出された場合は、subscription検証として扱わず実行を止める。
- Codexの書き込み可能`auth.json`方式は同じ認証キャッシュを並列共有せず、`--resume`も使わない。加えて、Claude/Codexを問わず`inheritEnv`を使うrunでは`--resume`を禁止する。新しいrun-idで実行する。
