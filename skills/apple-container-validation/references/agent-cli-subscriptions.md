# Claude Code CLI / Codex CLIをサブスクリプションで使う

Claude Code CLIまたはCodex CLIを検証ケースから呼び出す場合だけ本ファイルを読む。認証操作はホスト上の信頼済み対話セッションで人間が完了する。ログイン、2FA、ブラウザ承認をエージェントが代行しない。API課金へ意図せず切り替わらないよう、APIキーを検証コンテナへ渡さない。

## 共通方針

1. `assets/agent-cli-Containerfile`を検証ワークスペースへコピーする。
2. CLIとTypeScript 7、`tsx`、`pino`の版を固定してイメージをビルドする。
3. 認証情報をContainerfile、イメージ、manifest、Git、stdout、stderr、成果物へ書かない。
4. サブスクリプション認証だけをcaseへ渡す。
5. 認証のpreflightを少数ケースで行ってから本行列を実行する。
6. CLI版、モデル、effort/reasoning、許可ツール、sandbox、プロンプト、出力schemaを来歴へ残す。
7. サブスクリプションのレート制限と利用規約を守る。大量並列を成功率改善の手段にしない。

```bash
container build --progress plain \
  -t validation-agent-cli:20260815 \
  -f agent-cli-Containerfile .
```

`agent-cli-Containerfile`の既定版は作成時点の固定値である。実行前に公式の変更履歴とローカルの`claude --version`、`codex --version`を確認し、版を変更した場合は別run-idを使う。

## Claude Code CLI

### サブスクリプション認証

Claude Pro、Max、Team、Enterpriseのサブスクリプションを使う非対話実行では、ホスト上で次を実行する。

```bash
claude setup-token
```

ブラウザで承認すると長期OAuthトークンが表示される。トークンは秘密管理された環境変数へ設定する。

```bash
export CLAUDE_CODE_OAUTH_TOKEN='...'
unset ANTHROPIC_API_KEY
```

`CLAUDE_CODE_OAUTH_TOKEN`だけをmanifestの`inheritEnv`へ指定する。

```json
{
  "agentCli": "claude-code-subscription",
  "inheritEnv": ["CLAUDE_CODE_OAUTH_TOKEN"],
  "command": [
    "claude",
    "-p",
    "Reply with exactly OK.",
    "--output-format",
    "json"
  ]
}
```

- `--bare`は使わない。Claude Codeの公式資料ではbare modeが`CLAUDE_CODE_OAUTH_TOKEN`を読まない。
- `ANTHROPIC_API_KEY`を渡さない。設定されているとAPIキー認証が優先される場合がある。
- `claude setup-token`のトークンは個人のサブスクリプションに結び付く。共有リポジトリへ保存しない。
- preflightでは`/status`または実行結果からsubscription loginであることを確認し、トークン値は記録しない。

## Codex CLI

Codex CLIはChatGPTサブスクリプションによるログインをサポートする。検証環境では、次の2方式を区別する。

### 方式A: `CODEX_ACCESS_TOKEN`

ChatGPTワークスペースでCodex access tokenを発行できる場合は、信頼済み自動化向けのこの方式を優先する。

```bash
export CODEX_ACCESS_TOKEN='...'
unset OPENAI_API_KEY CODEX_API_KEY
```

```json
{
  "agentCli": "codex-subscription",
  "inheritEnv": ["CODEX_ACCESS_TOKEN"],
  "command": [
    "codex",
    "exec",
    "--json",
    "Reply with exactly OK."
  ]
}
```

`CODEX_ACCESS_TOKEN`はAPIキーではなく、ChatGPTワークスペースの信頼済みローカル実行用資格情報である。利用可能性はワークスペース設定に依存する。

### 方式B: ChatGPTログインの`auth.json`

access tokenを発行できない個人またはワークスペースでは、ホスト上でChatGPTログインを完了する。

```bash
codex login
codex login status
```

ファイル保存を使う場合、ユーザー設定で次を指定する。

```toml
forced_login_method = "chatgpt"
cli_auth_credentials_store = "file"
```

`auth.json`はアクセストークンと更新トークンを含む秘密ファイルである。信頼済みの非公開環境だけで、run専用の秘密ディレクトリへ`0600`で配置する。

```bash
mkdir -p .validation-secrets/codex-home
chmod 700 .validation-secrets/codex-home
install -m 600 "${CODEX_HOME:-$HOME/.codex}/auth.json" \
  .validation-secrets/codex-home/auth.json
```

`.validation-secrets/`をGitとレポート成果物から除外する。manifestではrun専用ディレクトリをCodex homeへ書き込み可能でマウントする。

```json
{
  "defaults": {
    "allowWritableMounts": true,
    "maxConcurrency": 1
  },
  "mounts": [
    {
      "source": ".validation-secrets/codex-home",
      "target": "/home/agent/.codex",
      "readonly": false
    }
  ],
  "cases": [
    {
      "agentCli": "codex-subscription",
      "exclusiveGroup": "codex-auth-cache",
      "env": {"CODEX_HOME": "/home/agent/.codex"},
      "inheritEnv": [],
      "command": ["codex", "exec", "--json", "Reply with exactly OK."]
    }
  ]
}
```

- Codexは必要に応じて`auth.json`を更新するため、書き込み可能マウントを使う。
- 同じ`auth.json`を複数コンテナや複数マシンから同時使用しない。スキルは共有書き込みmountを検出すると並列度を1へ落とす。
- `auth.json`が実行中に更新されるため、この方式のrunを`--resume`しない。さらに、access token方式を含め`inheritEnv`を1件でも使うrunは、資格情報や設定値を来歴へ保存・比較しないため`--resume`できない。いずれも新しいrun-idで再実行する。
- 実行後に更新された`auth.json`を信頼済み保存先へ戻す必要がある場合は、人間が秘密として扱う。結果ディレクトリへコピーしない。
- `OPENAI_API_KEY`、`CODEX_API_KEY`を渡さない。

## 検証ケースの設計

CLI比較では最低限、次を固定する。

| 項目 | 例 |
|---|---|
| CLI | Claude Code / Codex |
| CLI版 | 完全なversion文字列 |
| 認証 | subscription OAuth / ChatGPT / workspace access token |
| モデル | 明示したモデル名 |
| 推論設定 | effort / reasoning level |
| ツール | 読み取り専用などの許可集合 |
| sandbox | read-only / workspace-write |
| prompt | 完全な文字列またはSHA-256 |
| schema | 構造化出力schemaのSHA-256 |
| repeat | 非決定性を測る反復数 |

Claude CodeとCodexの結果を比較する場合、同じ入力、同じオラクル、同等のツール権限、同等のsandboxを使う。片方だけネットワークや書き込みを許可しない。

## エラー処理

- subscription entitlementがない場合は`BLOCKED: subscription access unavailable`とする。
- Claude CodeでAPIキー認証が検出された場合は実行を止める。
- Codexで`codex login status`がChatGPTログインを示さない場合は実行を止める。
- 401、403、device-code無効、ブラウザcallback失敗は認証問題として記録し、対象実装の失敗へ数えない。
- 429またはusage limitはレート制限として記録する。結果を隠して再試行を増やさない。
- トークン、`auth.json`、認証ヘッダーがログへ出た場合は成果物を公開せず、資格情報を失効させる。

## 公式資料

- Claude Code authentication: https://docs.anthropic.com/en/docs/claude-code/iam
- Claude Code headless mode: https://docs.anthropic.com/en/docs/claude-code/headless
- Codex authentication: https://developers.openai.com/codex/auth
- Codex subscription auth in trusted automation: https://developers.openai.com/codex/auth/ci-cd-auth
- Codex CLI reference: https://developers.openai.com/codex/cli/reference
- Codex access tokens: https://developers.openai.com/codex/enterprise/access-tokens
