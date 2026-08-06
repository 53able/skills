---
name: backlog-text-formatter
description: Converts Backlog (Nulab) wiki notation into HTML, and converts formatting intent into correct Backlog notation, following Backlog's official rule set for issue/wiki links, bold, italic, strikethrough, color, URLs, headings, bulleted and numbered lists, tables, blockquotes, code blocks, revision links, table of contents, line breaks, and images. Use when a request involves formatting, converting, previewing, or writing text in Backlog wiki syntax. Do not use for generic Markdown, Confluence, MediaWiki, or other non-Backlog wiki syntaxes.
---

# Backlog記法フォーマッター

Backlog（Nulab）のWiki/課題コメント記法と、それが変換されるHTMLとの間を橋渡しする。全ルールの詳細対応表は `references/rules.md` にある。

## Procedures

**Step 0: 変換方向を判定する**
1. 入力が Backlog記法のテキスト（`''`, `%%`, `*`, `-`, `+`, `|`, `{code}`, `#rev(...)` などを含む）で、それをHTML/プレビューに変換したい場合 → **Step 1（デコード）** へ進む。
2. 入力が「こういう見た目にしたい／このHTMLをBacklogコメントに貼りたい」という意図やプレーンテキストで、正しいBacklog記法を書きたい場合 → **Step 2（エンコード）** へ進む。
3. どちらとも判断できない場合は、ユーザーに「Backlog記法→HTML変換」か「HTML/意図→Backlog記法」かを確認する。

**Step 1: デコード（Backlog記法 → HTML）**
1. 変換したいBacklog記法テキストをファイルに書き出す（既にファイルがあればそれを使う）。
2. `uv run scripts/backlog_to_html.py <入力ファイル>` を実行する（依存はuvで閉じ込める。標準ライブラリのみだがuv経由で統一する）。標準入力からも変換できる（`cat input.txt | uv run scripts/backlog_to_html.py -`）。
3. 出力されたHTMLをそのままユーザーに提示する。整形して見せたい場合は、HTMLをそのまま提示するか、必要であれば軽くインデントして提示する（スクリプトの出力自体は1行に連結されたHTML）。
4. スクリプトが対応していない/想定外の構文が混じっていて出力が崩れる場合は、`references/rules.md` の該当ルールを読み、手動で該当部分だけをHTMLに変換して補う。

**Step 2: エンコード（意図・HTML → Backlog記法）**
1. `references/rules.md` を読み、目的の見た目（太字、リンク、表、見出し、リスト、引用、色など）に対応する記法を特定する。
2. 該当する記法を使ってBacklogテキストを組み立てる。複数ルールを組み合わせる場合は、記法どうしが衝突しないよう順序に注意する（例: 斜体`'''...'''`と太字`''...''`が隣接する場合は間にスペースや別要素を挟む）。
3. 組み立てたBacklog記法テキストをユーザーに提示する。可能であれば Step 1 の手順でHTMLへ変換し、意図した見た目になっているかを自己検証してから提示する。

## 注意点・既知の制約
- 見出しは `*`/`**`/`***`（1〜3階層）のみを想定する。表内の改行や、ネストした表など未定義の組み合わせは `references/rules.md` にも記載が無く、スクリプトも対応していない。
- 行頭 `>` による引用は連続行を1つの`<blockquote>`にまとめる。`{quote}...{/quote}`ブロックも同様に変換されるが、両者を混在させた場合の挙動は未定義。
- `#rev(...)` は引数に `:` を含めばGitリビジョン（テキストをそのまま使う）、含まなければSVNリビジョン（`r`を先頭に付ける）として扱う。
- スクリプトは実際にブラウザでレンダリングした際の見た目を優先し、`<`のみをエスケープする簡易実装（`{code}`ブロック内だけは`&`/`<`/`>`/引用符すべてを完全エスケープする）。信頼できない外部入力をそのまま公開ページに埋め込む用途では不十分なため、その場合は `scripts/backlog_to_html.py` 内のコメント（`ponytail:`）に記載した強化方針に従って `html.escape` を全面適用する版に直すこと。

## Error Handling
- `scripts/backlog_to_html.py` が例外で落ちる場合は、入力テキストの該当ブロック（`{code}`/`{quote}`/表）が正しく開始・終了タグで閉じられているか確認する。
- 変換結果の`<ul>`/`<li>`のネストがおかしい場合は、箇条書きの`-`の数（階層）が1行ごとに1段以上飛んでいないか確認する（例: `-`の次に`---`のような2段飛びはBacklogでも未定義）。
- `uv run scripts/backlog_to_html.py --test` を実行し、既知の変換ルールに対する内部の自己テストが全てパスすることを確認する。失敗した場合はまずこのテストの差分を見て、正規表現やブロック抽出ロジックのどこが崩れたかを特定する。
