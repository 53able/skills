# Pi モノリポ 開発ルール

ソース: https://github.com/earendil-works/pi/blob/main/AGENTS.md  
アーキテクチャ詳細: packages/agent/docs/ を参照

---

## コミュニケーションスタイル

- 回答は短く簡潔にする。
- コミット・Issue・PRコメント・コードにemoji不使用。
- 余計な言葉や楽しそうな表現は使わない。技術的な文章のみ、丁寧かつ直接的に。
- 実装コマンドを実行する前に、まず質問に答える。

---

## コード品質

- 広範囲な変更を行う前、まだ完全に確認していないファイルを編集する前、調査・監査の依頼を受けた際は、ファイルを全部読む。
- `any` 型は絶対に必要な場合を除き使わない。
- インラインimportは使わない: `await import("./foo.js")` も `import("pkg").Type` も禁止。
- `enum`・`namespace`/`module`・`import =`・`export =`・コンストラクタパラメータプロパティは使わない。標準的なトップレベルimportと明示的なフィールド代入を使う。
- `packages/ai/src/models.generated.ts` は直接変更しない — `packages/ai/scripts/generate-models.ts` を更新する。
- 型エラーを修正するために依存関係を削除またはダウングレードしない。アップグレードする。
- キーチェックをハードコードしない — 全キーバインドは設定可能にする。

---

## コマンド

- コード変更後: **パッケージルート**（リポルートではない）から `npm run check` を実行する。出力を全部取得し、切り捨てない。全エラー/警告/infoを修正してからコミット。
- `npm run check` はテストを実行しない。
- **実行禁止**: `npm run build` および `npm test`。
- 特定のテストを実行する場合（指示があった時のみ）: パッケージルートから `npx tsx ../../node_modules/vitest/dist/cli.js --run test/specific.test.ts`。
- テストファイルを作成または変更した場合は、そのテストを実行してパスするまで修正を繰り返す。
- アドホックなスクリプトは `/tmp` に書いてから実行し、不要になったら削除する。複数行のスクリプトをbashコマンドに直接埋め込まない。
- ユーザーが明示的に求めない限り**コミットしない**。

---

## Gitルール（並列エージェントにとって重要）

- **自分が変更したファイルのみステージングする**: `git add <特定のファイルパス>` を使う — `git add -A` や `git add .` は使わない。
- コミット前に `git status` を実行して、自分のファイルのみがステージングされていることを確認する。
- 関連するIssueやPRがある場合は、コミットメッセージに `fixes #N` または `closes #N` を含める。
- **禁止操作**: `git reset --hard`・`git checkout .`・`git clean -fd`・`git stash`・`git add -A`・`git add .`・`git commit --no-verify`。
- リベースのコンフリクトが発生した場合: 自分のファイルのみ解決する。変更していないファイルにコンフリクトがある場合は中断してユーザーに確認する。
- force pushは禁止。

---

## PRワークフロー

- PRはまずローカルにpullせず分析する。
- PRを自分で作らない。featureブランチで作業し、mainにマージして、pushする。
- ユーザーがPRを承認した場合のフル手順: featureブランチ作成 → PR pull → mainにrebase → 調整 → コミット → mainにマージ → push → PRをクローズ → コメントを残す。
- 複数行のコメントは常にtempファイルに書き、`--body-file` で投稿する。

---

## tmuxでのTUIテスト

```bash
tmux new-session -d -s pi-test -x 80 -y 24
tmux send-keys -t pi-test "cd /path/to/pi && ./pi-test.sh" Enter
sleep 3 && tmux capture-pane -t pi-test -p
tmux send-keys -t pi-test "プロンプトをここに入力" Enter
tmux kill-session -t pi-test
```

---

## Changelogフォーマット

場所: `packages/*/CHANGELOG.md`

`## [Unreleased]` 以下のセクション:
- `### Breaking Changes`
- `### Added`
- `### Changed`
- `### Fixed`
- `### Removed`

ルール:
- 新しいエントリは常に `## [Unreleased]` 以下に追加する。リリース済みのバージョンセクションには追加しない。
- 帰属表記: 内部変更は `Fixed foo ([#123](link))`、外部コントリビューションは `Added X ([#456](link) by [@user](link))`。

---

## 新LLMプロバイダの追加（packages/ai）

変更が必要なファイル:
1. `packages/ai/src/types.ts` — `Api` unionに追加、オプションインターフェース、`ApiOptionsMap`、`KnownProvider`
2. `packages/ai/src/providers/<provider>.ts` — `stream<Provider>()` と `streamSimple<Provider>()` を実装
3. `packages/ai/package.json` — subpathエクスポートを追加
4. `packages/ai/src/index.ts` — `export type` 再エクスポートを追加
5. `packages/ai/src/providers/register-builtins.ts` — 遅延ローダーを追加（プロバイダモジュールをここで静的importしない）
6. `packages/ai/src/env-api-keys.ts` — 認証情報検出を追加
7. `packages/ai/scripts/generate-models.ts` — モデル取得ロジックを追加
8. テスト: `stream.test.ts` および全プロバイダマトリクステストに追加
9. `packages/coding-agent/src/core/model-resolver.ts` — デフォルトモデルIDを追加
10. `packages/coding-agent/src/core/provider-display-names.ts` — 表示名を追加
11. `packages/coding-agent/src/cli/args.ts` — 環境変数ドキュメントを追加
12. ドキュメント: `packages/coding-agent/README.md`、`docs/providers.md`、`packages/ai/README.md`

---

## リリース

全パッケージは同じバージョン番号を共有する。

```bash
npm run release:patch    # バグ修正・機能追加
npm run release:minor    # API破壊的変更
```

事前にスモークテストを実施する:
```bash
npm run release:local -- --out /tmp/pi-local-release --force
/tmp/pi-local-release/node/pi --version
/tmp/pi-local-release/node/pi
```

npm WebAuthn 2FAは最終publishにメンテナーの操作が必要。publish後: 各パッケージに新しい `## [Unreleased]` セクションを追加し、コミット、mainとタグをpushする。

---

## テストスイートの構成（packages/agent）

- `test/harness/agent-harness.test.ts` — コアライフサイクル
- `test/harness/agent-harness-stream.test.ts` — ストリームオプションとプロバイダフック
- ハーネステストには `registerFauxProvider` / `fauxAssistantMessage` を使う（実際のAPI呼び出しなし）
- ハーネステストの実行: `npm run test:harness`
- カバレッジの実行: `npm run coverage:harness`
