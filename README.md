# Agent Skills

構造化思考・多角的分析・開発ワークフローのためのエージェントスキル集。

[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI に対応。
Cursor / Claude Code / Codex など 40 以上のエージェントで使用できる。

## 思考・分析

意思決定や問題解決に認知フレームワークを適用するスキル。

- **thinking-ensemble** — 16の MBTI 認知レンズを NT / NF / SJ / SP の4グループに分け、全グループを並列サブエージェントとして同時起動。タスク重みづけ統合で認知的多様性を最大化する。
- **decision-matrix** — 複数の選択肢を重み付き評価項目で定量的・客観的に比較する意思決定マトリクスを作成する。CSV/JSON 入力から加重合計を算出する `scripts/score_matrix.py` を同梱。
- **thinking-logical** — 論点設定→情報収集→解釈→構造化の順で進めるロジカルシンキングの推論プロトコル。
- **thinking-mece** — MECE（相互排他・全体網羅）の2条件で目的に対する切り口を決め、漏れとダブりをチェックする分解プロトコル。
- **thinking-deduction** — 大前提（一般論）と小前提（具体事実）から必然的結論を導く演繹的思考プロトコル。
- **thinking-induction** — 複数サンプルから共通点を抽出し一般化する帰納法的思考プロトコル。
- **thinking-abduction** — 驚くべき事実から説明仮説を形成し検証する、アブダクション（仮説形成）の推論プロトコル。
- **thinking-pac** — 前提(P)・仮定(A)・結論(C) に分解し、結論と前提をつなぐ暗黙の仮定を疑うPAC思考プロトコル。
- **thinking-critical** — 論点・前提・飛躍の3点を疑うクリティカルシンキング（批判的思考）の論理検証プロトコル。
- **thinking-debate** — 賛否が分かれる論題を立て、賛成/反対の往復から争点を顕在化させるディベート思考プロトコル。
- **thinking-meta** — 対象レベルとメタレベルを往復し、考え方そのものを振り返るメタ思考プロトコル。
- **jobs-theory-innovation** — ジョブ理論（Jobs-to-be-Done）に基づき、構造化されたメモリと6つの分析レンズ、Chain-of-Thoughtで顧客の真のジョブを探索しイノベーション機会を特定する。

## 執筆・発信

フィード型の Web 長文を、クリックから読了まで設計するスキル。

- **readable-writing-workflow** — 「届けるまでが仕事」としてタイトル比重・読者メリット・圧縮・寝かせ・インプット／リサーチ／構成の配分を手順化する（一次エッセイ由来の要旨を `references/mindset-and-tactics.md` に整理）。
- **nihongo-skeleton-writing** — 単語・文・段落・縮約・敬語の観点で日本語文章の骨格を磨く。改稿チェックリストと段落ラベル用スクリプトを同梱。
- **tech-article-angle** — 技術記事のアイデアや草稿を、現在需要の高い論点へ寄せてテーマ・タイトル・構成を整える。需要モデルと角度スコア用スクリプトを同梱。
- **zenn-markdown** — Zenn Flavored Markdown の記法（message/details、埋め込み、mermaid 制限、KaTeX 等）を適用して記事・スクラップ・本の原稿を執筆・校正する。
- **natural-expression-refiner** — 誇張・借り物の美辞麗句・過剰な謙遜を避け、実感に近い等身大な表現へ日本語文章を整える。過大化を検出する `scripts/flag-overstatement.py` を同梱。
- **sentence-logic-guard** — 文と文のつながりを点検し、直前の文が残した不足を次の文が補っているかを読者視点で確認する。文ペア抽出用の `scripts/sentence_pairs.py` を同梱。
- **logical-consistency-reviewer** — Why So / So What / MECE の観点で文章・記事・レポート・企画書の論点飛躍・矛盾・根拠不足を検出する。
- **chuuni-refiner** — 日本語文章を意図を保ったまま指定の厨二レベル（low/medium/high/max）へ、暗黒ファンタジー的な大仰さと特別な存在感を加えて変換する。レベル別の強度を決める `scripts/level-guide.py` を同梱。

## プレゼンテーション

聞き手中心のトーク設計とスライド監査のスキル。

- **presentation-zen-garr-reynolds** — ガー・レイノルズの Presentation Zen 原則でブリーフ作成、スライド構成、slideument 分離、デリバリー指導、Markdown 下書き監査（`scripts/audit-presentation.py`）を手順化する。

## 図解・ビジュアル

テキストから概念図解を組み立てるスキル。

- **zukai-creator** — テキスト・メモ・記事・スライド・説明文から要素・関係性・グループ・ラベルを抽出し、図解パターンとスタイリングルールを選んでわかりやすい日本語の概念図解を作る。図解ブリーフの妥当性を確認する `scripts/check-diagram-brief.py` を同梱。

## 動画生成

ミーティングや議事録からエクスプレイナービデオを自動生成するスキル。

- **meeting-to-video** — ミーティングのトランスクリプトから Remotion ストーリー型ビデオプロジェクトを生成する。`npx remotion preview` でローカルプレビューできる状態まで自動構築する。ElevenLabs / OpenAI TTS によるボイスオーバー生成にも対応。

## 命名

ファイル・スラッグ・短い技術成果物の英語名を、意図から候補化して形式整形するスキル。

- **naming-skill** — 日本語または英語の意図から最大4語の英語名候補を作り、kebab-case / snake_case / camelCase / PascalCase など change-case 由来の形式へ整形する。`scripts/format_name.py` を同梱。

## デスクトップアプリ

ウェブ URL をネイティブデスクトップアプリに変換するスキル。

- **pake-app-builder** — Pake（Tauri v2）でウェブ URL を macOS / Windows / Linux 向けスタンドアロンアプリ（約 5 MB）にパッケージする。`scripts/check-env.sh` を同梱。

## OS操作・キャプチャ

macOS 上でエージェントが再現可能な形で画面を扱うスキル。

- **macos-screenshot-capture** — `screencapture` と補助 CLI で、画面全体・ウィンドウ指定・選択範囲・タイマー撮影・クリップボード保存に対応した macOS のスクリーンショットを取得する。`scripts/capture_macos_screenshot.py` を同梱。

## フロントエンド実装

CSS のレイアウト課題を名前付きパターンへ落とし込むスキル。

- **css-layout** — CSS のレイアウト課題に対し、中央配置・レスポンシブグリッド・ページ骨格・サイズ制御のパターンを選定し適用する。Flexbox、Grid、clamp、aspect-ratio、コンテナクエリを扱う。

## ブラウザ拡張

WXT を使ったブラウザ拡張の設計・実装・検証を支援するスキル。

- **wxt-extension-development** — WXT プロジェクトの調査、entrypoint 設計、manifest と権限変更、content script UI、storage、messaging、build、zip、ブラウザ検証を手順化する。`scripts/inspect-wxt-project.py` を同梱。

## 開発ワークフロー

実装プランの品質担保・コードリーディング・コミット・PR など、着手前後の手順をエージェントに載せるスキル。

- **self-refine** — プラン実行前に Multi-Aspect 評価（目的整合性・影響範囲・前提妥当性・実行可能性・認知負荷）でセルフリファインし、全次元 OK になってから実行する。「実行して」「進めて」「go」の直前に使用。
- **context-to-gantt** — 議事録・要件・タスクリストなどのコンテキストからタスクと期間を抽出し、Kibo UI スタイルのガントチャートを単一 HTML で生成する。ビルド不要でブラウザ共有できる。
- **code-reading** — コードリーディングを取得・処理・管理の3層フレームワークで効率的に実行する。実装をむやみに精読せず、インターフェイスと役割の理解に読む箇所を絞る。複雑なケースではサブエージェント起動を推奨。
- **cognitive-load-minimizer** — コードレビュー・リファクタ・アーキ判断・機能実装で、避けられる認知負荷（浅い抽象、技巧的条件分岐、早すぎるレイヤー化、フレームワーク密結合、誤解を招くドメインモデル）を特定して削る。認知負荷スコアを算出する `scripts/score-cognitive-load.py` を同梱。
- **task-breakdown** — Design Docs を精読し、実装可能なタスクに分解して、ブランチ戦略を策定する。
- **tdd-from-design-docs** — Design Docs から指定された範囲を、失敗するテストを先に書く TDD（Red/Green/Refactor）ワークフローで実装する。Design Docs がない場合はコードベース・ユーザー入力から要件を代替収集する。
- **commit-diffs** — 現在の差分を分析し、「1コミット＝1つの論理的変更」の原則で最適な粒度にコミットを分割・実行する。単純なケースはスキル内で完結し、複雑なケースは commit-manager サブエージェントへ委譲する。
- **git-commit-granularity** — Git コミットの粒度ベストプラクティスに従い、`git add -p` によるハンクステージングでアトミックで単一概念のコミットへ分割・整形するガイドを提供する。
- **pr-creation** — `gh` コマンドでドラフト PR を作成する。レビュアーが読みたくなる説明を作ることを重視する。単純なケースはスキル内で完結し、複雑なケースは pr-manager サブエージェントへ委譲する。
- **pr-conflict-resolve** — ローカル CLI（git / gh）を使って GitHub PR のコンフリクトを解消する。merge vs rebase の戦略選択、コンフリクトマーカーの解消、安全な復旧手順、プッシュ後の PR 確認チェックリストまでをガイドする。
- **pr-evidence-capture** — UI 変更や状態遷移を伴う PR に、E2E テスト計画・操作後スクリーンショット・検証結果を確認エビデンスとして残す。`gh` で画像をアップロードし、Chrome DevTools MCP で画面を操作・撮影し、PR コメントへ投稿する。

## セキュリティ・プライバシー

画像や文書を公開・共有・LLM投入する前に機密情報を除去するスキル。

- **image-pii-masking** — 画像内の文字として写り込んだ氏名・住所・電話番号・APIキー等を OCR(Tesseract)と Presidio、日本語向け正規表現で検出し、不透明な塗りつぶし・再OCR検証・EXIF除去まで実行する。`scripts/mask_image.py` と `scripts/selftest.py` を同梱。

## ドキュメント・変換

LLM 投入前にローカル文書を扱いやすい形式へ変換するスキル。

- **pdf-markdown-local** — ローカル PDF を Microsoft MarkItDown と uv で Markdown へ変換し、トークン効率よく LLM に渡す。`scripts/convert_pdf.py` を同梱。
- **csv-llm-edit** — CSV ファイルを Python で編集し、表形式データをトークン効率のよい TOON 形式へ変換して LLM に渡す。TOON は JSON 比で 30〜60% のトークン削減が見込める。`scripts/edit_csv.py` / `scripts/csv_to_toon.py` / `scripts/toon_to_csv.py` を同梱。

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
npx skills add 53able/skills --skill decision-matrix
npx skills add 53able/skills --skill thinking-logical
npx skills add 53able/skills --skill thinking-mece
npx skills add 53able/skills --skill thinking-deduction
npx skills add 53able/skills --skill thinking-induction
npx skills add 53able/skills --skill thinking-abduction
npx skills add 53able/skills --skill thinking-pac
npx skills add 53able/skills --skill thinking-critical
npx skills add 53able/skills --skill thinking-debate
npx skills add 53able/skills --skill thinking-meta
npx skills add 53able/skills --skill jobs-theory-innovation
npx skills add 53able/skills --skill readable-writing-workflow
npx skills add 53able/skills --skill nihongo-skeleton-writing
npx skills add 53able/skills --skill tech-article-angle
npx skills add 53able/skills --skill zenn-markdown
npx skills add 53able/skills --skill natural-expression-refiner
npx skills add 53able/skills --skill sentence-logic-guard
npx skills add 53able/skills --skill logical-consistency-reviewer
npx skills add 53able/skills --skill chuuni-refiner
npx skills add 53able/skills --skill presentation-zen-garr-reynolds
npx skills add 53able/skills --skill zukai-creator
npx skills add 53able/skills --skill meeting-to-video
npx skills add 53able/skills --skill naming-skill
npx skills add 53able/skills --skill pake-app-builder
npx skills add 53able/skills --skill css-layout
npx skills add 53able/skills --skill macos-screenshot-capture
npx skills add 53able/skills --skill wxt-extension-development
npx skills add 53able/skills --skill self-refine
npx skills add 53able/skills --skill context-to-gantt
npx skills add 53able/skills --skill code-reading
npx skills add 53able/skills --skill cognitive-load-minimizer
npx skills add 53able/skills --skill task-breakdown
npx skills add 53able/skills --skill tdd-from-design-docs
npx skills add 53able/skills --skill commit-diffs
npx skills add 53able/skills --skill git-commit-granularity
npx skills add 53able/skills --skill pr-creation
npx skills add 53able/skills --skill pr-conflict-resolve
npx skills add 53able/skills --skill pr-evidence-capture
npx skills add 53able/skills --skill pdf-markdown-local
npx skills add 53able/skills --skill csv-llm-edit
npx skills add 53able/skills --skill image-pii-masking
npx skills add 53able/skills --skill pi-agent-harness
npx skills add 53able/skills --skill reliable-llm-app-principles
npx skills add 53able/skills --skill primitive-reimpl

# Cursor 向けにグローバルインストール
npx skills add 53able/skills --skill thinking-ensemble -g -a cursor
npx skills add 53able/skills --skill decision-matrix -g -a cursor
npx skills add 53able/skills --skill thinking-logical -g -a cursor
npx skills add 53able/skills --skill thinking-mece -g -a cursor
npx skills add 53able/skills --skill thinking-deduction -g -a cursor
npx skills add 53able/skills --skill thinking-induction -g -a cursor
npx skills add 53able/skills --skill thinking-abduction -g -a cursor
npx skills add 53able/skills --skill thinking-pac -g -a cursor
npx skills add 53able/skills --skill thinking-critical -g -a cursor
npx skills add 53able/skills --skill thinking-debate -g -a cursor
npx skills add 53able/skills --skill thinking-meta -g -a cursor
npx skills add 53able/skills --skill jobs-theory-innovation -g -a cursor
npx skills add 53able/skills --skill readable-writing-workflow -g -a cursor
npx skills add 53able/skills --skill nihongo-skeleton-writing -g -a cursor
npx skills add 53able/skills --skill tech-article-angle -g -a cursor
npx skills add 53able/skills --skill zenn-markdown -g -a cursor
npx skills add 53able/skills --skill natural-expression-refiner -g -a cursor
npx skills add 53able/skills --skill sentence-logic-guard -g -a cursor
npx skills add 53able/skills --skill logical-consistency-reviewer -g -a cursor
npx skills add 53able/skills --skill chuuni-refiner -g -a cursor
npx skills add 53able/skills --skill presentation-zen-garr-reynolds -g -a cursor
npx skills add 53able/skills --skill zukai-creator -g -a cursor
npx skills add 53able/skills --skill meeting-to-video -g -a cursor
npx skills add 53able/skills --skill naming-skill -g -a cursor
npx skills add 53able/skills --skill pake-app-builder -g -a cursor
npx skills add 53able/skills --skill css-layout -g -a cursor
npx skills add 53able/skills --skill macos-screenshot-capture -g -a cursor
npx skills add 53able/skills --skill wxt-extension-development -g -a cursor
npx skills add 53able/skills --skill self-refine -g -a cursor
npx skills add 53able/skills --skill context-to-gantt -g -a cursor
npx skills add 53able/skills --skill code-reading -g -a cursor
npx skills add 53able/skills --skill cognitive-load-minimizer -g -a cursor
npx skills add 53able/skills --skill task-breakdown -g -a cursor
npx skills add 53able/skills --skill tdd-from-design-docs -g -a cursor
npx skills add 53able/skills --skill commit-diffs -g -a cursor
npx skills add 53able/skills --skill git-commit-granularity -g -a cursor
npx skills add 53able/skills --skill pr-creation -g -a cursor
npx skills add 53able/skills --skill pr-conflict-resolve -g -a cursor
npx skills add 53able/skills --skill pr-evidence-capture -g -a cursor
npx skills add 53able/skills --skill pdf-markdown-local -g -a cursor
npx skills add 53able/skills --skill csv-llm-edit -g -a cursor
npx skills add 53able/skills --skill image-pii-masking -g -a cursor
npx skills add 53able/skills --skill pi-agent-harness -g -a cursor
npx skills add 53able/skills --skill reliable-llm-app-principles -g -a cursor
npx skills add 53able/skills --skill primitive-reimpl -g -a cursor
```

サブディレクトリだけ指定する場合:

```bash
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-ensemble -g
npx skills add https://github.com/53able/skills/tree/main/skills/decision-matrix -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-logical -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-mece -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-deduction -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-induction -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-abduction -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-pac -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-critical -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-debate -g
npx skills add https://github.com/53able/skills/tree/main/skills/thinking-meta -g
npx skills add https://github.com/53able/skills/tree/main/skills/jobs-theory-innovation -g
npx skills add https://github.com/53able/skills/tree/main/skills/readable-writing-workflow -g
npx skills add https://github.com/53able/skills/tree/main/skills/nihongo-skeleton-writing -g
npx skills add https://github.com/53able/skills/tree/main/skills/tech-article-angle -g
npx skills add https://github.com/53able/skills/tree/main/skills/zenn-markdown -g
npx skills add https://github.com/53able/skills/tree/main/skills/natural-expression-refiner -g
npx skills add https://github.com/53able/skills/tree/main/skills/sentence-logic-guard -g
npx skills add https://github.com/53able/skills/tree/main/skills/logical-consistency-reviewer -g
npx skills add https://github.com/53able/skills/tree/main/skills/chuuni-refiner -g
npx skills add https://github.com/53able/skills/tree/main/skills/presentation-zen-garr-reynolds -g
npx skills add https://github.com/53able/skills/tree/main/skills/zukai-creator -g
npx skills add https://github.com/53able/skills/tree/main/skills/meeting-to-video -g
npx skills add https://github.com/53able/skills/tree/main/skills/naming-skill -g
npx skills add https://github.com/53able/skills/tree/main/skills/pake-app-builder -g
npx skills add https://github.com/53able/skills/tree/main/skills/css-layout -g
npx skills add https://github.com/53able/skills/tree/main/skills/macos-screenshot-capture -g
npx skills add https://github.com/53able/skills/tree/main/skills/wxt-extension-development -g
npx skills add https://github.com/53able/skills/tree/main/skills/self-refine -g
npx skills add https://github.com/53able/skills/tree/main/skills/context-to-gantt -g
npx skills add https://github.com/53able/skills/tree/main/skills/code-reading -g
npx skills add https://github.com/53able/skills/tree/main/skills/cognitive-load-minimizer -g
npx skills add https://github.com/53able/skills/tree/main/skills/task-breakdown -g
npx skills add https://github.com/53able/skills/tree/main/skills/tdd-from-design-docs -g
npx skills add https://github.com/53able/skills/tree/main/skills/commit-diffs -g
npx skills add https://github.com/53able/skills/tree/main/skills/git-commit-granularity -g
npx skills add https://github.com/53able/skills/tree/main/skills/pr-creation -g
npx skills add https://github.com/53able/skills/tree/main/skills/pr-conflict-resolve -g
npx skills add https://github.com/53able/skills/tree/main/skills/pr-evidence-capture -g
npx skills add https://github.com/53able/skills/tree/main/skills/pdf-markdown-local -g
npx skills add https://github.com/53able/skills/tree/main/skills/csv-llm-edit -g
npx skills add https://github.com/53able/skills/tree/main/skills/image-pii-masking -g
npx skills add https://github.com/53able/skills/tree/main/skills/pi-agent-harness -g
npx skills add https://github.com/53able/skills/tree/main/skills/reliable-llm-app-principles -g
npx skills add https://github.com/53able/skills/tree/main/skills/primitive-reimpl -g
```

## スキル構成

各スキルは `skills/<skill-name>/` に配置する。

```
skills/<skill-name>/
├── SKILL.md          # スキル本体（各エージェントが読み込む）
└── *.md              # スキルに同梱するサポートファイル（任意）
```

エージェント向けのリポジトリ運用メモは [AGENTS.md](./AGENTS.md) を参照。
