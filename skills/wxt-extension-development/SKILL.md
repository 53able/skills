---
name: wxt-extension-development
description: WXTを使ったブラウザ拡張開発を支援する。プロジェクト調査、entrypoint設計、manifestと権限変更、content script UI、storage、messaging、build、zip、ブラウザ検証を扱う。WXTプロジェクトの作成、変更、監査、デバッグ時に使う。非WXT拡張、汎用フロントエンド、拡張ストア審査には使わない。
---

# WXT拡張開発

## 手順

**Step 1: 作業対象を確認する**
1. WXTプロジェクトの新規作成か、既存プロジェクトの変更かを判定する。
2. 既存プロジェクトの場合、最初に `python scripts/inspect-wxt-project.py .` を実行して、`package.json`、`wxt.config.*`、`entrypoints/`、生成物ディレクトリの状態を確認する。
3. 新規作成の場合、パッケージマネージャ、UIテンプレート（Vanilla / React / Vue / Svelte / Solid）、対象ブラウザ（Chrome / Firefox / Safariなど）、生成先ディレクトリを明示してから `wxt init` の実行計画を作る。
4. WXT公式仕様や用語が必要な場合だけ、`references/wxt-field-guide.md` を読む。

**Step 2: 変更前に計画を作る**
1. 変更対象のentrypointを1つずつ特定する。popup、options、background、content scriptを混同しない。
2. 実行環境を明示する。backgroundは拡張側、content scriptはページ側、popup/optionsはHTML entrypointとして扱う。
3. `manifest.json` を直接編集する計画を立てない。manifest、permissions、host permissionsは原則 `wxt.config.*` またはentrypoint設定から生成させる。
4. 権限追加、host範囲拡大、依存関係追加、生成物削除が必要な場合は、人間レビューを必須ゲートとして計画に入れる。
5. 検証コマンドを計画に含める。最低限、プロジェクトに存在するbuild scriptを使う。Firefoxやzip配布が対象なら該当scriptも含める。

**Step 3: WXTの構造に沿って実装する**
1. `entrypoints/` 直下のファイル名または1階層ディレクトリでentrypointを定義する。深いネストに自動発見を期待しない。
2. popupやoptionsの関連ファイルは `entrypoints/popup/`、`entrypoints/options/` のようにまとめる。補助ファイルを `entrypoints/` 直下へ雑に置かない。
3. background処理は `defineBackground` のコールバック内へ置く。
4. content script処理は `defineContentScript({ ..., main(ctx) { ... } })` の `main(ctx)` 内へ置く。
5. `browser.*`、`document`、`window` など実行時APIをentrypointトップレベルで呼ばない。トップレベルは設定、import、型、純粋関数に限定する。
6. 拡張APIは原則 `wxt/browser` の `browser` を使う。ブラウザ差分があるAPIはfeature detectionまたはoptional chainingで扱う。
7. 生成物ディレクトリ `.wxt/` と `.output/` を編集しない。

**Step 4: content script UIを設計する**
1. ページへUIを挿入する場合、分離度に応じて方式を選ぶ。
   - ページCSSの影響を許容する小さなUI: `createIntegratedUi`
   - ページCSSから守りたいUI: `createShadowRootUi`
   - HMRや強い分離が重要なUI: `createIframeUi`
2. Shadow Root UIでは `cssInjectionMode: 'ui'` を検討する。
3. IFrame UIではiframe用HTMLと `web_accessible_resources` の必要性を確認する。
4. SPA対象では、通常のページ遷移でcontent scriptが再実行されない前提で、`ctx.locationWatcher` や `wxt:locationchange` の使用を検討する。
5. 対象URLの `matches` は最小範囲に限定する。`<all_urls>` は明確な理由がある場合だけ使う。

**Step 5: storage、messaging、permissionsを扱う**
1. storageを使う場合は `wxt/utils/storage` の採用を優先検討し、`storage` permissionの要否を明示する。
2. messagingでは、vanilla extension messagingを使うか、`webext-bridge` / `@webext-core/messaging` などを導入するかを先に決める。
3. permissionsやhost permissionsを追加する場合、各権限の用途、対象entrypoint、対象ブラウザ、代替案を説明する。
4. APIの型が存在しても全ブラウザで実行可能とは断定しない。対象ブラウザの実行可否を検証項目に入れる。

**Step 6: 検証する**
1. `package.json` のscriptsを読んで、実在するコマンドだけを実行する。
2. 代表的な検証順序を使う。
   - 型チェックscriptがある場合: `npm run typecheck` など
   - build: `npm run build` または該当パッケージマネージャのbuild script
   - Firefox対象: `npm run build:firefox`
   - zip配布対象: `npm run zip` と必要に応じて `npm run zip:firefox`
3. build後に `.output/{target}/manifest.json` を確認し、permissions、host permissions、content scripts、background、action/popupが意図通り生成されたか点検する。
4. ブラウザ確認項目を報告する。popup表示、content scriptの対象URL限定、backgroundイベント、console error、権限表示、拡張再読み込み後の挙動を含める。
5. 失敗時はエラーログを要約し、関係ないリファクタや依存追加へ飛ばず、最小修正案を出す。

**Step 7: レビューする**
1. `git diff` または変更ファイル一覧を確認する。
2. `.wxt/`、`.output/`、lockfile、package manifest、permissionsが意図せず変わっていないか確認する。
3. 変更内容、検証結果、未検証のブラウザ、手動確認事項を分けて報告する。
4. WXTやClaude Code向けプロジェクトルールを残す必要がある場合だけ、`assets/claude-wxt-guidelines.md` を参照して短い `CLAUDE.md` 案を作る。

## エラー処理

* `scripts/inspect-wxt-project.py` が `package.json が見つかりません` を返す場合、作業ディレクトリを確認し、既存プロジェクトではなく新規作成フローへ切り替える。
* `wxt.config.*` が見つからない場合、`package.json` のdependencies/devDependenciesに `wxt` があるか確認する。なければWXTプロジェクトと断定しない。
* buildで `browser is not defined`、`document is not defined`、`window is not defined` が出る場合、entrypointトップレベルの実行時API呼び出しを探し、callbackまたは`main(ctx)`内へ移す。
* content scriptが対象ページで動かない場合、`matches`、host permissions、対象ブラウザ、SPA遷移、生成manifestを順に確認する。
* 権限追加が必要になった場合、実装を止め、追加理由と最小権限案を提示して承認を待つ。
* 公式仕様の記憶と実プロジェクトの挙動が衝突する場合、現在のWXTバージョン、公式ドキュメント、実行結果を優先する。
