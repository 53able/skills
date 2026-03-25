# Meeting Transcript Extraction Prompt

以下のミーティングトランスクリプトを分析し、VideoPropsSchema に準拠した JSON を生成してください。

## スキーマ

{
  title: string,
  date?: string,           // YYYY-MM-DD
  participants?: string[],
  phases: Array<{
    phase: "problem" | "discussion" | "decision",
    label: string,         // 日本語（例: "課題"、"議論"、"決定"）
    summary: string,
    bullets: string[],     // 最大3つ
    narration?: string,    // Unicodeコードポイント50〜100文字
  }>,                      // 1〜5個
  actions: Array<{
    owner: string,
    task: string,
    due?: string,
  }>,                      // なければ []
}

## ルール

1. `phases` は `problem / discussion / decision` に分類（1〜5個）
2. `bullets` は最重要ポイントのみ、最大3つ
3. `narration` は自然な日本語の語り口で **Unicodeコードポイント50〜100文字**
4. `actions` は明確に述べられたタスクのみ（不明な場合は `[]`）
5. **出力はJSONのみ**（コードブロック・説明文は不要）

## トランスクリプト

{{TRANSCRIPT}}
