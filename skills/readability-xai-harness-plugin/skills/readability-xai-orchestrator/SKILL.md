---
name: readability-xai-orchestrator
description: "He & Martens (2026) の XAI ナラティブ多エージェント枠を、複雑文章→読みやすい文章へ転用するオーケストレーター。Narrator・Faithful Evaluator/Critic・Coherence を反復し、_workspace に成果物を蓄積する。読みやすさハーネス、XAIナラティブ、忠実性ループ、平易化パイプライン、マルチエージェント編集、arXiv 2603.20003 の手法と依頼されたら必ずこのスキルを使う。単一プロンプトでの要約のみ、コードレビュー、画像説明だけの依頼では使わない。"
---

# Readability XAI Orchestrator

## 実行モード: エージェントチーム（既定）

Narrator・Faithful Evaluator・Faithful Critic を核とし、オプションで Coherence Agent と QA を加える。チームは `TeamCreate` で構成し、`TaskCreate` と `SendMessage` で協調する（ツール名は Claude Code 側の規約に従う）。

## 論文とのマッピング

| 論文コンポーネント | 本ハーネス |
|--------------------|------------|
| SHAP 表・予測 | ソース文章（＋任意の「保持すべき事実」メモ） |
| Narrator | `readability-narrator` + エージェント `readability-narrator.md` |
| Faithful Evaluator | `faithful-evaluator-text` |
| Faithful Critic / Rule | `faithful-critic-text` |
| Coherence Agent | `coherence-agent-text` |
| アンサンブル（多数決） | 任意: 抽出の不確実性が高いとき複数 Evaluator 投票（`references/ensemble.md`） |

出典: [An Agentic Approach to Generating XAI-Narratives](https://arxiv.org/abs/2603.20003)（PDF: https://arxiv.org/pdf/2603.20003v1 ）

## システムデザイン（論文 Sec.2.2 に対応）

ユーザーまたはオーケストレータが最初に1つ選ぶ。

| デザイン | 含まれるエージェント | 使いどころ |
|----------|----------------------|------------|
| **basic** | Narrator + Faithful Evaluator | 最小構成・高速 |
| **critic** | + Faithful Critic | 修正指示まで欲しい（推奨） |
| **critic-rule** | + Faithful Critic（Rule 重視） | 長いフィードバックを抑えたい |
| **coherent** | + Coherence（critic 系と併用） | 文体・接続を強く整えたい |
| **coherent-rule** | + Coherence + Rule 寄り Critic | 同上、テンプレ多め |

**注意**: 論文では Coherence 併用が **faithfulness を悪化**させうる。`coherent*` を選ぶ場合は QA が P0 を監視する。

## データフロー（ファイルベース）

1. `_workspace/00_input/source.md` … ソース原文
2. `_workspace/00_input/constraints.md` … 読者・文長・禁止事項（任意）
3. 各ラウンド `n`（最大3推奨、論文は主実験で最大3イテレーション）:
   - `_workspace/r{n}_readability_narrator_draft.md`
   - `_workspace/r{n}_faithful_evaluator_report.md`
   - `_workspace/r{n}_faithful_critic_feedback.md`（critic 系のとき）
   - `_workspace/r{n}_coherence_feedback.md`（coherent 系のとき）
4. `_workspace/final_readability_output.md` … 採用版
5. `_workspace/qa_r{n}_report.md` … QA（任意だが推奨）

## ワークフロー

### Phase 0: 準備

1. 上記入力を書き込む。
2. デザイン（basic / critic / critic-rule / coherent / coherent-rule）を決定。

### Phase 1: ラウンド0（草案）

1. `TaskCreate`: Narrator に `source.md` と `constraints.md` を渡し草案を生成。

### Phase 2: 評価（並列可）

1. Faithful Evaluator に草案とソースを渡す → `faithful_evaluator_report.md`
2. critic 系: Faithful Critic がレポートを指令へ変換
3. coherent 系: Coherence Agent が言語提案

### Phase 3: 反復

1. Narrator に「直前草案 + Faithful 指令 +（あれば）Coherence 指令」を渡し改稿。
2. 停止条件（論文に準拠）:
   - **coherent 系以外**: Faithful がスコープ内 100% と判断 **または** 最大ラウンド到達
   - **coherent 系**: 早期 faithfulness 停止を**無効化**し、論文と同様に**全ラウンド走査**も選択可（デフォルトは最大ラウンドまで Coherence も適用）

実務上は「最大3ラウンド」か「Faithful クリーンで打ち切り」のハイブリッドを推奨。

### Phase 4: QA

1. `readability-qa` エージェントが境界面交差チェック。

### Phase 5: 最終出力

1. `final_readability_output.md` に採用文面と、採用ラウンド番号・未解決の注意を記す。

## エラーハンドリング

| 状況 | 対応 |
|------|------|
| Evaluator の抽出が不安定 | `ensemble.md` の多数決、または人間レビューにエスカレーション |
| フィードバック矛盾 | Narrator が忠実性優先、矛盾は `_workspace/r{n}_narrator_conflict_notes.md` に記録 |
| ソースが長すぎる | セクション分割 Evaluator、スコープをファイル先頭に明記 |
| 1回リトライ後も失敗 | そのラウンドの結果を残し、最終報告に「未解決」を明記 |

## テストシナリオ

### 正常系

- **入力**: 450語の規約条文、`constraints` に「一般消費者向け・800字以内」
- **期待**: 3ラウンド以内に `final_readability_output.md` が生成され、Faithful が unsupported を検出しない、QA が P0 ゼロ

### 異常系

- **入力**: ソースに数値なし、草案にのみ「30%」が出現
- **期待**: Evaluator が `number` または `unsupported` エラーを出し、Critic が削除/弱化指示、最終版で該当を解消または「ソースに数値なし」と注記

## エージェント割当（起動時）

本パッケージは **Cursor プラグイン**（`readability-xai-harness-plugin`）として配布する。エージェント定義はプラグインルートの `agents/` を参照する（プロジェクトに `.claude/agents/` を置く従来形でもよいが、重複は避ける）。

| 役割 | エージェントファイル | スキル |
|------|----------------------|--------|
| Narrator | `agents/readability-narrator.md` | `readability-narrator` |
| Faithful Evaluator | `agents/faithful-evaluator-text.md` | `faithful-evaluator-text` |
| Faithful Critic | `agents/faithful-critic-text.md` | `faithful-critic-text` |
| Coherence | `agents/coherence-agent-text.md` | `coherence-agent-text` |
| QA | `agents/readability-qa.md` | （手順はエージェント定義に従う） |

**インストール**: `skills/readability-xai-harness-plugin/` をフォルダごと `~/.cursor/plugins/local/readability-xai-harness-plugin` に置くか、Cursor のプラグイン読み込み対象パスに追加する（`npx skills` で個別スキルだけ取り込む場合はリポジトリの `skills/readability-xai-harness-plugin/skills/<skill-name>/` を指定する）。

**モデル**: 各 `Agent(..., model: "opus")` を明示する。

## 参照

- `references/ensemble.md` … 抽出アンサンブル（任意）
- `references/test-prompts.md` … スキル検証用プロンプト例
