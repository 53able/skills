# Extension フックイベントと戻り値

このファイルは2つのフック層を扱う：

- **coding-agent ExtensionAPI**（Extensionファイル内の `pi.on(...)`）: `@earendil-works/pi-coding-agent` の `ExtensionAPI` が公開するイベント。Extension作成者が主に使うフックの入口。
- **AgentHarnessフック**（Node.jsアプリでの直接利用）: `@earendil-works/pi-agent-core` の低レベルイベント。ExtensionAPI層とイベントの形状が一部異なる。

`ExtensionAPI.on()` のイベントカタログは、モノリポの `packages/coding-agent/docs/extensions.md` が公式のリファレンス。

Extensionは `pi.on(eventType, handler)` でハンドラを登録する。

---

## イベントカタログ

### `session_start`

セッションライフサイクルの各開始時点（起動・新規セッション・再開・フォーク・リロード）で発火する。Extension状態の初期化やセッションエントリからの状態復元に使う。

```typescript
pi.on("session_start", async (event, ctx) => {
  // event.reason: "startup" | "reload" | "new" | "resume" | "fork"
  // event.previousSessionFile: "new", "resume", "fork" 時に存在する
  ctx.ui.notify(`セッション開始: ${event.reason}`, "info");

  // カスタムセッションエントリから状態を復元する:
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry.type === "custom" && entry.customType === "my-state") {
      // entry.data から状態を再構築する
    }
  }
});
```

### `session_shutdown`

Extensionランタイムが破棄される前に発火する（終了・リロード・新規セッション・再開・フォーク）。クリーンアップやカスタムセッションエントリへの状態保存に使う。

```typescript
pi.on("session_shutdown", async (event, ctx) => {
  // event.reason: "quit" | "reload" | "new" | "resume" | "fork"
  // event.targetSessionFile: セッション切り替えフローの遷移先セッションファイル
  // カスタムセッションエントリとして状態を保存する:
  await ctx.sessionManager.appendCustomEntry("my-state", { myData: "..." });
});
```

### `resources_discover`

`session_start` の後に発火する。Extensionはスキル・プロンプト・テーマのディレクトリパスを返し、リソース探索パイプラインに追加できる。

```typescript
pi.on("resources_discover", async (event, _ctx) => {
  // event.reason: "startup" | "reload"
  // event.cwd: カレントワーキングディレクトリ
  return {
    skillPaths: ["/path/to/extra/skills"],
    promptPaths: ["/path/to/extra/prompts"],
    themePaths: ["/path/to/extra/themes"],
  };
});
```

**起動時のライフサイクル順:**
```
factory() 呼び出し → session_start { reason: "startup" } → resources_discover { reason: "startup" }
```

**セッション切り替え時（/new, /resume, /fork）:**
```
session_shutdown → session_start { reason: "new" | "resume" | "fork" } → resources_discover
```

---

### `before_agent_start`

各エージェント実行の開始前に発火する。メッセージの注入やシステムプロンプトの変更が可能。

```typescript
pi.on("before_agent_start", async (event, ctx) => {
  // event.prompt（プロンプトテキスト）, event.images（画像）,
  // event.systemPrompt（現在のシステムプロンプト）, event.resources（リソース）
  return {
    messages?: AgentMessage[],  // コンテキストの先頭に追加される
    systemPrompt?: string,       // 現在のプロンプトを置き換える（ハンドラはチェーンされる）
  };
});
```

### `context`

各LLMプロバイダ呼び出しの前に発火する。メッセージ配列の変換が可能。

```typescript
pi.on("context", async (event, ctx) => {
  // event.messages（現在のメッセージ配列）
  return {
    messages: pruneOldMessages(event.messages),
  };
});
```

### `before_provider_request`

HTTPリクエスト構築前に発火する。ストリームオプションにパッチを当てられる。

```typescript
pi.on("before_provider_request", async (event, ctx) => {
  // event.model（使用モデル）, event.sessionId, event.streamOptions
  return {
    streamOptions?: AgentHarnessStreamOptionsPatch,
    // パッチ: headers/metadata の値を undefined にするとそのキーが削除される
  };
});
```

### `before_provider_payload`

リクエストボディのシリアライズ直前に発火する。生のペイロードを変換できる。

```typescript
pi.on("before_provider_payload", async (event, ctx) => {
  // event.model, event.payload（生のプロバイダリクエストオブジェクト）
  return {
    payload: modifiedPayload,
  };
});
```

### `after_provider_response`

観測専用。レスポンスヘッダーの受信後に発火する。

```typescript
pi.on("after_provider_response", async (event, ctx) => {
  // event.status（HTTPステータス）, event.headers（レスポンスヘッダー）
  // 戻り値は無視される
});
```

### `tool_call`

ツール実行前に発火する。実行をブロックできる。

```typescript
pi.on("tool_call", async (event, ctx) => {
  // event.toolCallId, event.toolName, event.input
  if (event.toolName === "bash" && !approvedBashCommand(event.input.command)) {
    return { block: true, reason: "このコマンドは承認されていません" };
  }
});
```

**動作**: 順次実行。最初に `{ block: true }` を返したハンドラが実行を停止させる。

### `tool_result`

ツール実行後に発火する。結果にパッチを当てられる。

```typescript
pi.on("tool_result", async (event, ctx) => {
  // event.toolCallId, event.toolName, event.input,
  // event.content（結果コンテンツ）, event.details, event.isError
  return {
    content?: Array<TextContent | ImageContent>,
    details?: unknown,
    isError?: boolean,
    // terminate?: boolean — AgentHarness 直接利用時に使用可能;
    // ExtensionAPI での利用可否は packages/coding-agent/docs/extensions.md を確認すること
  };
});
```

**動作**: 順次パッチ蓄積 — 各ハンドラは前のハンドラのパッチ済み結果を受け取る。

### `session_before_compact`

コンパクション前に発火する。キャンセルまたはカスタム要約の提供が可能。

```typescript
pi.on("session_before_compact", async (event, ctx) => {
  // event.preparation（firstKeptEntryId, messagesToSummarize, tokensBefore など）
  // event.branchEntries, event.customInstructions, event.signal
  return {
    cancel?: boolean,
    compaction?: {
      summary: string,
      firstKeptEntryId: string,
      tokensBefore: number,
      details?: unknown,
    },
  };
});
```

### `session_before_tree`

ツリーナビゲーション前に発火する。キャンセルまたはブランチ要約の提供が可能。

```typescript
pi.on("session_before_tree", async (event, ctx) => {
  // event.preparation（targetId, entriesToSummarize, userWantsSummary など）
  return {
    cancel?: boolean,
    summary?: { summary: string; details?: unknown },
    customInstructions?: string,
    replaceInstructions?: boolean,
    label?: string,
  };
});
```

### 観測イベント（戻り値は無視される）

| イベント | ペイロード |
|---------|-----------|
| `session_compact` | `{ compactionEntry, fromHook }` |
| `session_tree` | `{ newLeafId, oldLeafId, summaryEntry, fromHook }` |
| `model_select` | `{ model, previousModel, source }` |
| `thinking_level_select` | `{ level, previousLevel }` |
| `resources_update` | `{ resources, previousResources }` |
| `queue_update` | `{ steer, followUp, nextTurn }` |
| `save_point` | `{ hadPendingMutations }` |
| `abort` | `{ clearedSteer, clearedFollowUp }` |
| `settled` | `{ nextTurnCount }` |

---

## Extension登録ヘルパー（coding-agent専用）

`ExtensionAPI`（`pi.`）はさらに以下を公開している：

```typescript
pi.registerTool(tool: AgentTool)
pi.registerCommand(name, { description, handler })
pi.registerShortcut(keyCombo, handler)
pi.registerProvider(providerDef)     // カスタムLLMプロバイダ
// UI登録（バージョンにより異なる — docs/extensions.md を確認すること）
```

---

## Extensionのエラーポリシー

スローしたExtensionは捕捉され、TUIヘッダーにエラーが報告され、スキップされる。ハーネスはそのExtensionの結果なしで処理を継続する。

`AgentHarness` を直接利用してカスタムフックを構築する場合（coding-agent外）、必要に応じて `errorMode` ストラテジーを指定する：
- デフォルト: `"continue"`（ログに記録して失敗したハンドラをスキップ）
- `"throw"`: 厳格なテスト環境向け
