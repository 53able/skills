import { VideoProps } from "../schema";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

type Props = Pick<VideoProps, "title" | "date">;

/** アウトロ: タイトルを静止表示（アニメーションなし） */
export const Outro = ({ title, date }: Props) => {
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
        opacity: 1,
      }}
    >
      <div style={{ color: "#6366f1", fontSize: 24, letterSpacing: 4, textTransform: "uppercase", marginBottom: 16 }}>
        MEETING RECAP
      </div>
      <h1 style={{ color: "#ffffff", fontSize: 72, fontWeight: 800, margin: 0, textAlign: "center" }}>
        {title}
      </h1>
      {formattedDate && (
        <div style={{ color: "#94a3b8", fontSize: 28, marginTop: 32 }}>{formattedDate}</div>
      )}
    </div>
  );
};
