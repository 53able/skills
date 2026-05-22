# Zenn Markdown — 標準要素

出典: [ZennのMarkdown記法一覧](https://zenn.dev/zenn/articles/markdown-guide)

## 見出し

```markdown
## 見出し2（本文の起点として推奨）
### 見出し3
#### 見出し4
```

- 本文は **`##` から**始めるのが推奨（アクセシビリティ）。
- `#` はページタイトル文脈に留める。

## リスト

```markdown
- 項目1
- 項目2
  - ネスト

1. 番号付き
2. 二つ目
```

`*` と `-` はどちらも可。

## リンク

```markdown
[アンカーテキスト](https://example.com)
```

## 画像

```markdown
![Altテキスト](https://example.com/image.png =250x)

*キャプション*

[![](https://example.com/image.png)](https://example.com)
```

- 幅: URL の後ろに半角スペース + `=250x`（px）
- キャプション: 画像の **直下の行** に `*テキスト*`

## 表

```markdown
| Head | Head |
| ---- | ---- |
| A    | B    |
```

表セル内改行: `<br>` を使う。

## コードブロック

````markdown
```js
const x = 1;
```

```js:fooBar.js
const x = 1;
```

```diff js:fooBar.js
- old
+ new
```

```text
プレーンテキスト（ハイライトなし）
```
````

- 言語指定で Shiki ハイライト
- ファイル名: ``言語:ファイル名``（`:` は区切り。**ファイル名に `:` は不可**）
- diff: `` ```diff 言語 ``。先頭が `+` `-` `>` `<` 半角スペースのいずれかでない行はハイライトされない

## インラインコード

```markdown
`code`
```

先頭・末尾の半角スペースは CSS 仕様上表示されない。

## 数式（KaTeX）

ブロック（前後に空行必須）:

```markdown

$$
e^{i\theta} = \cos\theta + i\sin\theta
$$

```

インライン: `$a \ne 0$`

## 引用

```markdown
> 引用文
```

## 脚注

```markdown
本文[^1]とインライン^[内容]。

[^1]: 脚注本文
```

## 区切り線

```markdown
-----
```

## インライン装飾

```markdown
*イタリック*
**太字**
~~打ち消し線~~
```

## 改行

Enter 1 回で `<br>` 相当の改行（段落内改行）。空行で新段落。

## 絵文字

`:emoji:` で入力補完（エディタ依存）。
