# レスポンシブパターン

## RAM (Repeat, Auto, Minmax)

**When**: メディアクエリなしでレスポンシブなグリッドレイアウト

```css
.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}
```

**Gotchas**:
- `auto-fit`: 空トラックを折りたたみ、アイテムが伸長
- `auto-fill`: 空トラックを維持

---

## Deconstructed Pancake

**When**: 横並びから縦積みへ自動折り返し

```css
.parent {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}
.item {
  flex: 1 1 150px; /* grow shrink basis */
}
```

**Gotchas**: `flex-basis` が折り返しのトリガーポイント

---

## Clamping

**When**: 幅やフォントサイズに最小・推奨・最大値を設定

```css
.card { width: clamp(23ch, 60%, 46ch); }
.title { font-size: clamp(1.5rem, 5vw, 3rem); }
```

**Gotchas**: `clamp(min, preferred, max)` の順序を間違えない

---

## Container Query

**When**: ビューポートではなくコンテナサイズに応じてスタイル変更

```css
.container { container: inline-size; }

@container (min-width: 350px) {
  .card {
    display: grid;
    grid-template-columns: 40% 1fr;
  }
}
```

**Gotchas**:
- 親に `container: inline-size` が必須
- `container-name` でネストされたコンテナを識別可能

---

## 選択ガイド

| ユースケース | 推奨パターン |
|-------------|-------------|
| 商品カード一覧 | RAM |
| タグ/バッジの並び | Deconstructed Pancake |
| 記事本文の幅制限 | Clamping |
| サイドバー内のカード | Container Query |

## RAM vs Deconstructed Pancake

| 特性 | RAM | Deconstructed Pancake |
|------|-----|----------------------|
| 基盤 | Grid | Flexbox |
| 列数 | 自動計算 | 折り返しで変動 |
| アイテム幅 | 均等 | 伸縮可能 |
| 推奨用途 | カードグリッド | タグ、ナビゲーション |
