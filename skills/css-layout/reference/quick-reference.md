# クイックリファレンス

## 全パターン早見表

| 課題 | 推奨パターン | 核心コード |
|------|-------------|-----------|
| 要素を完全に中央配置したい | Super Centered | `display: grid; place-items: center;` |
| 単一要素を素早く中央配置 | Autobot | `display: flex;` + 子に `margin: auto;` |
| 複数要素を縦に中央揃え | Gentle Flex | `display: flex; flex-direction: column; align-items: center; justify-content: center;` |
| グループ全体を中央配置 | Content Center | `display: grid; place-content: center;` |
| モーダル/オーバーレイの中央配置 | Pop n' Plop | `position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);` |
| メディアクエリなしでレスポンシブグリッド | RAM | `grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));` |
| 自動折り返しのカード列 | Deconstructed Pancake | `display: flex; flex-wrap: wrap;` + 子に `flex: 1 1 150px;` |
| 最小・最大幅を制限したい | Clamping | `width: clamp(23ch, 60%, 46ch);` |
| コンテナサイズに応じたスタイル変更 | Container Query | `container: inline-size;` + `@container` |
| スティッキーフッター | Pancake Stack | `grid-template-rows: auto 1fr auto;` |
| ヘッダー+サイドバー+メイン+フッター | Holy Grail | `grid-template: auto 1fr auto / auto 1fr auto;` |
| アスペクト比を維持した画像/動画 | Aspect Ratio | `aspect-ratio: 16 / 9;` |

## パターン分類

### 中央配置（5種）
- Super Centered
- Autobot
- Gentle Flex
- Content Center
- Pop n' Plop

### レスポンシブ（4種）
- RAM
- Deconstructed Pancake
- Clamping
- Container Query

### ページ構造（2種）
- Pancake Stack
- Holy Grail

### コンポーネント（1種）
- Aspect Ratio
