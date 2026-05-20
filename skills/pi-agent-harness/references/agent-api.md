# Agent / AgentHarness API リファレンス

ソース: https://github.com/earendil-works/pi/tree/main/packages/agent

---

## Agentクラス（`@earendil-works/pi-agent-core`）

### コンストラクタ

```typescript
new Agent({
  initialState: {
    systemPrompt: string,
    model: Model<any>,                    // @earendil-works/pi-ai の getModel() で取得
    thinkingLevel?: ThinkingLevel,        // "off"|"minimal"|"low"|"medium"|"high"|"xhigh"
    tools?: AgentTool<any>[],
    messages?: AgentMessage[],
  },
  convertToLlm?: (messages: AgentMessage[]) => Message[],
  transformContext?: (messages: AgentMessage[], signal: AbortSignal) => Promise<AgentMessage[]>,
  steeringMode?: "one-at-a-time" | "all",
  followUpMode?: "one-at-a-time" | "all",
  streamFn?: CustomStreamFn,             // プロキシバックエンド向け
  sessionId?: string,
  getApiKey?: (provider: string) => Promise<string>,
  toolExecution?: "parallel" | "sequential",
  beforeToolCall?: (opts) => Promise<{ block?: boolean; reason?: string } | undefined>,
  afterToolCall?: (opts) => Promise<{ terminate?: boolean; details?: unknown } | undefined>,
  thinkingBudgets?: { minimal?: number; low?: number; medium?: number; high?: number },
})
```

### 状態

```typescript
agent.state.systemPrompt = "新しいプロンプト";
agent.state.model = getModel("openai", "gpt-4o");
agent.state.thinkingLevel = "medium";
agent.state.tools = [myTool];
agent.state.messages = newMessages;       // トップレベルの配列は保存前にコピーされる
agent.state.isStreaming                   // 読み取り専用 boolean
agent.state.streamingMessage             // ストリーミング中の部分的なアシスタントメッセージ
agent.state.pendingToolCalls             // ReadonlySet<string>
agent.state.errorMessage                 // 直近のエラー文字列
```

### メソッド

```typescript
await agent.prompt("text", images?)         // テキストプロンプト
await agent.prompt({ role: "user", ... })   // AgentMessage を直接渡す
await agent.continue()                      // 既存コンテキストから再開する
agent.abort()
await agent.waitForIdle()
agent.steer(message)                        // 実行中にステアリングメッセージを注入する
agent.followUp(message)                     // フォローアップをキューに追加する
agent.clearSteeringQueue()
agent.clearFollowUpQueue()
agent.clearAllQueues()
agent.reset()
const unsubscribe = agent.subscribe(handler)
```

### イベントシーケンス（prompt）

```
agent_start
turn_start
message_start / message_update... / message_end   （ユーザーメッセージ）
message_start / message_update... / message_end   （アシスタント）
tool_execution_start → tool_execution_update* → tool_execution_end
message_start / message_end   （toolResult）
turn_end
[ステアリング/フォローアップ → turn_start ... turn_end]*
agent_end
```

### ツール定義

```typescript
const tool: AgentTool = {
  name: "tool_name",
  label: "表示名",                 // UI表示専用
  description: "使用する条件",
  parameters: Type.Object({ ... }), // TypeBox スキーマ
  executionMode?: "parallel" | "sequential",
  execute: async (toolCallId, params, signal, onUpdate) => {
    // onUpdate で部分的な結果をストリーミングできる
    return {
      content: [{ type: "text", text: "結果" }],
      details: {},
      // terminate?: true   （このバッチ後にエージェントを停止する）
    };
  },
};
```

**失敗時は例外をスローする。** エラーメッセージをコンテンツとして返してはいけない。

### カスタムメッセージ型（declaration merging）

```typescript
declare module "@earendil-works/pi-agent-core" {
  interface CustomAgentMessages {
    notification: { role: "notification"; text: string; timestamp: number };
  }
}
```

### 低レベルループ

```typescript
import { agentLoop, agentLoopContinue } from "@earendil-works/pi-agent-core";

for await (const event of agentLoop([userMessage], context, config)) {
  // 観測のみ — 非同期ハンドラの完了を待たない
}
```

ツールのプリフライト前にイベント処理をバリアとして機能させたい場合は `Agent` クラスを使う。

---

## AgentHarness（`@earendil-works/pi-agent-core`）

### コンストラクタオプション

```typescript
new AgentHarness({
  env: ExecutionEnv,            // Node.js では NodeExecutionEnv
  session: Session,             // SessionRepo.create() / open() で取得
  tools?: AgentTool[],
  resources?: {
    skills?: Skill[],
    promptTemplates?: PromptTemplate[],
  },
  systemPrompt?: string | ((ctx) => string | Promise<string>),
  getApiKeyAndHeaders?: (model) => Promise<{ apiKey: string; headers?: Record<string,string> }>,
  streamOptions?: AgentHarnessStreamOptions,
  model: Model<any>,
  thinkingLevel?: ThinkingLevel,
  activeToolNames?: string[],
  steeringMode?: QueueMode,
  followUpMode?: QueueMode,
})
```

### フェーズ

```typescript
type AgentHarnessPhase = "idle" | "turn" | "compaction" | "branch_summary" | "retry";
```

構造的操作は `phase === "idle"` を必要とする: `prompt`, `skill`, `promptFromTemplate`, `compact`, `navigateTree`。
ビジー状態で呼び出すと `AgentHarnessError { code: "busy" }` がスローされる。

### 構造的操作（idle必須）

```typescript
await harness.prompt("text", options?)
await harness.skill(skillName, args?)
await harness.promptFromTemplate(templateName, args?)
await harness.compact(options?)
await harness.navigateTree(targetId, options?)
```

### ターン中の操作

```typescript
await harness.steer("text", options?: { images?: ImageContent[] })
await harness.followUp("text", options?: { images?: ImageContent[] })
await harness.nextTurn("text", options?: { images?: ImageContent[] })   // 次のユーザーメッセージの前に挿入される
harness.abort()
```

### ランタイム設定setter（次のセーブポイントで反映）

```typescript
await harness.setModel(model)
await harness.setThinkingLevel(level)
await harness.setTools(tools, activeToolNames?)
await harness.setActiveTools(toolNames)
await harness.setResources(resources)
await harness.setStreamOptions(options)
```

### getter（インフライトのスナップショットではなく最新の設定を返す）

```typescript
harness.getModel()
harness.getThinkingLevel()
harness.getResources()
harness.getStreamOptions()
harness.getSteeringMode() / await harness.setSteeringMode(mode)
harness.getFollowUpMode() / await harness.setFollowUpMode(mode)
```

### ハーネスイベント

ハーネスリスナーに配信される全イベント：

| イベント型 | タイミング | チャネル |
|-----------|-----------|----------|
| `before_agent_start` | 各エージェント実行の開始前 | `on()` |
| `context` | LLMターン前（メッセージの注入・変換が可能） | `on()` |
| `before_provider_request` | プロバイダHTTPリクエスト送信前 | `on()` |
| `before_provider_payload` | リクエストボディ送信前 | `on()` |
| `after_provider_response` | レスポンスヘッダー受信後 | `on()` |
| `tool_call` | ツール実行前（ブロック可能） | `on()` |
| `tool_result` | ツール結果取得後（content/isError にパッチ可能） | `on()` |
| `session_before_compact` | コンパクション前（キャンセルまたは要約の提供が可能） | `on()` |
| `session_compact` | コンパクションエントリ書き込み後 | `subscribe()` |
| `session_before_tree` | ツリーナビゲーション前（キャンセル可能） | `on()` |
| `session_tree` | リーフ変更後 | `subscribe()` |
| `model_select` | モデル変更時 | `subscribe()` |
| `thinking_level_select` | 思考レベル変更時 | `subscribe()` |
| `resources_update` | setResources() によるリソース変更時 | `subscribe()` |
| `queue_update` | ステアリング/フォローアップ/nextTurnキュー変更時 | `subscribe()` |
| `save_point` | ターン＋ツール完了後・次のスナップショット前 | `subscribe()` |
| `abort` | abort() 呼び出し時 | `subscribe()` |
| `settled` | 実行完全終了時 | `subscribe()` |

低レベルの `AgentEvent` 型もすべて `subscribe()` 経由で配信される: `agent_start`, `agent_end`, `turn_start`, `turn_end`, `message_start`, `message_update`, `message_end`, `tool_execution_start`, `tool_execution_update`, `tool_execution_end`。

### ハーネスイベントの購読

購読方法は2種類あり、それぞれセマンティクスが異なる：

**`harness.subscribe(listener)`** — 全ての観測イベント（エージェントループのライフサイクルイベントおよびフック不要なハーネスイベント）を受け取る。モニタリングやロギングに使う。

```typescript
const unsubscribe = harness.subscribe(async (event) => {
  // 受け取るイベント: agent_start, turn_start, message_start, message_update,
  //   message_end, turn_end, tool_execution_start/update/end,
  //   agent_end, save_point, settled, queue_update, model_select,
  //   thinking_level_select, resources_update, session_compact,
  //   session_tree, abort
  if (event.type === "turn_end") {
    console.log("ターン完了:", event.message.role);
  }
  if (event.type === "settled") {
    await flushState();
  }
});
unsubscribe(); // リスナーを解除する
```

**`harness.on(type, handler)`** — 特定のイベント型に対して結果を返すフックハンドラを登録する。ツール呼び出しのブロック・結果のパッチ・コンテキストの変換に使う。戻り値がハーネスの動作に影響する。

```typescript
// ツール呼び出しをブロックする
const unsubscribe = harness.on("tool_call", async (event) => {
  // event.toolCallId, event.toolName, event.input
  if (event.toolName === "bash") {
    return { block: true, reason: "bash は許可されていません" };
  }
});

// ツール結果にパッチを当てる
harness.on("tool_result", async (event) => {
  // { content, details, isError } を返してパッチを当てる
});

// 各LLM呼び出し前にコンテキストを変換する
harness.on("context", async (event) => {
  return { messages: event.messages.slice(-20) }; // 直近20件のみ保持
});

// エージェント実行開始前に処理する
harness.on("before_agent_start", async (event) => {
  return { systemPrompt: event.systemPrompt + "\n追加指示。" };
});
```

`on()` ハンドラは登録順に実行される。`tool_call` では最初に `{ block: true }` を返したハンドラが実行を停止させる。`tool_result` ではハンドラが順番にパッチを蓄積する。

---

## セッションストレージ

```typescript
import { JsonlSessionRepo } from "@earendil-works/pi-agent-core/node";
import { NodeExecutionEnv } from "@earendil-works/pi-agent-core/node";
import * as path from "node:path";

const env = new NodeExecutionEnv(process.cwd());
const sessionsRoot = path.join(process.env.HOME ?? "~", ".pi", "agent", "sessions");
const repo = new JsonlSessionRepo({ fs: env, sessionsRoot });

// 新しいセッションを作成する
const session = await repo.create({ cwd: process.cwd() });
// または既存のセッションを一覧・オープンする
const sessions = await repo.list({ cwd: process.cwd() });
const session2 = await repo.open(sessions[0]);
```

> **注意:** `JsonlSessionRepoFileSystem` は `Pick<FileSystem, ...>` のスライス型。`NodeExecutionEnv` はこれを満たす。カスタムファイルシステムを使う場合は `packages/agent/src/harness/session/jsonl-repo.ts` で正確なpickフィールドを確認すること。

セッションエントリのJSONL型: `message`, `thinking_level_change`, `model_change`, `compaction`, `branch_summary`, `custom`, `custom_message`, `label`, `leaf`。

---

## AgentHarnessStreamOptions

```typescript
{
  transport?: "sse" | "websocket" | "auto",
  timeoutMs?: number,
  maxRetries?: number,
  maxRetryDelayMs?: number,
  headers?: Record<string, string>,
  metadata?: Record<string, unknown>,
  cacheRetention?: "default" | "long",
}
```
