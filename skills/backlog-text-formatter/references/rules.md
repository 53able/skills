# Backlog記法 変換ルール一覧

Backlog（Nulab）のWiki/課題コメント記法と、それが変換されるHTMLの対応表。各ルールは「整形前（記法）」と「整形後（HTML）」のペアで示す。`scripts/backlog_to_html.py` はこの表に基づいて記法→HTML変換を決定的に行う。記法を新しく書く場合（HTML/意図→記法）は、この表を逆引きして適用する。

## 1. 課題リンク・Wikiページリンク
- 記法: `BLG-95`, `[[BLG-98]]`, `[[WikiPageName]]`
- 変換後: それぞれリンク（ボタン風要素）になる。`KEY-番号` 形式は課題キーとして自動リンク、`[[...]]` で囲むと課題キーでもWikiページ名でも同様にリンクになる。
- HTML: `<button type="button" role="button" class="_trigger-text">表示テキスト</button>`

## 2. 太字
- 記法: `''Bold''`（シングルクオート2個で囲む）
- 変換後: `<b>Bold</b>`

## 3. 斜体
- 記法: `'''Italic'''`（シングルクオート3個で囲む）
- 変換後: `<i>Italic</i>`
- 注意: 斜体（3個）と太字（2個）の記法は衝突しやすいため、**3個パターンを先に処理**してから残りに2個パターンを適用する。

## 4. 打ち消し線
- 記法: `%%Strike%%`
- 変換後: `<s>Strike</s>`

## 5. 色
- 記法:
  - `&color(#f00) { Color }` → 文字色を16進指定
  - `&color(red) { Color }` → 文字色を色名指定
  - `&color(#ffffff, #abd500) { Color }` → 文字色, 背景色の順で2つ指定
- 変換後: `<span style="color: <色1>;">Color</span>` または `<span style="color: <色1>; background-color: <色2>;">Color</span>`
- 色1つのみ指定時は `color` のみ、2つ指定時は1つ目が `color`、2つ目が `background-color`。

## 6. URL
- 記法:
  - `https://backlog.com/`（URLをそのまま書く）
  - `[[Backlog>https://backlog.com/]]`（表示名とURLを `>` で区切る）
  - `[[Backlog:https://backlog.com/]]`（表示名とURLを `:` で区切る）
- 変換後: `<a href="URL" class="loom-link-another">表示テキスト</a>`
  - 生URLの場合は表示テキスト=URL自身。
  - `[[表示名>URL]]` / `[[表示名:URL]]` の場合は表示テキスト=表示名。

## 7. 見出し
- 記法: 行頭の `*` の数で見出しレベルを決める。
  - `* Header1` → h1
  - `** Header2` → h2
  - `*** Header3` → h3
- 変換後: `<h1> Header1</h1>` のように、`*`直後の空白を含めてそのままテキストにする（先頭スペースは保持）。

## 8. 箇条書き（リスト）
- 記法: 行頭の `-` の数でネストレベルを決める。
  - `- Item-A` → 第1階層
  - `-- Item-B-1` → 第2階層
  - `--- Item-B-2-a` → 第3階層
- 変換後: `<ul><li> Item-A</li><li> Item-B<ul><li> Item-B-1<ul><li> Item-B-2-a</li></ul></li></ul></li></ul>`
- ネストは親項目の `<li>` テキストの直後に子 `<ul>` を入れ子にする。

## 9. 箇条書き（数字リスト）
- 記法: 行頭の `+`（階層は付けず常に1個）
  - `+ Item-A`
  - `+ Item-B`
  - `+ Item-C`
- 変換後: `<ol><li> Item-A</li><li> Item-B</li><li> Item-C</li></ol>`

## 10. 表
- 記法: `|セル|セル|セル|` の行を並べる。
  - 行末に `h` が付くと、その行はヘッダー行（`<th>`）になる: `|A|B|C|h`
  - セルの先頭が `~` だと、そのセルだけ `<th>` になる（行見出し）: `|~No.1|aaa|bbb|`
  - 空行が挟まると別テーブルとして区切られる。
- 変換後: `<table><tbody>...</tbody></table>`
  - 通常セル → `<td>`、`h`行のセル → `<th>`、`~`付きセル → `<th>`。

## 11. 引用文
- 記法:
  - 行頭 `>` を付ける方式: `> 引用した` / `> 文章です。`（連続する `>` 行は1つの引用ブロックにまとまる）
  - ブロック方式: `{quote} ... {/quote}`（複数行、各行を段落に分ける）
- 変換後: `<blockquote><p>引用した</p><p>文章です。</p></blockquote>`

## 12. コードマクロ
- 記法: `{code} ... {/code}` で囲む（複数行、そのままのインデント・改行を保持）
- 変換後: `<pre class="loom_code prettyprint">...内容そのまま（HTMLエスケープ済み）...</pre>`

## 13. Subversionリビジョン詳細へのリンク
- 記法: `#rev(リビジョン番号)` 例: `#rev(11)` / `#rev(プロジェクトキー/リビジョン番号)` 例: `#rev(BLG/11)`
- 変換後: `<button type="button" role="button" class="_trigger-text">r11</button>`
- ルール: リビジョン番号部分（`/` の後ろ、無ければ全体）が数字のみなら `r` を先頭に付けてボタン化する。

## 14. Gitリビジョン詳細へのリンク
- 記法: `#rev(リポジトリ:リビジョン)` 例: `#rev(app:abcdeabcde)` / `#rev(プロジェクトキー/リポジトリ:リビジョン)` 例: `#rev(BLG/app:abcdeabcde)`
- 変換後: `<button type="button" role="button" class="_trigger-text">app:abcdeabcde</button>` および `<button type="button" role="button" class="_trigger-text">BLG/app:abcdeabcde</button>`
- ルール: 引数に `:` を含む場合はGitリビジョンとみなし、ボタンのテキストは引数をそのまま使う（変換しない）。

## 15. 目次
- 記法: `#contents`
- 変換後: 文書内の見出し（h1〜h3）を `<ul class="loom-table-of-content">` にフラットに列挙し、各項目は対応する見出しの `id`（`loom-header-0`, `loom-header-1`, ...文書内の出現順）へのアンカーリンクになる。
- 見出し自体にも同じ連番の `id="loom-header-N"` を付与する必要がある。
- 注意: 元のルール表には `Header1`(h1)→`Header2`(h2)→`Header3`(h3) の並びがフラット（入れ子なし）になる例に加えて、さらに深い `Header3-1` が `<ul>` で入れ子になる例も示されているが、`Header3-1` に対応する「整形前」記法が示されておらず再現条件が不明。`scripts/backlog_to_html.py` はフラット列挙のみをサポートする。

## 16. 改行
- 記法: `aaa&br;bbb`
- 変換後: `aaa<br>bbb`

## 17. 画像の貼り付け（他サイトのURL）
- 記法: `#image(https://.../logo.svg)`
- 変換後: `<img src="URL" class="loom-external-image" alt="ファイル名から生成した簡易alt">`

## 18. 縮小画像の貼り付け（他サイトのURL）
- 記法: `#thumbnail(https://.../logo.svg)`
- 変換後: `<img src="URL" class="loom-external-image-thumbnail" alt="ファイル名から生成した簡易alt">`

## 19. 特殊な文字をそのまま出力（エスケープ）
- 記法: `\\%\\%Not struck\\%\\%` → 打ち消し線記法として解釈させず `%%Not struck%%` という文字そのものを出力する。
- 表の中で `|` をセル区切りではなく文字として出したい場合: `\\|\\|` → `||`
- 変換後: エスケープされた `\\%\\%` は `%%` に、`\\|\\|` は `||` に変換されるが、それぞれ通常の打ち消し線処理・セル区切り処理の対象から除外される。

## 処理順序の指針（`scripts/backlog_to_html.py` が採用する順序）
1. エスケープ列（`\\%\\%`, `\\|\\|`）を一時プレースホルダに退避する。
2. `{code}...{/code}` ブロックを抜き出し、内容をHTMLエスケープした `<pre>` に確定させ、他の処理から保護する。
3. `{quote}...{/quote}` ブロックを `<blockquote>` に変換する。
4. 行単位で見出し（`*`）・箇条書き（`-`/`+`）・表（`|`）・引用（行頭`>`）のブロック構造を解析する。
5. `#contents` があれば、手順4で収集した見出し一覧からTOCを生成する。
6. 残るインラインテキストに対して、リンク系（課題/Wiki/URL/`#rev`/画像/`#thumbnail`）→ 斜体（3連クオート）→ 太字（2連クオート）→ 打ち消し線 → 色 → 改行の順で変換する。
7. 手順1で退避したエスケープ列を実際の文字（`%%`, `||`）へ戻す。
