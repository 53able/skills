# 使用例：よくある実装パターン

## ローディングスピナーの中央配置

```css
.loading-container {
  display: grid;
  place-items: center;
  min-height: 200px;
}
```

**使用パターン**: Super Centered

---

## レスポンシブなカードグリッド

```css
.card-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

**使用パターン**: RAM

---

## フルハイトアプリレイアウト

```css
.app {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-height: 100dvh; /* dvh = dynamic viewport height */
}
```

**使用パターン**: Pancake Stack

**Tips**: `100vh` より `100dvh` を推奨。モバイルブラウザのアドレスバーを考慮する。

---

## サイドバー付きダッシュボード

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

**使用パターン**: Holy Grail の簡略版

---

## モーダルダイアログ

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  width: clamp(300px, 90%, 600px);
  max-height: 90vh;
  overflow-y: auto;
}
```

**使用パターン**: Super Centered + Clamping

---

## レスポンシブなナビゲーション

```css
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.nav-item {
  flex: 0 1 auto;
}
```

**使用パターン**: Deconstructed Pancake（shrinkなし）

---

## サムネイル画像グリッド

```css
.thumbnail-grid {
  display: grid;
  gap: 0.5rem;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
}

.thumbnail {
  aspect-ratio: 1 / 1;
  overflow: hidden;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

**使用パターン**: RAM + Aspect Ratio
