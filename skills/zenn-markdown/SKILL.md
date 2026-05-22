---
name: zenn-markdown
description: Zenn向けMarkdown（Zenn Flavored Markdown）の記法を適用し、記事・スクラップ・本の原稿を執筆・校正する。見出し階層、コードブロック、数式、メッセージ／アコーディオン、リンクカード、GitHub/YouTube/X埋め込み、mermaid制限などを扱う。Zenn記事、技術ブログ原稿、zenn-cliプロジェクトのMarkdown編集時に使う。GitHub Flavored Markdownのみ、CommonMark一般論、Zenn以外のCMS（Qiita/Note/dev.to）には使わない。
---

# Zenn Markdown 執筆

Zenn の Markdown 方言（[公式記法一覧](https://zenn.dev/zenn/articles/markdown-guide)）に沿って原稿を書く・直す。詳細な記法表は必要なときだけ `references/` を読む。

## いつ使うか

- Zenn 記事・スクラップ・本の `.md` を新規執筆または校正するとき
- `zenn-cli` プロジェクト内の Markdown をプレビュー前に整えるとき
- リンクカード・GitHub 埋め込み・mermaid など Zenn 固有記法の選択が必要なとき

## 使わない場合

- Qiita / Note / dev.to など Zenn 以外の CMS 向け原稿
- GFM や CommonMark の一般論だけが欲しいとき（Zenn 方言と混同しやすい）
- HTML タグ中心のレイアウト（Zenn は `<br>` 以外の HTML 埋め込み非対応）

## 手順

### 1. 原稿の種類と見出し方針を決める

1. 出力先が **記事 / スクラップ / 本** のどれかを確認する。
2. 本文見出しは **`##`（見出し2）から始める**ことを原則とする（アクセシビリティ推奨）。`#` は記事タイトル相当の文脈でのみ使う。
3. 段落は **Enter 1 回で改行**される（markdown-it の `breaks` 相当）。空行で段落区切りにする。

### 2. 標準要素を適用する

1. リスト・リンク・画像・表・引用・脚注・インライン装飾は `references/syntax-core.md` に従う。
2. 画像は必要なら `=250x` で幅指定、直下の `*キャプション*` でキャプションを付ける。
3. コードブロックは言語を必ず指定する。ファイル名は `` ```js:fooBar.js ``、diff は `` ```diff js:fooBar.js ``、ハイライトなし＋ファイル名は `` ```:text `` または `` ```text ``。
4. 数式は KaTeX。ブロックは `$$` の **前後に空行**、インラインは `$...$`。

### 3. Zenn 独自記法を選ぶ

1. 注意・補足・折りたたみが必要なら `references/zenn-extensions.md` を読み、次から選ぶ:
   - `:::message` / `:::message alert`（警告）
   - `:::details タイトル`（アコーディオン）
   - ネスト時は外側の `:` を増やす（`::::details` など）
2. 非公開メモは **1 行** の HTML コメント `<!-- ... -->` のみ（複数行コメントは非対応）。

### 4. 埋め込みを配置する

1. 外部コンテンツは `references/embeds.md` の表から記法を選ぶ。
2. **URL だけの行**（前後に改行）でカード化できるもの: 一般 URL、X、YouTube、GitHub ファイル permalink。
3. アンダースコア `_` を含む URL でリンクが途切れる場合:
   - カード: `@[card](URL)`
   - X: `@[tweet](URL)`
   - 単純リンク: `<URL>`
4. GitHub 埋め込みは **テキストファイルのみ**。行範囲は `#L1-L3` 形式。

### 5. mermaid を書く

1. `` ```mermaid `` ブロックを使う。
2. 制限を守る: **2000 文字以内**、フローチャートの `&` チェーン **10 以下**、クリックイベントは無効（設定しない）。
3. 詳細と回避策は `references/mermaid-limits.md` を読む。

### 6. 執筆後チェック

1. スキル同梱の `scripts/validate-zenn-markdown.py` を対象ファイルに実行する:

```bash
python3 scripts/validate-zenn-markdown.py path/to/article.md
```

2. `zenn-cli` 利用時はローカルプレビューでレンダリングを確認する:

```bash
npx zenn preview
```

3. 警告・エラーを修正し、再実行して **エラー 0** を確認する。

## クイック参照（最小）

| 目的 | 記法 |
|------|------|
| 注意ボックス | `:::message` / `:::message alert` |
| 折りたたみ | `:::details タイトル` … `:::` |
| リンクカード | URL 単独行 または `@[card](URL)` |
| GitHub コード | permalink 単独行 + 任意 `#L10-L20` |
| 数式ブロック | 空行 + `$$` … `$$` + 空行 |
| 表内改行 | `<br>` |

## エラー処理

| 症状 | 対処 |
|------|------|
| 数式がレンダリングされない | `$$` の前後に空行があるか確認 |
| URL カードが途中で切れる | `_` を含む URL → `@[card](...)` または `<...>` |
| mermaid がエラー表示 | 2000 文字超・`&` 過多・非対応記法を `references/mermaid-limits.md` で確認 |
| コードにファイル名を付けたいが `:` を含む | 現状不可（区切りが `:` のため）。ファイル名から `:` を除くか本文で明示 |
| インラインコード先頭/末尾の半角スペースが消える | Zenn 仕様。必要なら U+2000 等の特殊スペースを検討 |
| `<br>` 以外の HTML が効かない | Markdown／Zenn 拡張記法に置き換える |
| CLI と Web で差分 | `npm install zenn-cli@latest` で CLI を更新 |

## 参照ファイル

| ファイル | 内容 |
|----------|------|
| `references/syntax-core.md` | 見出し・リスト・画像・表・コード・数式・脚注 |
| `references/zenn-extensions.md` | message / details / コメント |
| `references/embeds.md` | リンクカード・SNS・GitHub・スライド・Figma 等 |
| `references/mermaid-limits.md` | mermaid 制限と分割方針 |
