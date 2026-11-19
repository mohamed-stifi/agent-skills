import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Camera, CamKey } from '../kit/Camera';
import { C } from '../kit/tokens';
import { BrandMark, Rise, Rule } from '../kit/ui';

// EXAMPLE SCENE — shows the pattern every scene follows: a world plane, a camera with keys, one subject,
// a decisive `snap`, a headline, and an exit push that hides the cut. Delete it once real scenes exist.
const KEYS: CamKey[] = [
  { f: 0, x: 960, y: 540, zoom: 4, rx: 18, ry: -10, rz: 0 },
  { f: 26, x: 960, y: 540, zoom: 1.1, rx: 0, ry: 0, rz: 0, ease: 'snap' }, // decisive: anticipation + overshoot
  { f: 210, x: 960, y: 540, zoom: 1.16, rx: 0, ry: 0, rz: 0, ease: 'drift' }, // a hold is never fully still
  { f: 239, x: 760, y: 470, zoom: 30, rx: 0, ry: 0, rz: 0, ease: 'pushIn' }, // exit: push into the mark
];

export const S01Example: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <Camera keys={KEYS} background={C.ground}>
      <div style={{ position: 'absolute', left: 560, top: 380, display: 'flex', flexDirection: 'column', gap: 28 }}>
        <BrandMark size={150} />
        <Rule frame={f} a={40} b={64} w={800} />
        <Rise text="Your product, in one sentence." frame={f} start={56} size={56} upper={false} weight={500} family='"Barlow", sans-serif' tracking="0" />
      </div>
    </Camera>
  );
};
