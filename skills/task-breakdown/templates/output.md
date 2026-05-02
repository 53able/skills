# 最終出力テンプレート

> Design Docsに追記するタスクブレイクダウン情報の形式

## テンプレート

```markdown
## タスクブレイクダウン

### タスク一覧

| # | タスク名 | 概要 | 見積もり | 先行タスク | ブランチ |
|---|-----|-----|-----|-----|-----|
| T0 | Design Docs PR | タスクブレイクダウン情報の追加 | S | - | `feature/xxx/00-design-docs` |
| T1 | [名前] | [概要] | [S/M/L] | T0 | `feature/xxx/01-modifier` |
| T2 | [名前] | [概要] | [S/M/L] | T1 | `feature/xxx/02-modifier` |
| T3 | [名前] | [概要] | [S/M/L] | T2 | `feature/xxx/03-modifier` |

### 依存関係図（スタック方式）

graph LR
    T0[Design Docs PR] --> T1
    T1 --> T2
    T2 --> T3

### ブランチ戦略

| ブランチ | 親 | マージ順 | 備考 |
|-----|---|-----|-----|
| `feature/xxx/00-design-docs` | `main` | 0 | Design Docs PR（設計レビュー用） |
| `feature/xxx/01-modifier` | `/00-design-docs` | 1 | |
| `feature/xxx/02-modifier` | `/01-modifier` | 2 | |
| `feature/xxx/03-modifier` | `/02-modifier` | 3 | |

> **整合性チェック**: 先行タスクとブランチの親が一致していることを確認
> - T1の先行タスク: T0 → `/01-modifier`の親: `/00-design-docs` ✅
> - T2の先行タスク: T1 → `/02-modifier`の親: `/01-modifier` ✅
> - T3の先行タスク: T2 → `/03-modifier`の親: `/02-modifier` ✅

### 見積もりサマリー

- 総タスク数: N
- S（小）: X件
- M（中）: Y件
- L（大）: Z件
```

## 見積もり基準

| サイズ | 目安時間 | PR差分目安 | 例 |
|---|---|---|---|
| S（小） | 1-2時間 | ~100行 | 型定義追加、単純なユーティリティ |
| M（中） | 半日 | 100-200行 | API実装、コンポーネント作成 |
| L（大） | 1日 | 200-300行 | 複雑なロジック、大きなリファクタ |

## 命名規則

### codename
- Design Docsの主題を象徴する識別子
- 4単語以内
- ケバブケース
- 例: `approach-plan-bulk`, `campaign-settings`, `user-auth-v2`

### modifier
- タスク内容を示す短い修飾語
- 4単語以内
- ケバブケース
- 例: `schema`, `api-endpoint`, `list-ui`, `detail-modal`

## 使用時の注意

1. **Mermaid図のエスケープ**: 特殊文字（`[]`, `{}`, `<>`等）は適切にエスケープ
2. **ブランチ名の省略**: 表中では `/00-design-docs` のように省略形を使用可
3. **整合性チェックの記載**: 必ず確認結果を明記
