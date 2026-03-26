# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI に対応。
Cursor / Claude Code / Codex など 40 以上のエージェントで使用できる。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。

## 動画生成

ミーティングや議事録からエクスプレイナービデオを自動生成するスキル。

- **meeting-to-video** — ミーティングのトランスクリプトから Remotion ストーリー型ビデオプロジェクトを生成する。`npx remotion preview` でローカルプレビューできる状態まで自動構築する。ElevenLabs / OpenAI TTS によるボイスオーバー生成にも対応。

## インストール

このリポジトリを GitHub に public で公開後、以下のコマンドでインストールできる。

```bash
# 全スキルをインストール
npx skills add 53able/skills

# 特定のスキルだけインストール
npx skills add 53able/skills --skill thinking-ensemble
npx skills add 53able/skills --skill meeting-to-video

# Cursor 向けにグローバルインストール
npx skills add 53able/skills --skill thinking-ensemble -g -a cursor
npx skills add 53able/skills --skill meeting-to-video -g -a cursor
```

サブディレクトリだけ指定する場合:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
```

## スキル構成

各スキルは `skills/<skill-name>/` に配置する。

```
skills/<skill-name>/
├── SKILL.md          # スキル本体（各エージェントが読み込む）
└── *.md              # スキルに同梱するサポートファイル（任意）
```

エージェント向けのリポジトリ運用メモは [AGENTS.md](./AGENTS.md) を参照。
