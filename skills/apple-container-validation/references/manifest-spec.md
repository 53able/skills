# 検証マニフェスト仕様

必要になったときだけ本ファイルを読む。

## ルート

```json
{
  "version": 1,
  "slug": "short-experiment-name",
  "claim": "検証する技術的主張",
  "hypothesis": "条件付きで反証可能な仮説",
  "falsificationCriteria": [{"id": "criterion-main", "description": "棄却条件1"}],
  "image": {},
  "defaults": {},
  "mounts": [],
  "cases": []
}
```

- `slug`: 小文字英数字とハイフンだけを使う。
- `claim`: 元の主張を短く保つ。
- `hypothesis`: 対象、条件、期待結果を含める。
- `falsificationCriteria`: 一意なIDと説明を実行前に定義する。結果を見て変更しない。

## image

既存イメージを使う場合:

```json
{"tag": "python:3.13-slim"}
```

ローカルでビルドする場合:

```json
{
  "tag": "validation-example:20260815",
  "context": "image",
  "file": "image/Containerfile",
  "pull": false
}
```

`context` と `file` はマニフェストの親ディレクトリ配下にある、dot/`..`・絶対指定・制御文字・symlink componentを含まない相対パスにする。`context`は実ディレクトリ、`file`はそのcontext配下の通常ファイルに限定する。再現性を優先し、ベースイメージと依存バージョンを固定する。

検証ハーネスのランタイム規約は`references/runtime-conventions.md`に従う。Pythonに外部依存がある場合は`uv`、JavaScript系ではTypeScript 7、`tsx`、`pino`を使用する。対応するlockfileと設定ファイルをbuild contextへ含める。

## defaults

```json
{
  "network": "none",
  "cpus": 1,
  "memory": "2G",
  "timeoutSeconds": 120,
  "retries": 0,
  "repeats": 1,
  "maxConcurrency": 8,
  "readOnlyRoot": true,
  "allowWritableMounts": false
}
```

- `network`: 通信不要なら `none`、必要な場合だけ `default` または明示したネットワーク名を使う。
- `cpus` / `memory`: 1ケース当たりの上限。ホスト容量を超える並列度を指定しない。
- `retries`: ハーネスまたは外部依存の一時失敗を観察するための再試行回数。結果の見栄えを良くする目的で増やさない。
- `repeats`: 非決定性または性能分布を測る反復数。
- `readOnlyRoot`: 原則 `true`。一時ファイルは `/tmp`、証跡は `/evidence` を使う。
- `allowWritableMounts`: 原則 `false`。明示的に有効化した場合、root-level mountは全ケースで共有されるためランナーが全ジョブを直列化する。並列性が必要なら書き込みを各ジョブ固有の `/evidence` に限定する。

## mounts

```json
[
  {
    "source": "./fixture",
    "target": "/workspace",
    "readonly": true
  }
]
```

- `source`はmanifest配下のsymlinkでない通常ファイルまたは実ディレクトリに限定する。FIFO、socket、deviceなどの特殊ファイルは拒否する。
- 入力は読み取り専用にする。
- `/evidence` はランナーが予約するため指定しない。
- 書き込み可能マウントはケース間で共有しない。

## cases

```json
{
  "id": "timeout-negative",
  "group": "failure",
  "description": "応答が停止した場合に制限時間内で終了するか",
  "relation": "support",
  "agentCli": "claude-code-subscription",
  "criterionIds": [],
  "exclusiveGroup": "upstream-api",
  "command": ["sh", "-lc", "run-test --mode timeout > /evidence/measurement.json"],
  "env": {"MODE": "strict"},
  "inheritEnv": ["CLAUDE_CODE_OAUTH_TOKEN"],
  "network": "none",
  "cpus": 1,
  "memory": "1G",
  "timeoutSeconds": 30,
  "retries": 0,
  "repeats": 3,
  "readOnlyRoot": true,
  "oracle": {
    "exitCode": 0,
    "stdoutContains": ["timeout handled"],
    "stdoutNotContains": ["secret"],
    "stderrContains": [],
    "stderrNotContains": ["panic"],
    "artifacts": [
      {"path": "measurement.json", "exists": true, "contains": "elapsed_ms"}
    ]
  }
}
```

- `relation`: オラクル成立時に仮説を `support`、`falsify`、または `neutral` のどれへ動かすかを指定する。`falsify` は `criterionIds` を必須にし、宣言した各棄却条件は最低1件の有効な`relation: falsify`ケースから参照する。`support`/`neutral`からの参照だけでは運用上の反証可能性を満たさない。`falsify`では、棄却条件が実際に観察されたとき成立するオラクルを定義する。健全な対象でその観察が生じなければ、ジョブは判定済みの`oracle-fail`になる。
- `agentCli`: CLIを使う場合だけ`claude-code-subscription`または`codex-subscription`を指定する。認証方式と安全条件は`references/agent-cli-subscriptions.md`に従う。
- `criterionIds`: 検証する棄却条件IDを指定する。
- `exclusiveGroup`: 同じ共有資源を使うケースへ同じ値を付け、その群だけ直列化する。
- `command`: argv配列にする。パイプ、リダイレクト、複合コマンドが必要な場合だけ `sh -lc` を明示する。
- `env`: 公開可能な固定値だけを置く。
- `inheritEnv`: ホストから渡す環境変数名だけを置く。値はマニフェストや来歴へ書かない。stdout/stderrオラクルはリダクト前の生出力をメモリ内で判定し、その後、保存ログ、image inspect/build log、hash対象、failure記録ではホスト環境変数の完全一致値をリダクトする。runner/validator診断はイベント順に全recordと終端改行を1本のstreamへbufferし、完全なstreamへリダクトと最終byte検査を適用してから、invocationごとに1つの物理channelだけへ一度だけ出力する。runnerは終了コード0ならstdout、非0ならstderr、validatorは`--json`なら常にstdout、text modeはvalidならstdout、invalidならstderrを使う。もう一方のchannelは空で、統合時のchannel境界で秘密値が再構成されない。argparseはusage、未知option、値を直接echoせずgenericな`invalid arguments`を同じbufferへ入れる。artifactは任意のバイナリなので、オラクル判定とhash計算の前に通常ファイルを走査し、既知の空でない完全一致値があれば、削除による連結で別の既知値が生じなくなるまで固定点で削除して`oracle-fail`にする。さらにrunner所有JSON/Markdown/textは構造をリダクトして最終bytesへserializeした後、全既知値が不在であることをpublish前に検査する。JSON句読点などの境界をまたいで値が再構成され、安全なserializeができない場合は成果物を変更せずfail closedする。hashはサニタイズ後の保存bytesを表す。エンコード、変形、分割された秘密値は検出できず、runnerがpost-processする前に中断すれば生値が残り得る。この残余リスクを減らすためrunner所有ディレクトリは0700、ファイルは0600にするが、同一ユーザーからの秘匿は保証しない。parse不能なmanifestでは`inheritEnv`名を取得できないため、validatorは文書内容や詳細例外をechoせずgeneric errorだけを出す。JSON decode時は全文字列とobject keyを再帰的に検査し、U+D800–U+DFFFのlone surrogateを拒否する。Pythonの整数変換上限を超えるJSONも`ValueError`詳細や数字列を出さずmalformed JSONとして扱う。Claude Code subscriptionでは`CLAUDE_CODE_OAUTH_TOKEN`、Codex workspace access tokenでは`CODEX_ACCESS_TOKEN`だけを許可する。APIキーは渡さない。1ケースでも`inheritEnv`を使うrunは、値が同一だったことを安全に証明できないため`--resume`を禁止し、新しいrun-idを使う。
- `oracle`: 最低1項目を定義する。既定の期待終了コードは0。stdout/stderr条件は生出力をメモリ内で評価するが、結果ファイルへ生出力や秘密値を含むfailure excerptは保存しない。claim-bearing caseではpayload由来の正の証拠として、空でない`stdoutContains`または`exists: true`を明示したartifactを含める。否定条件、stderr、存在しないartifactだけではpayload起動を証明しない。markerの一意性はvalidatorで証明できないため、stderrとApple Container system logも確認する。
- `artifacts.path`: `/evidence` からの相対パスにする。絶対パス、`..`、NUL/CR/LFを含む制御文字は禁止する。`exists: false`と`contains`は併用できない。`exists: true`が成立するのはevidence root内のsymlinkでない通常ファイルだけで、ディレクトリ、FIFO、socket、deviceなどは不成立とする。`contains`もこの通常ファイルだけを読む。`exists: false`はパスの不在だけを確認する。

## 証跡

ランナーは次を保存する。

```text
results/<run-id>/
  image-build.log              # context build時だけ
  image-inspect.json           # dry-runでは未inspectの記録
  run-manifest.json
  summary.json                 # 権威あるcommit record
  report.<generation>.md       # summary.reportArtifactが参照する権威あるreport
  report.md                    # convenience copy。更新失敗時は古い可能性あり
  jobs/<case-id>-r<repeat>/
    result.json                # jobがresult publishまで到達した場合
    stdout.log                 # 実行時のみ。最終attemptの写し
    stderr.log                 # 実行時のみ。最終attemptの写し
    attempts/<n>/              # 実行時のみ。retry回数に応じて複数
      stdout.log
      stderr.log
      evidence/                # 空の場合もある
```

`run-manifest.json` はマニフェスト、解決済みイメージ、build context、Containerfile、mount入力、skill bundle、ジョブ集合、並列度、Apple Containerバージョン、ホストのSHA-256または値を固定する。tree hashは通常ファイルと実ディレクトリを型付きでframeし、nested symlink、FIFO、socketなど未対応型を制御された入力エラーとして拒否する。入力tree hashはrun root作成前に完了させる。来歴、ログ、結果、集計、レポートは、同一ディレクトリに排他的に作った予測困難な一時ファイルから0600で置換し、既存の一時symlinkや出力先symlinkのtargetをたどらない。runner所有ディレクトリは0700にする。`--results-dir`はresolve前のlexical pathに既存symlink componentがある場合に拒否する。ジョブ、attempt、evidenceの各ディレクトリは、run root配下の実ディレクトリでsymlinkを含まないことを作成前後に検証し、resume前と最終publish前にrun root、`jobs/`、job root、attempts、各attemptの許可entryを閉じたschemaとして検査する。run rootは文書化した固定ファイル、`jobs/`、`report.md`、妥当なimmutable世代reportだけを許可し、移動した部分jobなどの兄弟entryを拒否する。evidence配下はsymlink・特殊ファイルを拒否して通常ファイルを`artifactSha256`へ再結合する。attempt作成後のsubprocess基盤例外も、リダクト済みlog、artifact hash、attempt recordを保存した`infrastructure-error`として結合する。timeout後のcontainer cleanupには`CONTAINER_CLEANUP_TIMEOUT_SECONDS = 10.0`を適用する。cleanup起動・非0終了・例外・cleanup timeoutは、元のtimeoutではなくgenericなcleanup failureを明示したhash-boundな`infrastructure-error`として同じattemptを完結させる。dry-runまたはattempt前基盤エラーのhash未記録evidenceは空でなければ拒否する。`jobs/`は期待job ID集合とも照合する。これは通常の部分状態や事前配置symlinkを拒否するが、同一ユーザーが検証と利用の間に同時変更するTOCTOU raceに対するdirfd/openatベースの完全な耐性は保証しない。fsyncや電源断耐性も保証しない。

権威ある最終成果物は`summary.json`と、その`reportArtifact.path`が指す予測困難な世代名のreportである。runnerは一度publishした世代別reportを上書きしない。results rootがskill bundle、image context、mount directory配下にある場合、入力来歴をrun追加から安定させるためresults subtreeをresolve前にlexical exclusionし、`treeHashExclusions`へ`skillBundle`、`imageContext`、全`mountSources`の構造で記録する。除外内のsymlink先をhashへ混入させない。results rootがskill rootと同一/祖先、またはhashed input directoryと同一なら意味のあるhashを作れないため拒否する。runnerはreportと最終summaryのserialize済みbytesを秘密値検査してから世代別reportをpublishし、そのpath/hashを含む`summary.json`を最後に原子的に置換する。runnerとvalidatorの診断は全recordと終端改行をイベント順の単一streamへbufferし、完全なstreamへ固定点削除・最終byte検査を適用した後、上記channel policyに従う1つの物理channelへ一度だけ出力する。summary置換後に失敗し得る整合性検査は行わない。report生成・publish失敗時は旧summaryを残し、summary publish失敗時の世代別reportは非権威の孤児になる。`report.md`は互換用copyであり、その更新失敗はcommit済みpairを無効にしない。動的manifest/result/failure文字列は単一行へ正規化し、ASCII Markdown句読点をnumeric character entityへ変換して、image、link、emphasis、autolink、raw HTML、heading、code、table構造を生成できないinert textにする。証拠一覧は実在するmode別ファイルだけを列挙する。

`--resume` は固定した来歴とattempt別ログ・artifact hashが一致し、`result.json`まで原子的に保存された完成済みジョブだけを再利用する。全既存完成jobを新規job実行前に検証し、hashが一致していてもattempt/final logがUTF-8としてdecodeできない場合を含め、1件でも整合性を拒否した場合は既存job treeをbyte単位で変更せず、新しい権威あるsummary/reportもpublishしない。`result.json`がない部分attemptは保存したまま拒否する。部分job状態は`results/<run-id>/`ツリー全体の外へ移すか、新しいrun-idを使う。run rootや`jobs/`内の別位置へ移してはならない。ランナーは部分証跡を自動削除・上書き・隔離しない。`inheritEnv`を使うrunは値を保存・比較しないためresumeできない。

## 実行状態と仮説評価

`summary.json` version 2では、実行状態をオラクル成立数から分離する。これは出力スキーマの版であり、入力マニフェストの`version: 1`とは別に管理する。

| `executionStatus` | 意味 | ランナー終了コード |
|---|---|---:|
| `DRY RUN` | 全期待ジョブのコマンド生成が欠損・重複・基盤エラーなく完了した | 0 |
| `COMPLETE` | 全ジョブが`oracle-pass`または`oracle-fail`まで到達した | 0 |
| `INCOMPLETE` | `timeout`、`infrastructure-error`、結果欠損、未知状態がある | 1 |

`claimOutcome`は実行状態と独立して、利用可能な判定済み証拠から次の順で集約する。

1. 全期待ジョブが1件ずつ`dry-run`なら`DRY RUN`かつ`UNVERIFIED`。dry run中でも欠損、重複、期待外、基盤エラー、未知状態があれば`INCOMPLETE`かつ`UNVERIFIED`。
2. 欠損や未判定が別ジョブにあっても、期待IDへ一意に対応する`falsify`の`oracle-pass`が1件あれば`FALSIFIED`。重複した`falsify`結果は反証証拠に数えない。
3. `support`が1件以上あり、期待した全`support`ジョブが1件ずつ存在して`oracle-pass`、期待した全`falsify`ジョブが1件ずつ存在して判定済みの`oracle-fail`、かつ重複・期待外・匿名結果がなければ`SUPPORTED WITHIN TESTED SCOPE`。証拠整合性に異常がない限り、`neutral`だけの欠損や未判定はこの支持証拠を消さない。
4. `support`または`falsify`の欠損、重複、未判定、timeout、基盤エラー、`support`の`oracle-fail`、期待外・匿名結果、重複した`neutral`結果、または支持証拠なしなら`UNVERIFIED`。

反復も個別ジョブとして同じ規則を適用する。したがって、`support`反復の`oracle-fail`が1件でもあれば支持判定にはならず、一意な`falsify`反復の`oracle-pass`が1件でもあれば反証となる。`neutral`は仮説評価を直接動かさないが、その重複は証拠整合性の異常として支持を止める。重複、未知、期待外、匿名の結果は実行を`INCOMPLETE`にする。

`counts`は`oracle-pass`、`oracle-fail`、`timeout`、`infrastructure-error`、`dry-run`、`other/unadjudicated`を常に出力し、該当がない状態も0で残す。

`summary.json`は`authenticationVerification`、`launcherOriginVerification`、`claimEvaluationQualification`も出力する。CLI intentがなければ認証は`NOT APPLICABLE`、あれば実際の非secret preflight証拠をrunnerが記録していないため`NOT VERIFIED BY RUNNER`である。dry runまたはclaim-bearing caseがなければlauncher由来は`NOT APPLICABLE`、実行したclaim-bearing runでは既定で`NOT VERIFIED BY RUNNER`とし、このときclaim評価は`PROVISIONAL`になる。system logを確認したとは自動記録しない。CIは`claimOutcome`単独を主張真偽のgateにしてはならない。run完了には`executionStatus`を使い、主張を受理するには外部または別途記録したlauncher-origin attestationを必須にする。

### version 1からの移行

version 1が出力した`INCOMPLETE OR ORACLE MISMATCH`はversion 2で廃止した。version 2のランナー終了コード0は、全期待ジョブの判定完了またはdry runを意味し、主張の支持を意味しない。支持判定へ移行するときは、全`support`の成立だけでなく、全`falsify`が欠損なく判定済みであることと、重複・期待外・匿名結果がないことも確認する。`falsify`のtimeoutや欠損を「反証なし」と読み替えてはならない。利用側は`counts.oracle-fail`も読み、実行未完了と期待観察の不一致を分ける。さらに、固定`report.md`との暗黙のpairを前提にせず、`summary.json.reportArtifact`の世代別path/hashを検証する。CIは`claimOutcome`単独ではなく、`executionStatus`と外部launcher-origin attestationを分けて扱う。

## Apple Container起動失敗の識別限界

Apple Containerの`container run`はpayloadの終了コードをプロセス終了コードとして返す。現行の公開CLI契約には、起動・設定失敗とpayloadの同じ非ゼロ終了コードを機械可読に区別するフィールドや専用終了コード範囲がない。ランナーはPython例外など実行ハーネス自身が捕捉した失敗を`infrastructure-error`、タイムアウトを`timeout`にするが、`container run`が通常の終了として返した起動・設定失敗は`oracle-fail`になり得る。終了コードや出力がpayload用オラクルへ偶然一致すれば`oracle-pass`にもなり、`SUPPORTED WITHIN TESTED SCOPE`または`FALSIFIED`へ影響し得る。非ゼロ終了の一律分類やstderr文字列ヒューリスティックは、正当なpayloadを誤分類するため行わない。claim-bearing caseにはpayloadだけが生成するstdout markerまたは`exists: true`を明示したartifactを含め、stderrとApple Containerのsystem logも手作業で確認する。validatorのpayload-origin警告はこの曖昧性への注意であり、markerの一意性や起動成功・失敗の証明ではない。
