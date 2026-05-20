---
name: reliable-llm-app-principles
description: 12-Factor Agents を中心に、信頼性の高い LLM アプリケーションを設計、レビュー、改善する手順を提供する。プロンプト所有、コンテキスト制御、構造化出力、統一状態、pause/resume、人間承認、制御フロー、エラー圧縮、小さなエージェント、外部トリガー、stateless reducer を扱う。LLM アプリ、エージェント実行基盤、tool-calling ワークフロー、本番信頼性レビューで使用する。一般的なプロンプト作成、モデル比較、UI 文言編集、LLM を含まない通常のアプリ設計には使用しない。
---

# 信頼性の高い LLM アプリケーション原則

12-Factor Agents を基礎に、LLM アプリケーションの設計、レビュー、改善を行う。

## 使用条件

使用する場面:
- LLM アプリケーション、AI エージェント、tool-calling ワークフローを設計する。
- 既存の LLM 実行基盤を信頼性、監査性、復旧性の観点でレビューする。
- プロンプト、コンテキスト、状態管理、人間承認、エラー処理の境界を整理する。
- 本番導入前の設計レビュー、PR レビュー、アーキテクチャレビューを行う。

使用しない場面:
- 単発のプロンプト改善だけを行う。
- LLM を含まない通常のバックエンド設計を行う。
- モデルの性能比較や価格比較だけを行う。
- UI 文言やマーケティングコピーだけを編集する。

## 基本方針

- LLM には「判断候補の生成」を任せる。
- 副作用、承認、検証、再試行、停止条件は決定的なコードで扱う。
- 自由文ではなく、型付き intent と payload を境界にする。
- 実行状態、業務状態、承認、エラーを durable な thread または event history に残す。
- replay、監査、pause/resume ができない設計を高リスクとして扱う。

## ワークフロー

1. **対象を特定する**
   - 対象アプリケーション、対象ワークフロー、ユーザーに見える成果を特定する。
   - LLM が判断する箇所と、コードが判断する箇所を分ける。
   - 高リスクな副作用を列挙する。例: 送信、削除、課金、デプロイ、権限変更。

2. **入力から action までの経路を描く**
   - ユーザー入力、webhook、cron、Slack、メール、監視アラートなどの trigger を列挙する。
   - trigger が canonical event に正規化されるか確認する。
   - event から context、LLM 出力、検証、実行、記録までの流れを追う。

3. **12 原則でレビューする**
   - 簡易レビューでは下の「短縮チェック」を使う。
   - 詳細レビューでは `references/principles.md` を読む。
   - 設計書または Markdown 仕様をレビューする場合は、必要に応じて `scripts/audit-llm-app.py` を実行する。

4. **ギャップを重大度で分類する**
   - Critical: LLM 出力が検証や承認なしに高リスク副作用を起こせる。
   - High: schema validation、durable state、prompt ownership、context builder のいずれかが欠けている。
   - Medium: retry budget、compact error、人間承認、trigger metadata、agent scope が曖昧。
   - Low: 命名、ドキュメント、例、テストケースの不足。

5. **改善案を実装可能な形に落とす**
   - 「何を変えるか」「どこを変えるか」「成功条件」「確認コマンド」を書く。
   - 不確かな箇所は推測で埋めず、`未確認` または `要確認` と明記する。
   - レビュー成果物が必要な場合は `assets/review-template.md` の形式を使う。

## 短縮チェック

各項目について、Evidence、Gap、Recommendation を 1 行ずつ記録する。

1. **Natural language to tool calls**: 自然言語を型付き intent と payload に変換しているか。
2. **Own prompts**: prompt が source control と review の対象になっているか。
3. **Own context window**: context builder があり、履歴を丸ごと渡していないか。
4. **Tools are structured outputs**: tool call を構造化出力として検証しているか。
5. **Unify execution state and business state**: 実行状態と業務状態が同じ thread または event history に残るか。
6. **Launch / pause / resume**: 長時間処理、承認待ち、callback 待ちを再開できるか。
7. **Contact humans with tool calls**: 人間への質問や承認依頼も構造化 event として扱うか。
8. **Own control flow**: 分岐、再試行、停止条件、承認条件をコードで持つか。
9. **Compact errors**: raw stack trace ではなく、短い retryable error を context に入れるか。
10. **Small focused agents**: agent の責務が狭く、handoff が型付きか。
11. **Trigger from anywhere**: 複数 trigger が canonical event に正規化されるか。
12. **Stateless reducer**: core step が `thread + event -> next action` に近いか。

## スクリプト

設計書や Markdown 仕様の初期スキャンが必要な場合だけ実行する。

```bash
python3 scripts/audit-llm-app.py path/to/spec.md
```

結果の扱い:
- `present` は関連語が見つかったことだけを示す。設計が正しい証拠にはしない。
- `missing` はレビュー対象として優先する。
- スクリプトが `MISSING_SIGNALS` を stderr に出した場合、該当項目を手動で確認する。

## 詳細参照

- 原則の詳細が必要な場合は `references/principles.md` を読む。
- レビュー観点を漏れなく確認する場合は `references/reliability-review-checklist.md` を読む。
- Markdown のレビュー成果物が必要な場合は `assets/review-template.md` を使う。

## エラー処理

- 入力資料が不足している場合は、不足資料を列挙し、確認可能な範囲だけレビューする。
- コードベースが読めない場合は、該当確認を `未確認` として残す。
- LLM 実行や外部 API の挙動を実測していない場合は、`未検証` と明記する。
- スクリプトが失敗した場合は stderr を読み、ファイルパス、文字コード、ディレクトリ指定の誤りを確認する。
- 高リスク副作用が見つかった場合は、先に validation、policy、human approval、idempotency の追加を提案する。
