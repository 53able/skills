# 中央配置パターン

## Super Centered

**When**: 任意の要素を親の中央に完璧に配置したいとき（最もシンプル）

```css
.parent {
  display: grid;
  place-items: center;
}
```

**Gotchas**: 親に高さが必要（`height: 100vh` など）

---

## Autobot

**When**: Flexコンテナ内の単一要素を素早く中央配置

```css
.parent { display: flex; }
.child { margin: auto; }
```

**Gotchas**: 複数要素には不向き

---

## Gentle Flex

**When**: 複数要素を縦方向に並べつつ中央揃え（サイズ変更なし）

```css
.parent {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1ch;
}
```

**Gotchas**: 子要素のサイズは変わらない（Content Centerとの違い）

---

## Content Center

**When**: グループ全体をまとめて中央配置

```css
.parent {
  display: grid;
  place-content: center;
  gap: 1ch;
}
```

**Gotchas**: 全ての子要素が最も幅の広い要素の幅に揃う

---

## Pop n' Plop

**When**: モーダル、ツールチップ、オーバーレイの中央配置

```css
.parent { position: relative; }
.overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**Gotchas**: 親に `position: relative` が必須

---

## 選択ガイド

| ユースケース | 推奨パターン |
|-------------|-------------|
| ローディングスピナー | Super Centered |
| フォーム内の単一ボタン | Autobot |
| ログインフォーム（複数入力） | Gentle Flex |
| カード内のアイコン+テキスト | Content Center |
| モーダルダイアログ | Pop n' Plop |
