/**
 * Pi Extension テンプレート
 * このファイルを ~/.pi/agent/extensions/, .pi/extensions/, またはPiパッケージ内に配置する。
 * piは起動時に自動で読み込む。
 *
 * デフォルトエクスポートは ExtensionAPI を受け取り、全フック・ツールを登録する。
 * 起動前に一度だけ初期化処理が必要な場合は async にする。
 *
 * ドキュメント: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md
 */

import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ─── カスタムツールを登録する ─────────────────────────────────────────────

  pi.registerTool({
    name: "example_tool",
    description: "入力をそのままエコーするサンプルツール。",
    parameters: Type.Object({
      message: Type.String({ description: "エコーするメッセージ" }),
    }),
    execute: async (_toolCallId, params, _signal) => {
      return {
        content: [{ type: "text", text: `Echo: ${params.message}` }],
        details: {},
      };
    },
  });

  // ─── スラッシュコマンドを登録する ─────────────────────────────────────────

  pi.registerCommand("example", {
    description: "サンプルコマンド",
    handler: async (_args, _ctx) => {
      // ここにコマンドの処理を実装する。
      // ctx からハーネス・セッション・UIファサードにアクセスできる。
    },
  });

  // ─── フック: 全ツール呼び出しを傍受する ───────────────────────────────────

  pi.on("tool_call", async (event, _ctx) => {
    // event.toolName, event.toolCallId, event.input
    // 実行を防ぎたい場合: return { block: true, reason: "..." }
    // 許可する場合: 何も返さない（または undefined を返す）
  });

  // ─── フック: ツール結果を変更する ─────────────────────────────────────────

  pi.on("tool_result", async (_event, _ctx) => {
    // _event.content, _event.isError, _event.details
    // 部分的なパッチを返す:
    // return { content: [...], isError: false };
  });

  // ─── フック: 各実行開始前にメッセージを注入する ───────────────────────────

  pi.on("before_agent_start", async (_event, _ctx) => {
    // _event.systemPrompt, _event.resources
    // return { messages: [...], systemPrompt: "..." };
  });

  // ─── フック: 各LLM呼び出し前にコンテキストを変換する ─────────────────────

  pi.on("context", async (event, _ctx) => {
    // メッセージのプルーニング・フィルタリング・注入が可能。
    // return { messages: filteredMessages };
    const messages = event.messages;
    return { messages };
  });
}
