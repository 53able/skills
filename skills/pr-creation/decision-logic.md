# 決定ロジック

## ベースブランチ決定

以下の優先順位でベースブランチを決定する：

| パターン | ベースブランチ | 例 |
|----------|---------------|---|
| `feature/{codename}/00-*` | `main` | 最初のブランチ |
| `feature/{codename}/{NN}-*` (NN > 00) | `feature/{codename}/{NN-1}-*` | 前の連番ブランチ |
| `fix/*` | `main` | |
| `hotfix/*` | `main` | |
| その他 | `main` | デフォルト |

### 命名規則で判断できない場合

```bash
git log --oneline --first-parent -10  # 分岐元を確認
```

## 依存PR確認

```bash
gh pr list --base <ベースブランチ> --state open --json number,title,headRefName
```

### 判断基準

| 状態 | 判断 | アクション |
|------|------|------------|
| 依存PRあり | 関連付け | 本文に `Depends on #<PR番号>` を追加 |
| 依存PRなし | スキップ | 次のステップへ |
| 確認不可 | 警告 | ユーザーに確認を求める |

## 実行例

### 例1: 基本的なPR作成（連番00 → mainベース）

**状況**: `feature/login/00-ddocs` ブランチで作業中、mainにマージしたい

```bash
$ git branch --show-current
feature/login/00-ddocs

# ベースブランチ: main（連番00なので）
# タイトル: [login] PR-00: Design Doc作成
```

### 例2: 依存PRがある場合（連番01 → 前の連番ベース）

**状況**: `feature/login/01-oauth` が `feature/login/00-ddocs`（PR #42）に依存

```bash
$ git branch --show-current
feature/login/01-oauth

$ gh pr list --base feature/login/00-ddocs --state open --json number,title
[{"number":42,"title":"[login] PR-00: Design Doc作成"}]

# ベースブランチ: feature/login/00-ddocs（連番01なので前の連番）
# タイトル: [login] PR-01: OAuth認証追加
# 本文に追加: Depends on #42
```

## 複雑なケースの判断

以下の場合は `pr-manager` サブエージェントに委譲：

| ケース | 理由 |
|--------|------|
| 連番01以降 | 前の連番ブランチの特定が必要 |
| 複数パッケージ跨り | 依存関係の分析が必要 |
| ブランチ命名が非標準 | 分岐元の調査が必要 |
