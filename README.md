# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。

```
npx skills@latest add oreore/skills/thinking-ensemble
```

## インストール

```bash
# スキルを個別にインストール
npx skills@latest add oreore/skills/<skill-name>
```

## スキル構成

各スキルは独自のディレクトリに格納。

```
<skill-name>/
├── SKILL.md          # スキル本体（Cursor が読み込む）
└── *.md              # スキルに同梱するサポートファイル
```

スキルは [Cursor](https://cursor.com) 向けに設計され、Agent Skills フォーマットに準拠。
