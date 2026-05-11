---
name: css-layout
description: >-
  CSSのレイアウト課題に対し、中央配置・レスポンシブグリッド・ページ骨格・サイズ制御のパターンを選定し適用する。Flexbox、Grid、clamp、aspect-ratio、コンテナクエリを扱う。中央配置、スティッキーフッター、オーバーレイ、カードグリッド、幅制約の実装時に使う。アニメーション、タイポグラフィ刻度、カラーテーマ、JavaScript主導のレイアウトには使わない。
---

# CSSレイアウト・パターン選択

> 課題を分類し、名前付きパターンと核心CSSへ落とし込む。詳細は `references/` をオンデマンドで読む。

## いつ使うか

- 要素の中央配置で手段が定まらないとき
- レスポンシブなグリッドやカード列を組むとき
- Header / Main / Footer やサイドバーを含むページ骨格を設計するとき
- `clamp` や `aspect-ratio`、コンテナクエリでサイズや見え方を制御するとき

## 使わない場合

- アニメーション・トランジション主体の演出
- フォントサイズスケールや行間などタイポグラフィ専用の調整
- テーマカラー／デザイントークンだけの変更
- レイアウトを JavaScript で測り回す実装方針（仮想リスト等）が主題のとき

## 手順

### 1. 課題を分類する

ユーザーの要求を次の分岐に当てはめる。迷ったら **Step 4** の即決表を先に当てる。

```
何を実現したい？
│
├─ 要素を中央に配置したい
│   ├─ 単一要素 → Super Centered または Autobot
│   ├─ 複数要素を縦に → Gentle Flex
│   ├─ グループ全体を → Content Center
│   └─ オーバーレイ／モーダル → Pop n' Plop
│
├─ レスポンシブなグリッド／カード配置
│   ├─ メディアクエリなしで列を組む → RAM
│   ├─ 折り返して縦に積む → Deconstructed Pancake
│   └─ コンテナ幅に応じてスタイルを切る → Container Query
│
├─ ページ全体の骨格
│   ├─ Header + Main + Footer → Pancake Stack
│   └─ サイドバー込みの定番グリッド → Holy Grail
│
└─ サイズを制御したい
    ├─ 幅の最小・最大・希望値 → Clamping（clamp）
    └─ 縦横比を固定 → Aspect Ratio
```

### 2. 詳細を読み込む

分類結果に応じて、次の **いずれかだけ** を読む（トークン節約のため一ファイルずつ）。

| 分類 | 読むファイル |
|------|----------------|
| 中央配置 | `references/centering.md` |
| レスポンシブ | `references/responsive.md` |
| ページ構造 | `references/page-structure.md` |
| コンポーネント寸法 | `references/component.md` |

### 3. 実装する

1. 参照ファイル内の **When**（適用条件）が今回の要件と一致することを確認する。
2. **核心コード**をそのまままたは変数名・寸法だけ差し替えて適用する。
3. 同ファイルの **Gotchas**（注意点）をすべて確認する。

### 4. 即決表（迷い回避）

| やりたいこと | 最初に試すパターン |
|-------------|-------------------|
| とにかく中央に置きたい | Super Centered（`place-items: center`） |
| カードを並べたい | RAM（`repeat(auto-fit, minmax(...))`） |
| フッターを下に固定したい | Pancake Stack（`grid-template-rows: auto 1fr auto`） |
| 幅を柔軟に制限したい | Clamping（`clamp(min, preferred, max)`） |

### 5. 検証する

1. `references/antipatterns.md` に該当する実装になっていないか確認する。
2. 用語や一覧の突合が必要なら `references/quick-reference.md` を開く。
3. 具体例が欲しい場合のみ `references/examples.md` を読む。

## 参照ファイル一覧

- `references/centering.md` — 中央配置パターン（5種）
- `references/responsive.md` — レスポンシブパターン（4種）
- `references/page-structure.md` — ページ構造パターン（2種）
- `references/component.md` — コンポーネント寸法（1種）
- `references/quick-reference.md` — 全パターン早見表
- `references/antipatterns.md` — 避けるべき実装
- `references/examples.md` — 実装例

## エラーハンドリング

- **どのパターンにも当てはまらない**: `references/quick-reference.md` の表で最も近い行を選び、そのパターンの詳細ファイルを読む。
- **パターンは決まったがコードがブラウザで崩れる**: `references/antipatterns.md` と該当パターンの Gotchas を再確認する。親の `display`／`min-height`／`overflow` が前提を壊していないか見る。
- **フロントマター（name / description）を変更したとき**: リポジトリの skills ルートで次を実行し、成功まで文言を直す。

```bash
python3 skill-creator/scripts/validate-metadata.py --name "css-layout" --description "[新しい説明文]"
```

- **スキル構造の監査**: `skill-creator/references/checklist.md` の各項目に照らして差し戻し原因を特定する。

## メタデータ検証（開発者向け）

`description` を更新する場合は、必ず上記 `validate-metadata.py` を通す。三人称・1024文字以内・名前とディレクトリ名 `css-layout` の一致を満たす。
