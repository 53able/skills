# コンポーネントパターン

## Aspect Ratio

**When**: 画像や動画の縦横比を維持

```css
.video-container { aspect-ratio: 16 / 9; }
.square { aspect-ratio: 1 / 1; }
.portrait { aspect-ratio: 3 / 4; }
```

**Gotchas**: 旧来の `padding-top` ハックは不要

---

## よく使う比率

| 用途 | 比率 | CSS |
|------|------|-----|
| YouTube動画 | 16:9 | `aspect-ratio: 16 / 9;` |
| Instagram投稿 | 1:1 | `aspect-ratio: 1 / 1;` |
| ポートレート写真 | 3:4 | `aspect-ratio: 3 / 4;` |
| 映画風 | 21:9 | `aspect-ratio: 21 / 9;` |
| OGP画像 | 1.91:1 | `aspect-ratio: 1.91 / 1;` |

---

## 画像との組み合わせ

```css
.image-container {
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

**Tips**: `object-fit: cover` でアスペクト比を維持しつつコンテナを埋める
