# コーディングエージェントのadapter

選択したWorkerのsectionだけを読む。すべてのflagをversion依存として扱い、実行前に完全なCLI versionを記録してinstalled CLIのhelpを確認する。

## Claude Code

npm package `@anthropic-ai/claude-code`の完全なversionを使う。non-interactiveなbare modeを使い、project／user hook、skill、command、subagent、plugin、MCP server、auto memory、`CLAUDE.md`の自動検出を止める。

```bash
claude --version
claude --help
claude --bare -p \
  --output-format stream-json \
  --allowedTools 'Read,Edit,Bash' \
  '変更不能なtask contractに従い、private workspaceだけを編集する。Git remoteを使わない。'
```

現行のClaude文書では、`--bare`はOAuth credentialとsystem Keychainを読まず、明示的なprovider認証を必要とする。長命keyを未信頼codeへ公開せず、短命なgateway経路を使う。`--add-dir`はskillを読み込める部分的な例外であるため、未信頼repositoryでは使わない。

`--dangerously-skip-permissions`は、Claude process全体がVM内でnon-root実行され、外側のmount、credential、network制約を確認した場合に限り検討する。built-in Bash sandboxだけではfile tool、MCP server、hookを隔離できない。

## Codex CLI

npm package `@openai/codex`の完全なversionを使う。non-interactive実行、ephemeral session、明示的なsandbox、user設定／rulesの無視、JSONL eventを指定する。

```bash
codex --version
codex exec --help
codex exec \
  --ephemeral \
  --sandbox workspace-write \
  --ignore-user-config \
  --ignore-rules \
  --json \
  '変更不能なtask contractに従い、private workspaceだけを編集する。Git remoteを使わない。'
```

`danger-full-access`は、nested sandboxが互換性を持たない理由を記録し、外側のVM制御を確認した場合に限り使う。現行のOpenAI文書は、repository管理下のcodeが読めるjob-level環境変数へ`OPENAI_API_KEY`や`CODEX_API_KEY`を置かないよう警告している。workload identityまたは短命なproxy／gateway経路を優先する。

configとrulesを無視してもrepository codeは安全にならない。`AGENTS.md`、`.codex/`、MCP設定、build script、test script、dependency lifecycle hookをactive inputとして検査する。

## Pi

npm package `@earendil-works/pi-coding-agent`の完全なversionを使う。project trust、context file、extension、skill、prompt template、persistent sessionを無効にする。Piにはbuilt-in sandboxがないため、Pi process全体をApple Container内で実行する。

```bash
pi --version
pi --help
pi -p \
  --mode json \
  --no-session \
  --no-approve \
  --no-extensions \
  --no-skills \
  --no-prompt-templates \
  --no-context-files \
  --tools read,write,edit,bash \
  '変更不能なtask contractに従い、private workspaceだけを編集する。Git remoteを使わない。'
```

hostの`~/.pi/agent`をmountしない。operator所有のextensionを使う場合もimage内でversion固定し、project-local extensionは無効のままにする。patch hashとtest結果をPiの外で再計算する。

## その他のagent

adapterを追加する前に、次をすべて満たす。

1. project／userのautoload pathをすべて特定し、無効化する。
2. machine-readableなnon-interactive modeを選ぶ。
3. taskが必要としない限りpersistent sessionを無効化する。
4. agent process全体をVM内に置く。
5. 完全なversionとeffective settingsを記録する。
6. host home、credential、remote、read-write working tree mountが存在しないことを示す。
7. autoload、network、persistence、path scope、log forgery、resource limitのnegative testを追加する。
