import { Audio, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { VideoProps } from "../schema";

type Phase = VideoProps["phases"][number];

const PHASE_COLORS: Record<Phase["phase"], string> = {
  problem: "#f59e0b",
  discussion: "#ef4444",
  decision: "#8b5cf6",
};

type Props = {
  phase: Phase;
  phaseIndex: number;
  totalPhases: number;
  /** フェーズ全体の尺（フレーム数）。音声トリミングに使用 */
  phaseDurationInFrames: number;
  /** phase-{n}.mp3 の n（1始まり）。ファイルが存在しない場合は undefined */
  audioSrc?: string;
};

/** ストーリーフェーズ1枚のスライド（タイムラインサイドバー付き） */
export const PhaseSlide = ({
  phase,
  phaseIndex,
  totalPhases,
  phaseDurationInFrames,
  audioSrc,
}: Props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const color = PHASE_COLORS[phase.phase];
  const headerProgress = spring({ frame, fps, from: 0, to: 1, delay: 5 });
  const summaryProgress = spring({ frame, fps, from: 0, to: 1, delay: 20 });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#0a0a0f",
        display: "flex",
        padding: "80px 120px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
      }}
    >
      {/* ボイスオーバー（narrationがあり音声ファイルが存在する場合のみ） */}
      {audioSrc && (
        <Audio
          src={audioSrc}
          trimBefore={0}
          trimAfter={phaseDurationInFrames}
        />
      )}

      {/* タイムラインサイドバー */}
      <div style={{ width: 60, display: "flex", flexDirection: "column", alignItems: "center", marginRight: 60 }}>
        {Array.from({ length: totalPhases }).map((_, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1 }}>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: "50%",
                background: i === phaseIndex ? color : i < phaseIndex ? "#475569" : "#1e293b",
                border: `3px solid ${i === phaseIndex ? color : i < phaseIndex ? "#475569" : "#334155"}`,
              }}
            />
            {i < totalPhases - 1 && (
              <div style={{ width: 2, flex: 1, background: i < phaseIndex ? "#475569" : "#1e293b" }} />
            )}
          </div>
        ))}
      </div>

      {/* メインコンテンツ */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div
          style={{
            opacity: headerProgress,
            transform: `translateX(${interpolate(headerProgress, [0, 1], [-30, 0])}px)`,
          }}
        >
          <div style={{ color, fontSize: 14, letterSpacing: 3, textTransform: "uppercase", marginBottom: 16 }}>
            {phase.label}
          </div>
          <h2
            style={{
              color: "#ffffff",
              fontSize: 56,
              fontWeight: 700,
              margin: "0 0 40px 0",
              lineHeight: 1.2,
              opacity: summaryProgress,
            }}
          >
            {phase.summary}
          </h2>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {phase.bullets.map((bullet, i) => {
            const bulletProgress = spring({ frame, fps, from: 0, to: 1, delay: 30 + i * 15 });
            return (
              <div
                key={i}
                style={{
                  opacity: bulletProgress,
                  transform: `translateX(${interpolate(bulletProgress, [0, 1], [-20, 0])}px)`,
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
                <span style={{ color: "#e2e8f0", fontSize: 32 }}>{bullet}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
