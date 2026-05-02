# サブエージェントプロンプト: Design Docs理解

> `explore` サブエージェントに委譲する際のプロンプトテンプレート

## 使用タイミング

- Phase 1: Understand で Design Docs が大規模な時
- コードベースの影響範囲調査が必要な時

## プロンプトテンプレート

```markdown
## タスク: Design Docs理解とスコープ特定

### 目的
Design Docsを精読し、実装スコープを特定する

### 調査対象
- Design Docs: [ファイルパス]
- 関連ディレクトリ: [影響が予想されるパッケージ]
- 関連キーワード: [検索キーワード]

### 調査項目

#### 1. Design Docs要約
以下の観点で要約を作成:
- 背景・課題: なぜこの機能が必要か
- ゴール: 何を達成しようとしているか
- 主要概念: 登場する概念・用語
- 技術的決定: 設計判断とその理由

#### 2. 実装スコープ特定
- IN SCOPE: 今回実装する範囲
- OUT OF SCOPE: 今回実装しない範囲
- 変更対象パッケージ: どのパッケージが影響を受けるか
- 新規作成ファイル: 何を新規作成するか

#### 3. 既存コードとの関連
- 影響を受ける既存ファイル
- 参考にすべき既存実装パターン
- 潜在的な競合・注意点

### 出力形式

#### Design Docs要約
| 項目 | 内容 |
|---|---|
| 背景・課題 | [記述] |
| ゴール | [記述] |
| 主要概念 | [概念1], [概念2], ... |
| 技術的決定 | [決定1]: [理由] |

#### 実装スコープ
| カテゴリ | 内容 |
|---|---|
| IN SCOPE | [機能1], [機能2] |
| OUT OF SCOPE | [機能1], [機能2] |
| 変更対象 | `packages/xxx`, `packages/yyy` |
| 新規作成 | `path/to/file.ts` |

#### 関連ファイル一覧
- [ファイルパス]: [役割・関連性]

### 調査の深さ
- thoroughness: "medium"（または "quick" / "very thorough"）
```

## 使用例

### 例1: 新機能のDesign Docs理解

```markdown
## タスク: Design Docs理解とスコープ特定

### 目的
アプローチプラン機能の新規実装に向けて、Design Docsを理解する

### 調査対象
- Design Docs: docs/design/approach-plan-v2.md
- 関連ディレクトリ: packages/scheduler/, packages/common/
- 関連キーワード: approachPlan, schedule, campaign

### 調査項目
[上記テンプレートの項目]

### 調査の深さ
- thoroughness: "very thorough"
```

## 注意事項

- サブエージェントの結果は必ず検証する
- Design Docsの原文を根拠として含めるよう指示する
- コードベースの探索結果も併せて報告させる
