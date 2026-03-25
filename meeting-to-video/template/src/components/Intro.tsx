import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import { VideoProps } from "../schema";

type Props = Pick<VideoProps, "title" | "date" | "participants">;

/** 会議タイトル・日付・参加者を表示するイントロスライド */
export const Intro = ({ title, date, participants }: Props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame, fps, from: 0, to: 1, delay: 10 });
  const subtitleSpring = spring({ frame, fps, from: 0, to: 1, delay: 25 });

  const formattedDate = date
    ? format(new Date(date), "yyyy年M月d日", { locale: ja })
    : undefined;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          opacity: titleSpring,
          transform: `translateY(${interpolate(titleSpring, [0, 1], [20, 0])}px)`,
          textAlign: "center",
        }}
      >
        <div style={{ color: "#6366f1", fontSize: 24, letterSpacing: 4, textTransform: "uppercase", marginBottom: 16 }}>
          MEETING RECAP
        </div>
        <h1 style={{ color: "#ffffff", fontSize: 72, fontWeight: 800, margin: 0 }}>
          {title}
        </h1>
      </div>
      <div
        style={{
          opacity: subtitleSpring,
          marginTop: 32,
          display: "flex",
          gap: 24,
          color: "#94a3b8",
          fontSize: 28,
        }}
      >
        {formattedDate && <span>{formattedDate}</span>}
        {participants && participants.length > 0 && (
          <span>{participants.join(" · ")}</span>
        )}
      </div>
    </div>
  );
};
