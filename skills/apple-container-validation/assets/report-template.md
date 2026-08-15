# Apple Container検証レポート: <主張>

## ステータス

- Claim outcome: `<Supported within tested scope / Falsified / Unverified>`
- Execution status: `<Complete / Incomplete / Blocked>`
- Run ID: `<run-id>`
- 検証日: `<ISO 8601>`

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
| Parallelism | `<workers>` |
| Agent CLI | `<none / Claude Code / Codex>` |
| CLI version | `<full version>` |
| Authentication | `<none / subscription OAuth / ChatGPT / workspace access token>` |
| Model / reasoning | `<model and effort/reasoning setting>` |

## ケース行列とオラクル

| Case | Group | Relation | Purpose | Oracle | Repeats |
|---|---|---|---|---|---:|
| `<id>` | `<target/boundary/negative/failure>` | `<support/falsify/neutral>` | `<目的>` | `<判定条件>` | 1 |

## 観察結果

観察事実だけを記述する。各数値または判定を `summary.json`、`result.json`、ログ、生成物のいずれかへ結び付ける。

| Case | Status | Observation | Evidence |
|---|---|---|---|
| `<id>` | `<oracle-pass/oracle-fail/timeout>` | `<観察>` | `<relative path>` |

## 推論

観察から導ける範囲を記述する。観察と同じ節へ混ぜない。

## 反証と不一致

仮説に反する結果、期待外れのケース、説明できないばらつきを残す。都合の悪い反復を削除しない。

## 限界と未検証事項

- `<対象外のOS、アーキテクチャ、バージョン>`
- `<測定誤差、並列干渉、外部依存>`
- `<Not run / Blocked / Unverified>`

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
- `results/<run-id>/summary.json`
- `results/<run-id>/jobs/*/result.json`
- `results/<run-id>/jobs/*/stdout.log`
- `results/<run-id>/jobs/*/stderr.log`

## Sources

- https://github.com/apple/container
- `<検証対象の一次資料URL>`
