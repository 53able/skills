---
name: pi-agent-harness
description: Pi Agent Harness モノリポ（earendil-works/pi）の開発・設定・拡張を支援する。コーディングエージェントCLI、AgentHarnessセッションライフサイクル、スキル・Extension・プロンプトテンプレートの作成、マルチプロバイダLLM設定、セッションツリーナビゲーション、コンパクション、フック、SDK組み込み、Piパッケージ作成をカバーする。piの開発・拡張、TypeScript Extensionの作成、カスタムツール登録、セッション管理、アプリケーションへのSDK組み込みを行う際に使用する。pi以外のNode.jsプロジェクト、非piのLLMフレームワーク、MCPサーバー設定には使用しない。
---

# Pi Agent Harness

## リポジトリ概要

**GitHub**: https://github.com/earendil-works/pi  
**ウェブサイト**: https://pi.dev | **ドキュメント**: https://pi.dev/docs/latest

| パッケージ | ディレクトリ | 役割 |
|-----------|------------|------|
| `@earendil-works/pi-coding-agent` | `packages/coding-agent` | インタラクティブなコーディングエージェントCLI |
| `@earendil-works/pi-agent-core` | `packages/agent` | エージェントランタイム（ツール実行・セッション・ハーネス） |
| `@earendil-works/pi-ai` | `packages/ai` | 統合マルチプロバイダLLM API |
| `@earendil-works/pi-tui` | `packages/tui` | ターミナルUIライブラリ |

全パッケージはロックステップバージョニングを採用。ソースからビルドする場合：

```bash
npm install
npm run build
npm run check   # リント・型チェック（コード変更後は必ず実行。テストは実行しない）
./pi-test.sh    # ソースからpiを実行（任意のディレクトリから）
```

---

## APIの選び方

| ユースケース | 使用するAPI |
|------------|------------|
| 手軽なプログラム利用・最小セットアップ | `@earendil-works/pi-coding-agent` の `createAgentSession` |
| イベントループの完全制御・カスタム状態管理 | `@earendil-works/pi-agent-core` の `Agent` クラス |
| 永続セッション・ツリーナビゲーション・Extensionフック | `@earendil-works/pi-agent-core` の `AgentHarness` |
| 観測のみのストリーミング（非同期バリア不要） | `@earendil-works/pi-agent-core` の `agentLoop` / `agentLoopContinue` |

`createAgentSession`（ステップ3）が最も手軽なエントリーポイント。`AgentHarness`（ステップ4）は永続JSONLセッション・ブランチング・コンパクション・フックシステムが必要なアプリ向け。`Agent`クラスはその中間に位置し、セッション永続化のオーバーヘッドなしにフルイベント制御が得られる。

---

## ステップ1: インストールと認証

**グローバルインストール（npm）：**
```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

**認証 — サブスクリプション（Claude/ChatGPT/Copilot）：**
```bash
pi          # 起動後に /login と入力
```

**認証 — APIキー：**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
pi
```

モデル選択・セッションオプション・ツール制限など詳細なフラグは `references/cli-reference.md` を参照。

---

## ステップ2: コーディングエージェント インタラクティブモード

プロジェクトディレクトリで `pi` を起動する。主なコマンド：

| コマンド | 説明 |
|---------|------|
| `/model` または Ctrl+L | モデルを切り替える |
| `/tree` または Esc×2 | セッションブランチツリーをナビゲートする |
| `/fork` | 過去のユーザーメッセージから新しいセッションを作成する |
| `/compact [指示]` | コンテキストを手動でコンパクションする |
| `/resume` または `pi -r` | 過去のセッションを再開する |
| `/settings` | 思考レベル・トランスポート・コンパクション設定を変更する |
| `/skill:name` | スキルを明示的に呼び出す |
| `/name <名前>` | 現在のセッションに名前をつける |

**非インタラクティブ（プリントモード）：**
```bash
pi -p "コードベースを要約して"
cat README.md | pi -p "このテキストを要約して"
```

**エージェント実行中のメッセージ送信：**
- Enter → ステアリングメッセージ（現在のツールバッチ終了後に配信）
- Alt+Enter → フォローアップ（エージェントが完全に停止した後に配信）
- Escape → 中断してキューのテキストをエディタに戻す

---

## ステップ3: SDK プログラム利用

`@earendil-works/pi-coding-agent` からインポートするとバッテリー同梱のSDKが使える。`@earendil-works/pi-agent-core` からインポートするとより軽量なランタイムが使える。

**SDKの最小例：**
```typescript
import { AuthStorage, createAgentSession, ModelRegistry, SessionManager } from "@earendil-works/pi-coding-agent";

const authStorage = AuthStorage.create();
const modelRegistry = ModelRegistry.create(authStorage);
const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  authStorage,
  modelRegistry,
});

await session.prompt("カレントディレクトリのファイルを列挙して。");
```

**低レベルのAgentクラス（pi-agent-core）：**
```typescript
import { Agent } from "@earendil-works/pi-agent-core";
import { getModel } from "@earendil-works/pi-ai";

const agent = new Agent({
  initialState: {
    systemPrompt: "あなたは親切なアシスタントです。",
    model: getModel("anthropic", "claude-sonnet-4-20250514"),
  },
});

agent.subscribe((event) => {
  if (event.type === "message_update" && event.assistantMessageEvent.type === "text_delta") {
    process.stdout.write(event.assistantMessageEvent.delta);
  }
});

await agent.prompt("こんにちは！");
```

`Agent`クラスの全コンストラクタオプション・状態フィールド・イベントシーケンス・カスタムツール・ステアリング/フォローアップAPIは `references/agent-api.md` を参照。

---

## ステップ4: AgentHarness（セッション対応ランタイム）

`AgentHarness` は低レベルのエージェントループをセッション永続化・リソース管理・操作ロック・フック/イベントシステムでラップしたもの。永続セッション・ツリーナビゲーション・Extensionフックが必要なアプリケーションで使用する。

**主要な概念：**
- **フェーズ**: `idle | turn | compaction | branch_summary | retry`。構造的な操作（`prompt`・`compact`・`navigateTree`）は `idle` 状態を必要とし、フェーズをアトミックに設定する。
- **ターンスナップショット**: 各ターン開始時点のモデル・ツール・リソース・ストリームオプションの不変なキャプチャ。ターン中に行われた設定変更は次のセーブポイントで反映される。
- **セーブポイント**: アシスタントのターン＋ツール結果が完了した後に発生。保留中のセッション書き込みをフラッシュし、次のプロバイダリクエスト用に設定変更を適用する。
- **保留中のセッション書き込み**: ビジー状態中にExtensionやフックがキューに入れた書き込み。セーブポイントで決定論的な順序でフラッシュされる。

**ターン中に許可される操作：**
- `steer()`・`followUp()`・`nextTurn()`
- `abort()`
- 全ランタイム設定setter（`setModel`・`setThinkingLevel`・`setTools`・`setResources`・`setStreamOptions`）

`AgentHarnessOptions`インターフェースとイベント/結果型の全一覧は `references/agent-api.md` を参照。

---

## ステップ5: カスタムツール

TypeBoxスキーマを使って `AgentTool` でツールを定義する：

```typescript
import { Type } from "typebox";
import type { AgentTool } from "@earendil-works/pi-agent-core";

const greetTool: AgentTool = {
  name: "greet",
  description: "名前を指定してユーザーに挨拶する。",
  parameters: Type.Object({
    name: Type.String({ description: "挨拶する名前" }),
  }),
  execute: async (toolCallId, params, signal) => {
    return {
      content: [{ type: "text", text: `こんにちは、${params.name}！` }],
      details: {},
    };
  },
};

agent.state.tools = [greetTool];
```

**ツールのエラー処理：** ツールが失敗した場合はエラーテキストを返すのではなく例外をスローする。エージェントはスローされたエラーを捕捉し、`isError: true` としてモデルに報告する。

**terminateヒント：** `execute()` から `{ ..., terminate: true }` を返すと、現在のツールバッチ後にエージェントを停止するよう示唆できる（バッチ内の全ツール結果が `terminate: true` を返す場合のみ有効）。

---

## ステップ6: Extension 作成

Extensionファイルの配置場所：
- `~/.pi/agent/extensions/`（グローバル）
- `.pi/extensions/`（プロジェクトローカル）
- Piパッケージ内

piはTypeScriptファイル（`.ts`）を直接読み込む。コンパイル済みの `.js` は不要。

```typescript
import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // カスタムツールを登録する
  pi.registerTool({
    name: "deploy",
    description: "現在のブランチをデプロイする。",
    parameters: Type.Object({ env: Type.String() }),
    execute: async (id, params, signal) => { /* ... */ },
  });

  // スラッシュコマンドを登録する
  pi.registerCommand("stats", {
    description: "プロジェクト統計を表示する",
    handler: async (args, ctx) => { /* ... */ },
  });

  // ツール呼び出しに反応する
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "bash") {
      // ブロックする場合: return { block: true, reason: "..." }
    }
  });

  // ツール結果にパッチを当てる
  pi.on("tool_result", async (event, ctx) => {
    // return { content: [...], isError: false }
  });
}
```

デフォルトエクスポートは `async` にもできる。piは非同期Extensionファクトリーを起動前に待機する。フックイベントの全一覧は `references/extension-events.md` を参照。

`assets/extension-template.ts` で完全なアノテーション付きExtension雛形を確認できる。

---

## ステップ7: スキル作成

スキルは [agentskills.io](https://agentskills.io) 仕様に従ったMarkdownファイル。配置場所：
- `~/.pi/agent/skills/<スキル名>/SKILL.md`（グローバル）
- `~/.agents/skills/<スキル名>/SKILL.md`
- `.pi/skills/<スキル名>/SKILL.md`（プロジェクト）
- `.agents/skills/<スキル名>/SKILL.md`

`/skill:name` で明示的に呼び出すか、モデルが自動的に発見する。`description` フィールドはモデルがスキルをいつ使うか判断するための主なシグナルになるため、起動条件を具体的に書くことが重要。

**最小スキル例：**
```markdown
---
name: deploy-app
description: アプリケーションを本番環境にデプロイする。デプロイまたはリリースの依頼時に使用する。
---
# アプリのデプロイ
1. `npm run build` を実行して出力を確認する。
2. `./scripts/deploy.sh` をターゲット環境を第1引数として実行する。
3. デプロイURLにアクセスできることを確認する。
```

---

## ステップ8: プロンプトテンプレート

プロンプトテンプレートは `{{プレースホルダー}}` 構文を持つMarkdownファイル。`~/.pi/agent/prompts/` または `.pi/prompts/` に配置する。エディタで `/テンプレート名` と入力して展開する。

```markdown
<!-- ~/.pi/agent/prompts/review.md -->
以下のコードをバグとセキュリティの観点でレビューして。
重点領域: {{focus}}
```

---

## ステップ9: Piパッケージ作成

スキル・Extension・プロンプト・テーマをnpmやgit経由で配布するためにバンドルする。

**パッケージの作成** — `package.json` に追記：
```json
{
  "name": "my-pi-package",
  "keywords": ["pi-package"],
  "pi": {
    "extensions": ["./extensions"],
    "skills":     ["./skills"],
    "prompts":    ["./prompts"],
    "themes":     ["./themes"]
  }
}
```

`assets/pi-package-template.json` を新しいパッケージの出発点としてコピーする。

**パッケージのインストール・管理：**
```bash
pi install npm:@scope/package
pi install git:github.com/user/repo
pi install https://github.com/user/repo
pi list
pi remove npm:@scope/package
pi update
pi config      # リソースの有効化・無効化
```

---

## ステップ10: マルチプロバイダLLM設定

`@earendil-works/pi-ai` は統合ストリーミングAPIを提供する。組み込みプロバイダ：Anthropic・OpenAI・Azure OpenAI・Google Gemini/Vertex・Amazon Bedrock・Mistral・Groq・Cloudflare・xAI・OpenRouterなど。

**モデルの選択：**
```bash
pi --model anthropic/claude-sonnet-4-20250514
pi --model openai/gpt-4o
pi --model sonnet:high      # 思考レベル付き
```

**カスタムモデル/プロバイダ：** `~/.pi/agent/models.json` に追加するか、Extensionで `pi.registerProvider()` を使って登録する。モノリポのソースにプロバイダを追加する場合は `references/adding-llm-provider.md` のチェックリストを参照。

---

## ステップ11: セッション管理

セッションはインプレースブランチングのためのツリー構造を持つJSONLファイル。各エントリには `id` と `parentId` がある。

```bash
pi -c                         # 直近のセッションを継続する
pi -r                         # セッションを選択して再開する
pi --session <パス|id>        # 特定のセッションを開く
pi --fork <パス|id>           # 新しいセッションにフォークする
pi --no-session               # エフェメラルモード（保存しない）
```

**セッション内ナビゲーション：**
- `/tree` — ビジュアルセッションツリー。任意のノードを選択してそこから継続できる
- `/fork` — アクティブブランチの選択したユーザーメッセージまでのパスを新しいセッションにコピーする
- `/clone` — 現在のアクティブブランチを新しいセッションファイルに複製する

コンパクションは古いメッセージを要約する（コンテキストウィンドウ内では非可逆だが、完全なJSONL履歴は常に保持される）。`/settings` → `autoCompact` で設定する。

---

## 開発ワークフロー（Piモノリポへのコントリビュート）

コード変更前に `references/development-rules.md` の全AGENTS.mdルールを確認すること。

主なルール：
- コード変更後は**パッケージルート**（リポルートではない）から `npm run check` を実行する。全エラー/警告/infoを修正してからコミット。
- `npm run build` や `npm test` は直接実行しない。
- 特定のテストを実行する場合：パッケージルートから `npx tsx ../../node_modules/vitest/dist/cli.js --run test/specific.test.ts`
- `git add -A` は使わない。セッション中に変更したファイルのみ個別にステージングする。
- ユーザーが明示的に求めない限りコミットしない。
- `any` 型・インラインdynamic import・`enum`・`namespace` は使わない。
- `packages/ai/src/models.generated.ts` は直接変更しない。ジェネレータスクリプトを更新する。

---

## エラー処理

| 状況 | 対処 |
|------|------|
| `AgentHarnessError code: "busy"` | idle でない状態で構造的操作が呼ばれた。`waitForIdle()` を待つか先に `abort()` する。 |
| `AgentHarnessError code: "hook"` | 状態コミット後にフックがスローした。状態はロールバックされないため `cause` チェーンを調査する。 |
| Extensionの読み込み失敗 | piはエラーをヘッダーに表示してExtensionなしで継続する。ファイルパスとTypeScript構文を確認する。 |
| `npm run check` 型エラー | エラー出力全体を読む。型エラーを修正するために依存関係をダウングレードしない — アップグレードする。 |
| セッションJSONLの破損 | 生の `.jsonl` ファイルを開く（1行1JSONオブジェクト）。破損行を削除または修復する。 |
| プロバイダ認証失敗 | `/login` で再認証するか、`ANTHROPIC_API_KEY` 等の環境変数が設定されているか確認する。 |
