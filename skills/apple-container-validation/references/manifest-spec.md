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
  "context": ".",
  "file": "Containerfile",
  "pull": false
}
```

`context` と `file` はマニフェストの親ディレクトリからの相対パスにする。再現性を優先し、ベースイメージと依存バージョンを固定する。

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

- `relation`: オラクル成立時に仮説を `support`、`falsify`、または `neutral` のどれへ動かすかを指定する。`falsify` は `criterionIds` を必須にする。
- `agentCli`: CLIを使う場合だけ`claude-code-subscription`または`codex-subscription`を指定する。認証方式と安全条件は`references/agent-cli-subscriptions.md`に従う。
- `criterionIds`: 検証する棄却条件IDを指定する。
- `exclusiveGroup`: 同じ共有資源を使うケースへ同じ値を付け、その群だけ直列化する。
- `command`: argv配列にする。パイプ、リダイレクト、複合コマンドが必要な場合だけ `sh -lc` を明示する。
- `env`: 公開可能な固定値だけを置く。
- `inheritEnv`: ホストから渡す環境変数名だけを置く。値はマニフェストへ書かない。Claude Code subscriptionでは`CLAUDE_CODE_OAUTH_TOKEN`、Codex workspace access tokenでは`CODEX_ACCESS_TOKEN`だけを許可する。APIキーは渡さない。
- `oracle`: 最低1項目を定義する。既定の期待終了コードは0。
- `artifacts.path`: `/evidence` からの相対パスにする。絶対パスと `..` は禁止する。

## 証跡

ランナーは次を保存する。

```text
results/<run-id>/
  image-build.log
  image-inspect.json
  run-manifest.json
  summary.json
  report.md
  jobs/<case-id>-r<repeat>/
    result.json
    stdout.log
    stderr.log
    evidence/
```

`run-manifest.json` はマニフェスト、解決済みイメージ、build context、Containerfile、mount入力、skill bundle、ジョブ集合、並列度、Apple Containerバージョン、ホストのSHA-256または値を固定する。`--resume` はこの来歴とattempt別ログ・artifact hashが一致する場合だけ許可する。
