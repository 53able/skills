# ページ構造パターン

## Pancake Stack（スティッキーフッター）

**When**: Header/Main/Footer構造でフッターを常に最下部に

```css
.layout {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}
```

**Gotchas**: `1fr` がメイン領域を伸長させ、フッターを押し下げる

### 構造例

```html
<div class="layout">
  <header>ヘッダー</header>
  <main>メインコンテンツ</main>
  <footer>フッター</footer>
</div>
```

---

## Holy Grail

**When**: ヘッダー + 左右サイドバー + メイン + フッターの5領域構造

```css
.layout {
  display: grid;
  grid-template: auto 1fr auto / auto 1fr auto;
}
header, footer { grid-column: 1 / 4; }
.left { grid-column: 1 / 2; }
main { grid-column: 2 / 3; }
.right { grid-column: 3 / 4; }
```

**Gotchas**: `grid-template` は `rows / columns` の順（スラッシュ区切り）

### 構造例

```html
<div class="layout">
  <header>ヘッダー</header>
  <aside class="left">左サイドバー</aside>
  <main>メインコンテンツ</main>
  <aside class="right">右サイドバー</aside>
  <footer>フッター</footer>
</div>
```

---

## 選択ガイド

| ユースケース | 推奨パターン |
|-------------|-------------|
| ブログ、LP | Pancake Stack |
| 管理画面、ダッシュボード | Holy Grail |

## 応用: サイドバー付きダッシュボード

Holy Grailの簡略版（左サイドバーのみ）:

```css
.dashboard {
  display: grid;
  grid-template-columns: 250px 1fr;
  min-height: 100dvh;
}

@media (max-width: 768px) {
  .dashboard { grid-template-columns: 1fr; }
}
```

**Tips**: `100vh` より `100dvh`（dynamic viewport height）を推奨。モバイルブラウザのアドレスバーを考慮する。
