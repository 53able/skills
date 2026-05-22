# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI に対応。
Cursor / Claude Code / Codex など 40 以上のエージェントで使用できる。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。

## 執筆・発信

フィード型の Web 長文を、クリックから読了まで設計するスキル。

- **readable-writing-workflow** — 「届けるまでが仕事」としてタイトル比重・読者メリット・圧縮・寝かせ・インプット／リサーチ／構成の配分を手順化する（一次エッセイ由来の要旨を `references/mindset-and-tactics.md` に整理）。
- **zenn-markdown** — Zenn Flavored Markdown の記法（message/details、埋め込み、mermaid 制限、KaTeX 等）を適用して記事・スクラップ・本の原稿を執筆・校正する。

## 動画生成

ミーティングや議事録からエクスプレイナービデオを自動生成するスキル。

- **meeting-to-video** — ミーティングのトランスクリプトから Remotion ストーリー型ビデオプロジェクトを生成する。`npx remotion preview` でローカルプレビューできる状態まで自動構築する。ElevenLabs / OpenAI TTS によるボイスオーバー生成にも対応。

## エージェント・LLM 基盤

コーディングエージェントの拡張と、本番向け LLM アプリケーション設計のスキル。

- **pi-agent-harness** — [Pi Agent Harness](https://github.com/earendil-works/pi) の開発・拡張。CLI、Extension、SDK 組み込み、セッション管理、マルチプロバイダ LLM 設定をカバーする。
- **reliable-llm-app-principles** — 12-Factor Agents を基に LLM アプリの設計・レビュー・改善を行う。プロンプト境界、構造化出力、状態管理、人間承認、監査可能性を手順化する。

## インストール

このリポジトリを GitHub に public で公開後、以下のコマンドでインストールできる。

```bash
# 全スキルをインストール
npx skills add 53able/skills

# 特定のスキルだけインストール
npx skills add 53able/skills --skill thinking-ensemble
npx skills add 53able/skills --skill meeting-to-video
npx skills add 53able/skills --skill readable-writing-workflow
npx skills add 53able/skills --skill zenn-markdown
npx skills add 53able/skills --skill pi-agent-harness
npx skills add 53able/skills --skill reliable-llm-app-principles

# Cursor 向けにグローバルインストール
npx skills add 53able/skills --skill thinking-ensemble -g -a cursor
npx skills add 53able/skills --skill meeting-to-video -g -a cursor
npx skills add 53able/skills --skill readable-writing-workflow -g -a cursor
npx skills add 53able/skills --skill zenn-markdown -g -a cursor
npx skills add 53able/skills --skill pi-agent-harness -g -a cursor
npx skills add 53able/skills --skill reliable-llm-app-principles -g -a cursor
```

サブディレクトリだけ指定する場合:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
npx skills add https://github.com/53able/skills/tree/main/skills/readable-writing-workflow -g
npx skills add https://github.com/53able/skills/tree/main/skills/zenn-markdown -g
npx skills add https://github.com/53able/skills/tree/main/skills/pi-agent-harness -g
npx skills add https://github.com/53able/skills/tree/main/skills/reliable-llm-app-principles -g
```

## スキル構成

各スキルは `skills/<skill-name>/` に配置する。

```
skills/<skill-name>/
├── SKILL.md          # スキル本体（各エージェントが読み込む）
└── *.md              # スキルに同梱するサポートファイル（任意）
```

エージェント向けのリポジトリ運用メモは [AGENTS.md](./AGENTS.md) を参照。
