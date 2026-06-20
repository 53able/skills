# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI に対応。
Cursor / Claude Code / Codex など 40 以上のエージェントで使用できる。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。
- **decision-matrix** — 複数の選択肢を重み付き評価項目で定量的・客観的に比較する意思決定マトリクスを作成する。CSV/JSON 入力から加重合計を算出する `scripts/score_matrix.py` を同梱。

## 執筆・発信

フィード型の Web 長文を、クリックから読了まで設計するスキル。

- **readable-writing-workflow** — 「届けるまでが仕事」としてタイトル比重・読者メリット・圧縮・寝かせ・インプット／リサーチ／構成の配分を手順化する（一次エッセイ由来の要旨を `references/mindset-and-tactics.md` に整理）。
- **nihongo-skeleton-writing** — 単語・文・段落・縮約・敬語の観点で日本語文章の骨格を磨く。改稿チェックリストと段落ラベル用スクリプトを同梱。
- **tech-article-angle** — 技術記事のアイデアや草稿を、現在需要の高い論点へ寄せてテーマ・タイトル・構成を整える。需要モデルと角度スコア用スクリプトを同梱。
- **zenn-markdown** — Zenn Flavored Markdown の記法（message/details、埋め込み、mermaid 制限、KaTeX 等）を適用して記事・スクラップ・本の原稿を執筆・校正する。

## プレゼンテーション

聞き手中心のトーク設計とスライド監査のスキル。

- **presentation-zen-garr-reynolds** — ガー・レイノルズの Presentation Zen 原則でブリーフ作成、スライド構成、slideument 分離、デリバリー指導、Markdown 下書き監査（`scripts/audit-presentation.py`）を手順化する。

## 動画生成

ミーティングや議事録からエクスプレイナービデオを自動生成するスキル。

- **meeting-to-video** — ミーティングのトランスクリプトから Remotion ストーリー型ビデオプロジェクトを生成する。`npx remotion preview` でローカルプレビューできる状態まで自動構築する。ElevenLabs / OpenAI TTS によるボイスオーバー生成にも対応。

## 命名

ファイル・スラッグ・短い技術成果物の英語名を、意図から候補化して形式整形するスキル。

- **naming-skill** — 日本語または英語の意図から最大4語の英語名候補を作り、kebab-case / snake_case / camelCase / PascalCase など change-case 由来の形式へ整形する。`scripts/format_name.py` を同梱。

## デスクトップアプリ

ウェブ URL をネイティブデスクトップアプリに変換するスキル。

- **pake-app-builder** — Pake（Tauri v2）でウェブ URL を macOS / Windows / Linux 向けスタンドアロンアプリ（約 5 MB）にパッケージする。`scripts/check-env.sh` を同梱。

## ブラウザ拡張

WXT を使ったブラウザ拡張の設計・実装・検証を支援するスキル。

- **wxt-extension-development** — WXT プロジェクトの調査、entrypoint 設計、manifest と権限変更、content script UI、storage、messaging、build、zip、ブラウザ検証を手順化する。`scripts/inspect-wxt-project.py` を同梱。

## 開発ワークフロー

実装プランの品質担保・PR・コミットなど、着手前後の手順をエージェントに載せるスキル。

- **self-refine** — プラン実行前に Multi-Aspect 評価（目的整合性・影響範囲・前提妥当性・実行可能性・認知負荷）でセルフリファインし、全次元 OK になってから実行する。「実行して」「進めて」「go」の直前に使用。
- **context-to-gantt** — 議事録・要件・タスクリストなどのコンテキストからタスクと期間を抽出し、Kibo UI スタイルのガントチャートを単一 HTML で生成する。ビルド不要でブラウザ共有できる。

## ドキュメント・変換

LLM 投入前にローカル文書を扱いやすい形式へ変換するスキル。

- **pdf-markdown-local** — ローカル PDF を Microsoft MarkItDown と uv で Markdown へ変換し、トークン効率よく LLM に渡す。`scripts/convert_pdf.py` を同梱。

## エージェント・LLM 基盤

コーディングエージェントの拡張と、本番向け LLM アプリケーション設計のスキル。

- **pi-agent-harness** — [Pi Agent Harness](https://github.com/earendil-works/pi) の開発・拡張。CLI、Extension、SDK 組み込み、セッション管理、マルチプロバイダ LLM 設定をカバーする。
- **reliable-llm-app-principles** — 12-Factor Agents を基に LLM アプリの設計・レビュー・改善を行う。プロンプト境界、構造化出力、状態管理、人間承認、監査可能性を手順化する。

## コードベース再実装

仕様未整備のレガシー機能を、観察とプリミティブ分解を経て外科的に再実装するスキル。

- **primitive-reimpl** — 既存コードから振る舞いと推定仕様を抽出し、プリミティブ能力へ分解して必要な部分だけ新モジュールとして再実装する。仕様マップ検証スクリプトとテンプレートを同梱。

## インストール

このリポジトリを GitHub に public で公開後、以下のコマンドでインストールできる。

```bash
# 全スキルをインストール
npx skills add 53able/skills

# 特定のスキルだけインストール
npx skills add 53able/skills --skill thinking-ensemble
npx skills add 53able/skills --skill meeting-to-video
npx skills add 53able/skills --skill readable-writing-workflow
npx skills add 53able/skills --skill nihongo-skeleton-writing
npx skills add 53able/skills --skill tech-article-angle
npx skills add 53able/skills --skill zenn-markdown
npx skills add 53able/skills --skill pi-agent-harness
npx skills add 53able/skills --skill reliable-llm-app-principles
npx skills add 53able/skills --skill self-refine
npx skills add 53able/skills --skill primitive-reimpl
npx skills add 53able/skills --skill context-to-gantt
npx skills add 53able/skills --skill presentation-zen-garr-reynolds
npx skills add 53able/skills --skill decision-matrix
npx skills add 53able/skills --skill pdf-markdown-local
npx skills add 53able/skills --skill naming-skill
npx skills add 53able/skills --skill pake-app-builder
npx skills add 53able/skills --skill wxt-extension-development

# Cursor 向けにグローバルインストール
npx skills add 53able/skills --skill thinking-ensemble -g -a cursor
npx skills add 53able/skills --skill meeting-to-video -g -a cursor
npx skills add 53able/skills --skill readable-writing-workflow -g -a cursor
npx skills add 53able/skills --skill nihongo-skeleton-writing -g -a cursor
npx skills add 53able/skills --skill tech-article-angle -g -a cursor
npx skills add 53able/skills --skill zenn-markdown -g -a cursor
npx skills add 53able/skills --skill pi-agent-harness -g -a cursor
npx skills add 53able/skills --skill reliable-llm-app-principles -g -a cursor
npx skills add 53able/skills --skill self-refine -g -a cursor
npx skills add 53able/skills --skill primitive-reimpl -g -a cursor
npx skills add 53able/skills --skill context-to-gantt -g -a cursor
npx skills add 53able/skills --skill presentation-zen-garr-reynolds -g -a cursor
npx skills add 53able/skills --skill decision-matrix -g -a cursor
npx skills add 53able/skills --skill pdf-markdown-local -g -a cursor
npx skills add 53able/skills --skill naming-skill -g -a cursor
npx skills add 53able/skills --skill pake-app-builder -g -a cursor
npx skills add 53able/skills --skill wxt-extension-development -g -a cursor
```

サブディレクトリだけ指定する場合:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
npx skills add https://github.com/53able/skills/tree/main/skills/readable-writing-workflow -g
npx skills add https://github.com/53able/skills/tree/main/skills/nihongo-skeleton-writing -g
npx skills add https://github.com/53able/skills/tree/main/skills/tech-article-angle -g
npx skills add https://github.com/53able/skills/tree/main/skills/zenn-markdown -g
npx skills add https://github.com/53able/skills/tree/main/skills/pi-agent-harness -g
npx skills add https://github.com/53able/skills/tree/main/skills/reliable-llm-app-principles -g
npx skills add https://github.com/53able/skills/tree/main/skills/self-refine -g
npx skills add https://github.com/53able/skills/tree/main/skills/primitive-reimpl -g
npx skills add https://github.com/53able/skills/tree/main/skills/context-to-gantt -g
npx skills add https://github.com/53able/skills/tree/main/skills/presentation-zen-garr-reynolds -g
npx skills add https://github.com/53able/skills/tree/main/skills/decision-matrix -g
npx skills add https://github.com/53able/skills/tree/main/skills/pdf-markdown-local -g
npx skills add https://github.com/53able/skills/tree/main/skills/naming-skill -g
npx skills add https://github.com/53able/skills/tree/main/skills/pake-app-builder -g
npx skills add https://github.com/53able/skills/tree/main/skills/wxt-extension-development -g
```

## スキル構成

各スキルは `skills/<skill-name>/` に配置する。

```
skills/<skill-name>/
├── SKILL.md          # スキル本体（各エージェントが読み込む）
└── *.md              # スキルに同梱するサポートファイル（任意）
```

エージェント向けのリポジトリ運用メモは [AGENTS.md](./AGENTS.md) を参照。
