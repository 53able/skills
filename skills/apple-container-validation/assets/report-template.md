# Apple Container検証レポート: <主張>

## ステータス

- Preflight/report disposition: `<READY / BLOCKED / NOT RUN>`
- Claim outcome: `<SUPPORTED WITHIN TESTED SCOPE / FALSIFIED / UNVERIFIED>`
- Execution status: `<COMPLETE / INCOMPLETE / DRY RUN>`
- Run ID: `<run-id / none>`
- 検証日: `<ISO 8601>`
- 判定済みジョブ: `<oracle-pass + oracle-fail> / <全ジョブ>`

`READY`はホストpreflightが成功し、runnerがレポートを出力したことだけを示す。実行完了や主張支持を意味せず、`READY`と`INCOMPLETE`は両立する。`COMPLETE`は全ジョブを観察してオラクル判定まで完了したことを示し、全オラクル成立を意味しない。`oracle-fail`も判定済みである。タイムアウト、基盤エラー、結果欠損は`INCOMPLETE`とする。runner起動前に停止した場合はPreflight/report dispositionへ`BLOCKED`または`NOT RUN`を書き、Execution statusは`not emitted (runner not invoked)`と記す。これは第4の`executionStatus`値ではない。

## 要約

検証した範囲、主要な観察、主張が支持された範囲を簡潔に記述する。

## 仮説と棄却条件

### 仮説

<対象、条件、期待結果を含む仮説>

### 棄却条件

- <実行前に決めた条件>

## 環境と来歴

| 項目 | 値 |
|---|---|
| Host | `<macOS / arch>` |
| Apple Container | `<version>` |
| Image | `<tag / digest>` |
| Repository | `<URL or local project name>` |
| Commit | `<SHA>` |
| Worktree | `<clean / dirty>` |
| Manifest SHA-256 | `<hash>` |
| Tree hash exclusions | `<skillBundle / imageContext / mountSources>` |
| Parallelism | `<workers>` |
| Agent CLI | `<none / Claude Code / Codex>` |
| CLI version | `<full version>` |
| Authentication method | `<none / subscription OAuth / ChatGPT / workspace access token>` |
| Authentication verification | `<NOT APPLICABLE / NOT VERIFIED BY RUNNER / externally verified>` |
| Launcher-origin verification | `<NOT APPLICABLE / NOT VERIFIED BY RUNNER / externally verified>` |
| Claim evaluation qualification | `<NOT APPLICABLE / PROVISIONAL / externally attested>` |
| Model / reasoning | `<model and effort/reasoning setting>` |

`claimOutcome`はlauncher由来が外部または記録済み証拠で確認されるまで暫定である。CIは`claimOutcome`単独を主張真偽のgateにせず、実行完了には`executionStatus`を使う。

## ケース行列とオラクル

| Case | Group | Relation | Purpose | Oracle | Repeats |
|---|---|---|---|---|---:|
| `<id>` | `<target/boundary/negative/failure>` | `<support/falsify/neutral>` | `<目的>` | `<判定条件>` | 1 |

## 観察結果

観察事実だけを記述する。各数値または判定を `summary.json`、`result.json`、ログ、生成物のいずれかへ結び付ける。

| Case | Status | Observation | Evidence |
|---|---|---|---|
| `<id>` | `<oracle-pass/oracle-fail/timeout/infrastructure-error/dry-run/unknown>` | `<観察>` | `<relative path>` |

未知のper-job statusは`summary.json.counts["other/unadjudicated"]`へ集計する。attempt作成後のsubprocess基盤例外は`infrastructure-error`として、リダクト済みlog、artifact hash、attempt recordへ結び付ける。

## 推論

観察から導ける範囲を記述する。観察と同じ節へ混ぜない。期待IDへ一意に対応する`falsify`の`oracle-pass`が1件でもあれば、実行状態が`INCOMPLETE`でも反証とする。検証範囲内で支持できるのは、期待した`support`が1件以上あり、全`support`が一意に存在して`oracle-pass`、全`falsify`が一意に存在して判定済みの`oracle-fail`、かつ重複・期待外・匿名結果がない場合だけである。証拠整合性に異常がない限り、`neutral`だけの欠損や未判定は支持証拠を消さない。`support`または`falsify`の欠損・未判定・timeout・基盤エラーや証拠整合性異常があれば未検証とする。

## 反証と不一致

仮説に反する結果、期待外れのケース、説明できないばらつきを残す。都合の悪い反復を削除しない。

## 限界と未検証事項

- `<対象外のOS、アーキテクチャ、バージョン>`
- `<測定誤差、並列干渉、外部依存>`
- `<NOT RUN / BLOCKED / UNVERIFIED>`

## 推奨する次の検証

1. 不確実性を最も減らす小さな追加実験を記述する。

## 再実行

```bash
python3 scripts/validate-manifest.py path/to/manifest.json
python3 scripts/run-matrix.py path/to/manifest.json --run-id NEW_RUN_ID --concurrency auto
```

## 証跡

- `results/<run-id>/run-manifest.json`
- `results/<run-id>/image-inspect.json`
- `results/<run-id>/summary.json`（権威あるcommit record）
- `results/<run-id>/report.<generation>.md`（`summary.json.reportArtifact`が参照する権威あるreport）
- `results/<run-id>/report.md`（convenience copy）
- `results/<run-id>/jobs/*/result.json`
- `results/<run-id>/jobs/*/attempts/*/stdout.log`
- `results/<run-id>/jobs/*/attempts/*/stderr.log`
- `results/<run-id>/jobs/*/attempts/*/evidence/`
- `results/<run-id>/jobs/*/stdout.log`（最終attemptの写し）
- `results/<run-id>/jobs/*/stderr.log`（最終attemptの写し）

## Sources

- https://github.com/apple/container
- `<検証対象の一次資料URL>`
