import React, { useEffect, useState } from 'react';
import { AbsoluteFill, OffthreadVideo, continueRender, delayRender, staticFile, useCurrentFrame } from 'remotion';
import { C, F, FPS } from './kit/tokens';

type Cue = { start: number; end: number; text: string };

/**
 * Burned-in captions over a finished film (public/<id>-final.mp4 + public/<id>-captions.json, staged by captions.sh).
 * Style: dark plate, white body font, square corners, bottom centre. Rendered muted; captions.sh puts the final audio back.
 */
export const Captioned: React.FC<{ id: string }> = ({ id }) => {
  const frame = useCurrentFrame();
  const [cues, setCues] = useState<Cue[] | null>(null);
  const [handle] = useState(() => delayRender(`captions ${id}`));
  useEffect(() => {
    fetch(staticFile(`${id}-captions.json`))
      .then((r) => r.json())
      .then((j) => { setCues(j.cues); continueRender(handle); })
      .catch(() => { setCues([]); continueRender(handle); });
  }, [handle, id]);
  const t = frame / FPS;
  const cue = cues?.find((c) => t >= c.start && t < c.end);
  let o = 0, y = 0;
  if (cue) {
    const fi = Math.min(1, (t - cue.start) / 0.09);
    const fo = Math.min(1, (cue.end - t) / 0.09);
    o = Math.min(fi, fo);
    y = (1 - fi) * 8;
  }
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <OffthreadVideo src={staticFile(`${id}-final.mp4`)} muted />
      {cue && (
        <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 60, paddingLeft: 48, paddingRight: 48 }}>
          <div style={{ opacity: o, transform: `translateY(${y}px)`, maxWidth: 1480, background: 'rgba(11,11,12,0.92)', border: `1px solid ${C.dLine}`, padding: '12px 24px 14px', fontFamily: F.body, fontWeight: 600, fontSize: 42, lineHeight: '52px', color: '#FFFFFF', textAlign: 'center', fontVariantNumeric: 'tabular-nums' }}>
            {cue.text}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
