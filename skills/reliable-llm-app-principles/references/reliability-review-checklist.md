# 信頼性レビュー・チェックリスト

LLM アプリケーションの設計書、コードベース、PR、アーキテクチャ案をレビューするときに使う。

## 必須レビュー項目

1. **タスク境界**
   - product workflow とユーザーに見える成果を特定する。
   - LLM に委譲する判断を特定する。
   - action を検証し実行する決定的コードを特定する。

2. **Prompt ownership**
   - prompt が source-controlled、named、diffable か確認する。
   - prompt に output schema と escalation rule があるか確認する。
   - 外部 framework 内部に隠れた prompt template を flag する。

3. **Context ownership**
   - context builder を特定する。
   - retrieved data の source provenance を確認する。
   - truncation、summarization、memory rule を確認する。

4. **Structured output and tools**
   - schema validation を確認する。
   - intent allowlist を確認する。
   - side-effecting tool の idempotency を確認する。

5. **State and lifecycle**
   - durable thread または event history を確認する。
   - atomic append または locking を確認する。
   - launch、pause、resume、timeout、deduplication semantics を確認する。

6. **Human interaction**
   - approval threshold を確認する。
   - human input の response schema を確認する。
   - notification から resume への対応関係を確認する。

7. **Control flow**
   - retry budget を確認する。
   - max loop iteration を確認する。
   - deterministic branching と stop condition を確認する。

8. **Error handling**
   - compact error summary を確認する。
   - sensitive-data redaction を確認する。
   - retryable error と terminal error の分類を確認する。

9. **Agent decomposition**
   - scope が広すぎないか確認する。
   - agent 間 handoff が typed か確認する。
   - focused agent ごとの eval を確認する。

10. **Trigger model**
    - trigger source ごとの canonical event 変換を確認する。
    - authentication、authorization、replay protection を確認する。
    - source metadata が保存されるか確認する。

11. **Reducer shape**
    - core step が `thread + event -> next action` として説明できるか確認する。
    - side effect が reducer の外にあるか確認する。
    - replay または audit が hidden memory に依存しないか確認する。

## 重大度

- **Critical**: LLM output が検証や承認なしに irreversible または high-risk な副作用を起こせる。
- **High**: durable state、schema validation、hidden prompts、controlled context construction のいずれかが欠けている。
- **Medium**: retry rule、error compaction、agent scope、trigger metadata が弱い。
- **Low**: runtime safety には直結しない documentation gap、命名不一致、example 不足。
