# CSS Layout Pattern Selector

> CSSレイアウトの課題に対して、最適なパターンを即座に選択・適用するスキル

## When to Use

- 要素の中央配置で悩んでいるとき
- レスポンシブなグリッド/カード配置を実装するとき
- ページ全体の構造（Header/Main/Footer等）を設計するとき
- アスペクト比や幅の制御が必要なとき

## Workflow

### Step 1: 課題の特定

ユーザーの要求を以下のカテゴリに分類する：

```
何を実現したい？
│
├─ 要素を中央に配置したい
│   ├─ 単一要素？ → Super Centered または Autobot
│   ├─ 複数要素を縦に？ → Gentle Flex
│   ├─ グループ全体を？ → Content Center
│   └─ オーバーレイ/モーダル？ → Pop n' Plop
│
├─ レスポンシブなグリッド/カード配置
│   ├─ メディアクエリなしで？ → RAM
│   ├─ 折り返して縦に積む？ → Deconstructed Pancake
│   └─ コンテナサイズベース？ → Container Query
│
├─ ページ全体の骨格を作りたい
│   ├─ Header + Main + Footer？ → Pancake Stack
│   └─ サイドバーも含む？ → Holy Grail
│
└─ サイズを制御したい
    ├─ 幅の最小・最大を設定？ → Clamping (clamp())
    └─ 縦横比を固定？ → Aspect Ratio
```

### Step 2: パターン詳細の参照

特定したパターンに応じて、以下のファイルを読み込む：

| カテゴリ | 参照ファイル |
|----------|-------------|
| 中央配置 | `patterns/centering.md` |
| レスポンシブ | `patterns/responsive.md` |
| ページ構造 | `patterns/page-structure.md` |
| コンポーネント | `patterns/component.md` |

### Step 3: 実装

1. パターンの「When」を確認し、ユースケースに合致することを確認
2. 核心コードを適用
3. 「Gotchas」（注意点）をチェック

### Step 4: 検証

- アンチパターンに該当していないか確認 → `reference/antipatterns.md`
- 不明点があればクイックリファレンスを参照 → `reference/quick-reference.md`

## Quick Pattern Selection

迷ったときの即決ガイド：

| やりたいこと | 最初に試すパターン |
|-------------|-------------------|
| とにかく中央に置きたい | Super Centered (`place-items: center`) |
| カードを並べたい | RAM (`repeat(auto-fit, minmax(...))`) |
| フッターを下に固定したい | Pancake Stack (`grid-template-rows: auto 1fr auto`) |
| 幅を柔軟に制限したい | Clamping (`clamp(min, preferred, max)`) |

## Reference Files

- `patterns/centering.md` - 中央配置パターン（5種）
- `patterns/responsive.md` - レスポンシブパターン（4種）
- `patterns/page-structure.md` - ページ構造パターン（2種）
- `patterns/component.md` - コンポーネントパターン（1種）
- `reference/quick-reference.md` - 全パターンの早見表
- `reference/antipatterns.md` - 避けるべきパターン
- `reference/examples.md` - よくある実装例
