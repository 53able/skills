# Claude Code 向けプロンプト例

WXT 拡張を Claude Code で進めるときの依頼テンプレート。禁止事項と停止条件を必ず含める。

## チーム既定

| 項目 | 既定値 |
|------|--------|
| UI フレームワーク | React |
| 対象ブラウザ | Chrome only（`build:firefox` / `zip:firefox` は既定では実行しない） |
| messaging | `webext-bridge`（新規導入時の第一候補。既存が vanilla なら無理に置き換えない） |

新規 `wxt init` では React テンプレートを選ぶ。Firefox 配布や messaging 方式の変更が必要なときは、計画段階で明示的に逸脱理由を書く。

## 読み取り専用調査

```
この WXT プロジェクトを読み取り専用で調査してください。

対象:
- package.json
- wxt.config.*（存在する場合）
- web-ext.config.ts（存在する場合）
- entrypoints/
- src/（存在する場合）

出力:
- UI フレームワークとパッケージマネージャ
- entrypoints ごとの役割
- manifest / permissions の定義場所
- 開発・build・zip の実行コマンド
- 変更前に確認すべきリスク

禁止事項:
- ファイルを編集しない
- コマンドを実行しない
- 依存関係を追加しない

完了条件: 調査結果だけを箇条書きで出し、次の作業提案を 3 つまで示して停止してください。
```

代替: スキル同梱の `scripts/inspect-wxt-project.py` を WXT プロジェクトルートに対して実行する。

## 計画のみ（実装前）

```
[機能の説明] を実装したいです。まだ編集しないで、実装計画だけを作ってください。

開始状態:
- WXT プロジェクト内で作業しています
- 対象 entrypoint の有無は未確認です

計画に含めるもの:
- 確認するファイル
- 変更予定のファイル
- 追加・変更する UI の仕様
- manifest / permissions 変更の要否
- messaging 方式（既定は webext-bridge）
- 検証コマンド（既定は Chrome: npm run build）
- ブラウザで確認する項目

禁止事項:
- 承認前に編集しない
- 依存関係を追加しない
- host_permissions を広げない
- 対象外 entrypoint をリファクタしない

停止条件: 計画を出したら停止し、実装してよいか確認してください。
```

plan mode を使う場合: `claude --permission-mode plan`。調査のための読み取りは許可されるが、コマンド実行を止めたいときはプロンプトで明示する。

## 小さく実装

```
WXT プロジェクトで [要件] を実装してください。

変更範囲:
- 追加/変更してよい: [entrypoint と隣接ファイルのみ]
- 変更してはいけない: 既存 entrypoints、wxt.config.*、package.json、生成物（.wxt/、.output/）

要件:
- UI は React（popup/options の場合は entrypoint 配下の React 構成に従う）
- runtime 処理は defineBackground のコールバックまたは defineContentScript の main(ctx) 内に置く
- matches は [最小 URL] に限定する
- messaging が必要なら webext-bridge を使う（既存方式がある場合はそれに合わせる）
- 不要な permissions や host_permissions を追加しない
- Only make the requested change. Do not add extra features, abstractions, or refactors.

人間レビューが必要な操作:
- ファイル削除
- 依存関係追加
- manifest / permissions / host_permissions 変更
- 対象 URL の拡大

検証:
- 実装後に npm run build を実行する（Chrome only）
- build できない場合はエラーを要約し、大きな設計変更をせず停止する

完了条件:
- 変更ファイル一覧
- 実装内容の要約
- build 結果
- ブラウザで手動確認すべき項目
を報告して停止してください。
```

## 避ける依頼

```
便利な拡張を全部作って。
```

entrypoint の種類・対象 URL・UI 方式・検証方法まで渡す。
