# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI に対応。
Cursor / Claude Code / Codex など 40 以上のエージェントで使用できる。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。

## インストール

このリポジトリを GitHub に public で公開後、以下のコマンドでインストールできる。

```bash
# 全スキルをインストール
npx skills add 53able/skills

# 特定のスキルだけインストール
npx skills add 53able/skills --skill thinking-ensemble

# Cursor 向けにグローバルインストール
npx skills add 53able/skills --skill thinking-ensemble -g -a cursor
```

## スキル構成

各スキルは独自のディレクトリに格納。

```
<skill-name>/
├── SKILL.md          # スキル本体（各エージェントが読み込む）
└── *.md              # スキルに同梱するサポートファイル
```
