import { Composition } from "remotion";
import { StoryVideo } from "./StoryVideo";
import { VideoPropsSchema } from "./schema";
import { TOTAL_FRAMES } from "./constants";
import contentJson from "../content.json";

export const RemotionRoot = () => {
  const defaultProps = VideoPropsSchema.parse(contentJson);
  return (
    <Composition
      id="StoryVideo"
      component={StoryVideo}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1920}
      height={1080}
      schema={VideoPropsSchema}
      defaultProps={defaultProps}
    />
  );
};
