# Piへの新LLMプロバイダ追加（packages/ai）

ソース: https://github.com/earendil-works/pi/blob/main/AGENTS.md#adding-a-new-llm-provider-packagesai

このチェックリストを順番に実施すること。各ファイルグループの後に `packages/ai` から `npm run check` を実行する。

---

## 1. コア型定義（`packages/ai/src/types.ts`）

- `Api` type unionにAPIの識別子を追加する（例: `"my-provider-stream"`）
- `StreamOptions` を継承するオプションインターフェースを作成する
- `ApiOptionsMap` にマッピングを追加する
- `KnownProvider` type unionにプロバイダ名を追加する

## 2. プロバイダ実装（`packages/ai/src/providers/my-provider.ts`）

以下をエクスポートする：

```typescript
export function streamMyProvider(options: MyProviderStreamOptions): AssistantMessageEventStream
export function streamSimpleMyProvider(options: SimpleStreamOptions): AssistantMessageEventStream
```

メッセージとツールをプロバイダ形式に変換する。標準化されたイベントをemitする: `text`, `tool_call`, `thinking`, `usage`, `stop`。

## 3. エクスポートと遅延登録

1. `packages/ai/package.json` にsubpathエクスポートを追加する:
   ```json
   "./providers/my-provider": "./dist/providers/my-provider.js"
   ```

2. ルートエントリから必要なオプション型の `export type` 再エクスポートを `packages/ai/src/index.ts` に追加する。

3. `packages/ai/src/providers/register-builtins.ts` に遅延ローダーラッパーを登録する — **ここでプロバイダモジュールを静的importしない**。

4. `packages/ai/src/env-api-keys.ts` に認証情報検出を追加する。

## 4. モデル生成（`packages/ai/scripts/generate-models.ts`）

プロバイダからモデルを取得・パースし、標準化された `Model` インターフェースにマップするロジックを追加する。

`packages/ai/src/models.generated.ts` は直接変更しない — 生成物ファイルである。

## 5. テスト（`packages/ai/test/`）

必須:
- `stream.test.ts` — 代表的なモデルを最低1件
- `tokens.test.ts`, `abort.test.ts`, `empty.test.ts`, `context-overflow.test.ts`
- `unicode-surrogate.test.ts`, `tool-call-without-result.test.ts`
- `image-tool-result.test.ts`, `total-tokens.test.ts`
- `cross-provider-handoff.test.ts` — プロバイダ/モデルのペアを最低1件

非標準の認証の場合は `test/my-provider-utils.ts` を作成して認証情報検出を実装する。

## 6. コーディングエージェント連携（`packages/coding-agent/`）

- `src/core/model-resolver.ts` → `defaultModelPerProvider` にデフォルトモデルIDを追加する
- `src/core/provider-display-names.ts` → `/login` UIの表示名を追加する
- `src/cli/args.ts` → 環境変数のドキュメントを追加する

## 7. ドキュメント

- `packages/coding-agent/README.md` → プロバイダ一覧に追加する
- `packages/coding-agent/docs/providers.md` → セットアップ手順・環境変数・`auth.json` キーを追加する
- `packages/ai/README.md` → プロバイダテーブル・オプション・認証・環境変数を追加する
- `packages/ai/CHANGELOG.md` → `## [Unreleased]` にエントリを追加する
