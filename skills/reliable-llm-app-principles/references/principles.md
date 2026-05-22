# 信頼性の高い LLM アプリケーション原則

`SKILL.md` の短縮チェックだけでは足りない場合に読む。

## 1. Natural language to tool calls

自然言語や外部イベントを、型付き intent と payload に変換する。自由文から直接副作用を起こさない。

実装シグナル:
- intent enum または discriminated union がある。
- payload schema が必須フィールドと型を検証する。
- 副作用の前に business policy を通す。

## 2. Own prompts

prompt を source control 上のファイル、または明確に命名されたコードモジュールで管理する。prompt をフレームワーク内部の隠れた設定にしない。

実装シグナル:
- prompt の差分をレビューできる。
- prompt に role、task、constraints、output schema、escalation 条件がある。
- prompt 変更に golden example または eval がある。

## 3. Own the context window

thread state、retrieved records、compact error、relevant memory から context を意図的に組み立てる。raw history をそのまま渡さない。

実装シグナル:
- context builder 関数がある。
- retrieved facts に provenance がある。
- truncation、summarization、memory injection の規則が明示されている。

## 4. Tools are just structured outputs

tool call を LLM が返す構造化出力として扱う。コードが検証し、コードが実行する。

実装シグナル:
- LLM が `{intent, payload}` または同等の構造を返す。
- tool execution が model call の外側にある。
- invalid structured output に retry または escalation がある。

## 5. Unify execution state and business state

ユーザーに見える業務 event と runtime event を、可能な限り同じ thread または event history に保存する。

実装シグナル:
- tool result、approval、error、wait が同じ durable history に append される。
- event append が atomic、または concurrency control で保護されている。
- audit と replay が同じ source を読む。

## 6. Launch, pause, resume

長時間ジョブ、人間承認、callback、process restart に耐えるため、単純な lifecycle API を持つ。

実装シグナル:
- launch が thread を開始または継続する。
- pause が停止理由を記録する。
- resume が外部 event を idempotent に受け取る。

## 7. Contact humans with tool calls

人間への質問や承認依頼を、ad hoc なチャットではなく構造化 tool call として扱う。

実装シグナル:
- human request に question、context、urgency、choices、response schema がある。
- approval decision が保存される。
- notification channel が resume event に戻る。

## 8. Own control flow

分岐、retry、approval、stop condition を決定的な application code で持つ。

実装シグナル:
- code が intent または state で switch する。
- 高リスク action に policy check または approval がある。
- loop に max iteration と timeout がある。

## 9. Compact errors into context

raw exception や長い log を、短く行動可能な error summary に変換してから model に戻す。

実装シグナル:
- error object に failing operation、cause summary、retryability、next allowed actions がある。
- sensitive data が除去される。
- retry budget が明示されている。

## 10. Small, focused agents

万能 agent ではなく、責務が狭い agent を優先する。

実装シグナル:
- agent scope が少数の tools と decisions に収まる。
- agent 間 handoff が型付きである。
- eval example が agent の責務に一致する。

## 11. Trigger from anywhere

Slack、email、webhook、cron、monitoring alert、product UI event を同じ event model に正規化する。

実装シグナル:
- trigger adapter が canonical event を生成する。
- trigger ごとに authentication と deduplication がある。
- source metadata が保存される。

## 12. Stateless reducer

agent step を可能な限り `thread + event -> next action` に近づける。副作用は reducer の外へ出す。

実装シグナル:
- reducer logic が stored events から再実行できる。
- tool side effect は validation 後に呼び出される。
- replay、debug、audit が hidden in-memory state に依存しない。
