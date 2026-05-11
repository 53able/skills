# アンチパターン

## 避けるべきパターン

| やりがち | 問題点 | 代わりに |
|---------|--------|---------|
| `margin: 0 auto` で垂直中央 | 水平方向のみ有効 | `place-items: center` を使う |
| `position: absolute` + 固定値 | レスポンシブでない | `transform: translate(-50%, -50%)` |
| メディアクエリの乱用 | 保守性低下 | `clamp()`, `minmax()`, Container Query |
| `padding-top: 56.25%` でアスペクト比 | ハック的で読みにくい | `aspect-ratio: 16/9` |
| `float` でレイアウト | 旧式、予期せぬ挙動 | Flexbox または Grid |
| 固定幅 (`width: 300px`) | レスポンシブでない | `clamp()` または `minmax()` |

---

## 詳細解説

### margin: 0 auto の誤用

```css
/* NG: 垂直方向には効かない */
.center {
  margin: 0 auto;
  /* 水平方向のみ中央に配置される */
}

/* OK: Grid で完全中央 */
.parent {
  display: grid;
  place-items: center;
}
```

### 固定値による配置

```css
/* NG: 様々な画面サイズで崩れる */
.modal {
  position: absolute;
  top: 200px;
  left: 400px;
}

/* OK: 常に中央 */
.modal {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

### メディアクエリの乱用

```css
/* NG: 保守が困難 */
@media (max-width: 1200px) { .card { width: 30%; } }
@media (max-width: 900px) { .card { width: 45%; } }
@media (max-width: 600px) { .card { width: 100%; } }

/* OK: 自動で適応 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}
```

### padding-top ハック

```css
/* NG: 意図が読み取りにくい */
.video-wrapper {
  position: relative;
  padding-top: 56.25%; /* 16:9 = 9/16 = 0.5625 */
}
.video-wrapper iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* OK: 意図が明確 */
.video-wrapper {
  aspect-ratio: 16 / 9;
}
```

### float によるレイアウト

```css
/* NG: clearfix が必要、予期せぬ挙動 */
.sidebar { float: left; width: 200px; }
.main { float: left; width: calc(100% - 200px); }
.clearfix::after { content: ""; display: block; clear: both; }

/* OK: 明確で予測可能 */
.layout {
  display: grid;
  grid-template-columns: 200px 1fr;
}
```
