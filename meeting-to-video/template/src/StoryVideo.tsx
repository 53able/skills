import { Sequence, staticFile } from "remotion";
import { VideoProps } from "./schema";
import { Intro } from "./components/Intro";
import { Outro } from "./components/Outro";
import { PhaseSlide } from "./components/PhaseSlide";
import { ActionItems } from "./components/ActionItems";
import { INTRO_FRAMES, ACTION_FRAMES, OUTRO_FRAMES, TOTAL_FRAMES } from "./constants";

/** フェーズ1個あたりのフレーム数を計算する純粋関数 */
const calcPhaseFrames = (totalPhases: number, hasActions: boolean): number => {
  const reserved = INTRO_FRAMES + OUTRO_FRAMES + (hasActions ? ACTION_FRAMES : 0);
  return Math.floor((TOTAL_FRAMES - reserved) / totalPhases);
};

/** ミーティングトランスクリプトから生成されたストーリー型ビデオ */
export const StoryVideo = ({
  title,
  date,
  participants,
  phases,
  actions,
  withVoiceover,
}: VideoProps) => {
  const hasActions = actions.length > 0;
  const phaseFrames = calcPhaseFrames(phases.length, hasActions);
  const actionStartFrame = INTRO_FRAMES + phases.length * phaseFrames;
  const outroStartFrame = actionStartFrame + (hasActions ? ACTION_FRAMES : 0);

  return (
    <>
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <Intro title={title} date={date} participants={participants} />
      </Sequence>

      {phases.map((phase, i) => (
        <Sequence
          key={`${phase.phase}-${i}`}
          from={INTRO_FRAMES + i * phaseFrames}
          durationInFrames={phaseFrames}
        >
          <PhaseSlide
            phase={phase}
            phaseIndex={i}
            totalPhases={phases.length}
            phaseDurationInFrames={phaseFrames}
            // withVoiceover=true かつ narration がある場合のみ音声を渡す
            // false のときはファイルが存在しなくてもプレビューが動く
            audioSrc={withVoiceover && phase.narration ? staticFile(`audio/phase-${i + 1}.mp3`) : undefined}
          />
        </Sequence>
      ))}

      {hasActions && (
        <Sequence from={actionStartFrame} durationInFrames={ACTION_FRAMES}>
          <ActionItems actions={actions} />
        </Sequence>
      )}

      {/* アウトロ: Outro専用コンポーネントで静止表示（アニメーションなし） */}
      <Sequence from={outroStartFrame} durationInFrames={OUTRO_FRAMES}>
        <Outro title={title} date={date} />
      </Sequence>
    </>
  );
};
