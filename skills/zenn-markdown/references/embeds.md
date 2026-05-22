# Zenn 埋め込み記法

多くは **URL または ID だけの行**（前後改行）または **`@[service](...)`** 形式。

## リンクカード

```markdown
https://zenn.dev/zenn/articles/markdown-guide

@[card](https://zenn.dev/zenn/articles/markdown-guide)
```

`_` を含む URL で自動認識が壊れる場合 → `@[card](URL)` または `<URL>`。

## X（Twitter）

```markdown
https://x.com/user/status/1234567890

@[tweet](https://x.com/user/status/1234567890)
```

- リプライ元を隠す: `?conversation=none` を URL に付与
- `__` がパスに 2 つ以上ある URL → `@[tweet](URL)` 必須

## YouTube

```markdown
https://www.youtube.com/watch?v=WRVsOCh907o
```

## GitHub ファイル

```markdown
https://github.com/owner/repo/blob/main/README.md

https://github.com/owner/repo/blob/main/src/app.ts#L10-L25
```

- **テキストファイルのみ**（画像等は埋め込み不可）
- 行指定: `#L10` または `#L10-L25`

## GitHub Gist

```markdown
@[gist](https://gist.github.com/user/id)

@[gist](https://gist.github.com/user/id?file=example.json)
```

## スライド・デモ・デザイン

| サービス | 記法 |
|----------|------|
| CodePen | `@[codepen](URL)` — タブは `?default-tab=html,css` |
| SlideShare | `@[slideshare](embed_codeのkey)` |
| SpeakerDeck | `@[speakerdeck](data-id)` — `?slide=24` 可 |
| Docswell | `@[docswell](スライドURL)` または embed URL |
| JSFiddle | `@[jsfiddle](URL)` |
| CodeSandbox | `@[codesandbox](iframeのembed URL)` |
| StackBlitz | `@[stackblitz](Embed URL)` |
| Figma | `@[figma](共有URL)` |
| blueprintUE | `@[blueprintue](公開ページURL)` |

## 配置ルール

1. 埋め込み行の **前後に空行** を入れる（X / YouTube / GitHub 等）。
2. 同一段落に URL と本文を混ぜない。
3. カード化したくない URL は `<https://...>` でインラインリンク化。
