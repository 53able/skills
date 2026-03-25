import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { VideoProps } from "../schema";

type Props = Pick<VideoProps, "actions">;

/** アクションアイテム一覧スライド */
export const ActionItems = ({ actions }: Props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleProgress = spring({ frame, fps, from: 0, to: 1, delay: 5 });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#050810",
        display: "flex",
        flexDirection: "column",
        padding: "80px 120px",
        boxSizing: "border-box",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          opacity: titleProgress,
          color: "#f472b6",
          fontSize: 14,
          letterSpacing: 3,
          textTransform: "uppercase",
          marginBottom: 40,
        }}
      >
        NEXT STEPS
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {actions.map((action, i) => {
          const cardProgress = spring({ frame, fps, from: 0, to: 1, delay: 15 + i * 20 });
          return (
            <div
              key={i}
              style={{
                opacity: cardProgress,
                transform: `translateX(${interpolate(cardProgress, [0, 1], [-20, 0])}px)`,
                background: "#1e293b",
                borderRadius: 12,
                padding: "24px 32px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ color: "#f472b6", fontSize: 14, marginBottom: 8 }}>{action.owner}</div>
                <div style={{ color: "#e2e8f0", fontSize: 32, fontWeight: 600 }}>{action.task}</div>
              </div>
              {action.due && (
                <div style={{ color: "#94a3b8", fontSize: 24, flexShrink: 0, marginLeft: 32 }}>{action.due}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
