import React from 'react';
import { AbsoluteFill, Composition, Sequence, Series } from 'remotion';
import './kit/fonts';
import { W, H, FPS } from './kit/tokens';
import { SCENES } from './timeline';
import { FILMS, framesOf } from './films';
import { Captioned } from './Captioned';
import * as Scenes from './scenes';

const MAP = Scenes as unknown as Record<string, React.FC>;

/** The main timeline: every scene back to back. */
const Main: React.FC = () => (
  <Series>
    {SCENES.map((s) => {
      const Comp = MAP[s.file];
      return (
        <Series.Sequence key={s.id} durationInFrames={s.dur}>
          <Comp />
        </Series.Sequence>
      );
    })}
  </Series>
);

/** A cut-down: plays [from, from+len) of the main timeline per part, concatenated. */
const Cut: React.FC<{ parts: [number, number][] }> = ({ parts }) => {
  let at = 0;
  return (
    <AbsoluteFill>
      {parts.map(([from, len], i) => {
        const el = (
          <Sequence key={i} from={at} durationInFrames={len}>
            <Sequence from={-from}><Main /></Sequence>
          </Sequence>
        );
        at += len;
        return el;
      })}
    </AbsoluteFill>
  );
};

export const Root: React.FC = () => (
  <>
    {FILMS.map((f) => (
      <Composition key={f.id} id={f.id} component={f.kind === 'main' ? Main : () => <Cut parts={f.parts ?? []} />}
        durationInFrames={framesOf(f)} fps={FPS} width={W} height={H} />
    ))}
    {FILMS.map((f) => (
      <Composition key={`${f.id}-captioned`} id={`${f.id}-captioned`} component={() => <Captioned id={f.id} />}
        durationInFrames={framesOf(f)} fps={FPS} width={W} height={H} />
    ))}
    {SCENES.map((s) => (
      <Composition key={s.id} id={s.id} component={MAP[s.file]} durationInFrames={s.dur} fps={FPS} width={W} height={H} />
    ))}
  </>
);
