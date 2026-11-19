import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C } from '../kit/tokens';
import { Camera, CamKey } from '../kit/Camera';
import { prog, tween, clamp } from '../kit/ease';
import { Rise, Rule } from '../kit/ui';
import { CAL, ALL, ORDER, HERO_ID, rectOf, WeekGrid, ToilBlock, YellowBlock, YELLOW_FULL, YELLOW_TITLE, YELLOW_SUB, mix, bank } from './Week';

// V01 · HOOK — "The week that toil eats". White ground, ends on ink (the 02:14 page).

// ---- landing schedule: gaps shrink, so the drops accelerate ----
const T: Record<string, number> = {};
{
  let t = 16;
  ORDER.forEach((id, i) => {
    T[id] = t;
    t += 10 * Math.pow(1 - i / (ORDER.length - 1), 2) + 0.6;
  });
}
const EXIT = Math.round(T[HERO_ID]) + 14; // the yellow block is pushed out
T['0-0'] = EXIT + 12; // "handover notes" takes its place as it leaves
const DIM_AT = EXIT + 30;
const DIVE = 296;

// ---- the squeeze: yellow loses width, then height, with every drop that lands on its ground ----
const ROWS = (r: number) => r * CAL.HR - 4;
const STEPS: [string, number][] = [['0-4', 4], ['0-3', 3], ['0-1', 1]];
const yellowAt = (f: number) => {
  const w0 = YELLOW_FULL.w, w1 = CAL.CW - 8;
  const ws = T['1-3'] - 8;
  const w = tween(f, ws, ws + 16, w0, w1, 'land');
  let h = YELLOW_FULL.h, prev = h;
  for (const [id, rows] of STEPS) {
    const s = T[id] - 8, to = ROWS(rows);
    if (f >= s) h = tween(f, s, s + 14, prev, to, 'land');
    prev = to;
  }
  const x = tween(f, EXIT, EXIT + 30, YELLOW_FULL.x, -560, 'snap');
  return { x, y: YELLOW_FULL.y, w, h };
};

const KEYS: CamKey[] = bank(
  [
    { f: 0, x: 400, y: 380, zoom: 2.4, rx: 16, ry: 9, rz: -1 },
    { f: 34, ease: 'land', x: 470, y: 405, zoom: 2.05, rx: 10, ry: 5, rz: 0 },
    { f: 110, ease: 'drift', x: 690, y: 440, zoom: 1.5, rx: 5, ry: 2, rz: 0 },
    { f: 176, ease: 'out', x: 950, y: 525, zoom: 1.08, rx: 1, ry: 0, rz: 0 },
    { f: 210, ease: 'out', x: 960, y: 530, zoom: 1.0, rx: 0, ry: 0, rz: 0 },
    { f: DIVE, ease: 'drift', x: 960, y: 530, zoom: 1.05, rx: 0, ry: 0, rz: 0 },
    // down to the 02:14 night block
    { f: 322, ease: 'whip', x: 1000, y: 962, zoom: 1.9, rx: 0, ry: 0, rz: 0 },
    { f: 334, ease: 'drift', x: 1000, y: 966, zoom: 2.4, rx: 0, ry: 0, rz: 0 },
    // exponential push (log-linear, built from linear segments)
    { f: 338, ease: 'linear', x: 1000, y: 968, zoom: 4.5, rx: 0, ry: 0, rz: 0 },
    { f: 342, ease: 'linear', x: 1000, y: 968, zoom: 9.5, rx: 0, ry: 0, rz: 0 },
    { f: 346, ease: 'linear', x: 1000, y: 968, zoom: 20, rx: 0, ry: 0, rz: 0 },
    { f: 350, ease: 'linear', x: 1000, y: 968, zoom: 45, rx: 0, ry: 0, rz: 0 },
    { f: 354, ease: 'linear', x: 1000, y: 968, zoom: 100, rx: 0, ry: 0, rz: 0 },
    { f: 359, ease: 'linear', x: 1000, y: 968, zoom: 240, rx: 0, ry: 0, rz: 0 },
  ],
  359,
);

const Drop: React.FC<{ id: string; frame: number }> = ({ id, frame }) => {
  const t = T[id];
  if (frame < t) return null;
  const p = prog(frame, t, t + 13, 'land');
  const r = rectOf(ALL[id]);
  return <ToilBlock label={ALL[id].label} x={r.x} y={r.y - (1 - p) * 56} w={r.w} h={r.h} night={ALL[id].night} style={{ opacity: clamp((frame - t) / 3) }} />;
};

export const V01Week: React.FC = () => {
  const frame = useCurrentFrame();
  const dim = tween(frame, DIM_AT, DIM_AT + 28, 1, 0.25, 'out');
  const y = yellowAt(frame);
  const hero = ALL[HERO_ID];
  const hr = rectOf(hero);
  const heroT = T[HERO_ID];
  const fillT = prog(frame, 330, 346, 'out');
  const headOut = prog(frame, DIVE + 2, DIVE + 16, 'pushIn');
  const hp = prog(frame, heroT, heroT + 13, 'land');
  return (
    <>
      <Camera keys={KEYS} background={C.ground}>
        <div style={{ opacity: dim }}>
          <WeekGrid />
          {ORDER.filter((id) => id !== HERO_ID).concat('0-0').map((id) => <Drop key={id} id={id} frame={frame} />)}
        </div>
        {/* the 02:14 page stays at full weight: it is where the camera dives */}
        {frame >= heroT && (
          <ToilBlock
            label={hero.label} x={hr.x} y={hr.y - (1 - hp) * 56} w={hr.w} h={hr.h} night
            bg={mix(C.concrete, C.ink, fillT)} fg={mix(C.ink, C.dFg, fillT)} edge={mix(C.red, C.ink, fillT)} bar={mix(C.red, C.ink, fillT)}
            style={{ opacity: clamp((frame - heroT) / 3) }}
          />
        )}
        {frame < EXIT + 40 && <YellowBlock x={y.x} y={y.y} w={y.w} h={y.h} title={YELLOW_TITLE} sub={YELLOW_SUB} />}
      </Camera>
      {/* headline, screen space */}
      <div style={{ position: 'absolute', left: 120, top: 300, width: 1680, opacity: 1 - headOut, transform: `translateY(${-headOut * 50}px)` }}>
        <Rule frame={frame} a={DIM_AT + 4} b={DIM_AT + 30} w={1680} />
        <div style={{ marginTop: 36 }}>
          <Rise text="YOUR BEST ENGINEERS" frame={frame} start={DIM_AT + 10} size={176} stagger={5} />
          <Rise text="SPEND THEIR WEEK ON THIS." frame={frame} start={DIM_AT + 24} size={176} stagger={5} />
        </div>
      </div>
      <AbsoluteFill style={{ background: C.ink, opacity: prog(frame, 349, 357, 'out'), pointerEvents: 'none' }} />
    </>
  );
};
