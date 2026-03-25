import { z } from "zod";

/** ストーリーの1フェーズ */
const PhaseSchema = z.object({
  /** 会議フェーズ種別 */
  phase: z.enum(["problem", "discussion", "decision"]),
  /** 画面表示ラベル（例: "課題"） */
  label: z.string(),
  /** 1行の要点 */
  summary: z.string(),
  /** 詳細ポイント（最大3つ） */
  bullets: z.array(z.string()).max(3),
  /**
   * TTS用ナレーション文（Unicodeコードポイント50〜100文字）
   * 省略時はそのフェーズの音声を生成しない
   */
  narration: z
    .string()
    .refine((s) => [...s].length >= 50 && [...s].length <= 100, {
      message: "narration must be 50–100 Unicode code points",
    })
    .optional(),
});

/** アクションアイテム */
const ActionSchema = z.object({
  /** 担当者名 */
  owner: z.string(),
  /** タスク内容 */
  task: z.string(),
  /** 期限（省略可） */
  due: z.string().optional(),
});

/** ビデオ全体のプロパティ */
export const VideoPropsSchema = z.object({
  /** 会議タイトル */
  title: z.string(),
  /** 会議日付（YYYY-MM-DD） */
  date: z.string().optional(),
  /** 参加者リスト */
  participants: z.array(z.string()).optional(),
  /** ストーリーフェーズ（1〜5個） */
  phases: z.array(PhaseSchema).min(1).max(5),
  /** アクションアイテム（なければ空配列） */
  actions: z.array(ActionSchema).default([]),
  /**
   * ボイスオーバー有効フラグ。
   * gen-audio.sh 実行後に true に設定することで <Audio> が有効になる。
   * false（デフォルト）のときは音声ファイルがなくてもプレビューが動く。
   */
  withVoiceover: z.boolean().default(false),
});

export type VideoProps = z.infer<typeof VideoPropsSchema>;
