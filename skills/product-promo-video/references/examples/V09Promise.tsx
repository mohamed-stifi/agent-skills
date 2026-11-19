import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/tokens';
import { Camera, CamKey } from '../kit/Camera';
import { prog, tween, clamp } from '../kit/ease';
import { Rise, Rule, NemoMark } from '../kit/ui';
import { CAL, ALL, ORDER, rectOf, WeekGrid, ToilBlock, YellowBlock, Check, YELLOW_FULL, YELLOW_TITLE, YELLOW_SUB, mix, bank } from './Week';

// V09 · PROMISE — the week, given back. The exact inverse of V01: same calendar, same labels, played backwards.
// White ground, ends on ink (the NEMO lane).

const LANE = { x: 1850, y: 40, w: 440, h: 1000, rowsY: 144, pitch: 48, rowH: 44, rowW: 392, cap: 17 };
const ORDER9 = ['0-0', ...[...ORDER].reverse()];
const NB = ORDER9.length;
const START: number[] = [];
{
  let t = 40;
  ORDER9.forEach((_, i) => {
    START.push(t);
    t += i === 0 ? 16 : 4.4 * Math.pow(1 - (i - 1) / (NB - 2), 2) + 0.5;
  });
}
const DUR = (i: number) => (i === 0 ? 30 : 22);
const ARR = START.map((s, i) => s + DUR(i));

const YB = 148;      // the yellow block comes home
const GROW = 176;    // ... and takes its day back
const HEAD = 222;    // headline
const OUT = 324;     // exit toward the NEMO lane

const KEYS: CamKey[] = bank(
  [
    { f: 0, x: 1010, y: 520, zoom: 1.28, rx: 7, ry: -5, rz: 0 },
    { f: 22, ease: 'land', x: 1000, y: 540, zoom: 1.02, rx: 0, ry: 0, rz: 0 },
    { f: 40, ease: 'drift', x: 1000, y: 540, zoom: 1.0, rx: 0, ry: 0, rz: 0 },
    // follow the first block's flight across the week to the lane
    { f: 74, ease: 'whip', x: 1560, y: 360, zoom: 1.22, rx: 0, ry: 0, rz: 0 },
    { f: 120, ease: 'drift', x: 1620, y: 420, zoom: 1.12, rx: 0, ry: 0, rz: 0 },
    { f: 156, ease: 'whip', x: 1010, y: 540, zoom: 1.0, rx: 0, ry: 0, rz: 0 },
    { f: GROW, ease: 'drift', x: 1000, y: 540, zoom: 1.0, rx: 0, ry: 0, rz: 0 },
    // the decisive move: with the yellow block's growth
    { f: GROW + 30, ease: 'snap', x: 940, y: 400, zoom: 1.12, rx: 0, ry: 0, rz: 0 },
    { f: HEAD + 6, ease: 'land', x: 960, y: 540, zoom: 1.0, rx: 0, ry: 0, rz: 0 },
    { f: OUT, ease: 'drift', x: 960, y: 540, zoom: 1.03, rx: 0, ry: 0, rz: 0 },
    { f: OUT + 22, ease: 'whip', x: 2070, y: 560, zoom: 1.15, rx: 0, ry: 0, rz: 0 },
    { f: 347, ease: 'linear', x: 2070, y: 560, zoom: 2.2, rx: 0, ry: 0, rz: 0 },
    { f: 350, ease: 'linear', x: 2070, y: 560, zoom: 8, rx: 0, ry: 0, rz: 0 },
    { f: 353, ease: 'linear', x: 2070, y: 560, zoom: 28, rx: 0, ry: 0, rz: 0 },
    { f: 356, ease: 'linear', x: 2070, y: 560, zoom: 100, rx: 0, ry: 0, rz: 0 },
    { f: 359, ease: 'linear', x: 2070, y: 560, zoom: 300, rx: 0, ry: 0, rz: 0 },
  ],
  359,
);

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const Flight: React.FC<{ i: number; frame: number }> = ({ i, frame }) => {
  const s = START[i], a = ARR[i];
  if (frame < s || frame >= a) return null;
  const blk = ALL[ORDER9[i]];
  const r = rectOf(blk);
  const p = prog(frame, s, a, 'whip');
  const tx = LANE.x + 24, ty = LANE.y + LANE.rowsY + Math.min(i, LANE.cap - 1) * LANE.pitch;
  const dist = Math.hypot(tx - r.x, ty - r.y);
  const arc = Math.sin(Math.PI * p) * (30 + dist * 0.05);
  const q = clamp((p - 0.4) / 0.6);
  return (
    <ToilBlock
      label={blk.label} x={lerp(r.x, tx, p)} y={lerp(r.y, ty, p) - arc} w={lerp(r.w, LANE.rowW, p)} h={lerp(r.h, LANE.rowH, p)}
      bg={mix(C.concrete, C.dPanel, q)} fg={q < 0.5 ? C.ink : C.dFg} bar={mix(blk.night ? C.red : C.asphalt, C.dGreen, q)}
    />
  );
};

const Lane: React.FC<{ frame: number }> = ({ frame }) => {
  const x = tween(frame, 16, 50, 2330, LANE.x, 'land');
  let landed = 0, done = 0;
  for (let i = 0; i < NB; i++) {
    landed += clamp((frame - (ARR[i] - 10)) / 10);
    if (frame >= ARR[i]) done++;
  }
  const s = Math.max(0, landed - LANE.cap);
  const content = 1 - prog(frame, 338, 350, 'out');
  return (
    <div style={{ position: 'absolute', left: x, top: LANE.y, width: LANE.w, height: LANE.h, background: C.ink }}>
      <div style={{ opacity: content }}>
        <div style={{ position: 'absolute', left: 24, top: 28 }}><NemoMark size={48} color={C.dFg} /></div>
        <div style={{ position: 'absolute', left: 24, right: 24, top: 100, display: 'flex', justifyContent: 'space-between', fontFamily: F.mono, fontWeight: 500, fontSize: 18, letterSpacing: '0.08em', color: C.dMuted, lineHeight: '24px' }}>
          <span>HANDED OVER</span>
          <span style={{ color: C.dFg, fontVariantNumeric: 'tabular-nums' }}>{done} / {NB}</span>
        </div>
        <div style={{ position: 'absolute', left: 24, right: 24, top: 136, height: 1, background: C.dLine }} />
        <div style={{ position: 'absolute', left: 24, top: LANE.rowsY, width: LANE.rowW, height: LANE.cap * LANE.pitch - 4, overflow: 'hidden' }}>
          {ORDER9.map((id, i) => {
            if (frame < ARR[i]) return null;
            const b = ALL[id];
            return (
              <ToilBlock key={id + i} label={b.label} x={0} y={(i - s) * LANE.pitch} w={LANE.rowW} h={LANE.rowH}
                bg={C.dPanel} fg={C.dFg} bar={C.dGreen} check={prog(frame, ARR[i], ARR[i] + 10, 'pop')}
                style={{ alignItems: 'center', paddingTop: 0, paddingBottom: 0 }} />
            );
          })}
        </div>
      </div>
    </div>
  );
};

const BUSINESS: { x: number; r: number; rows: number; t: number; title: string }[] = [
  { x: CAL.GX + 2 * CAL.CW + 4, r: 0, rows: 5, t: 206, title: 'New risk dashboard for the board' },
  { x: CAL.GX + 3 * CAL.CW + 4, r: 1, rows: 5, t: 214, title: 'Customer 360 for retail' },
  { x: CAL.GX + 4 * CAL.CW + 4, r: 2, rows: 4, t: 222, title: 'Iceberg roadmap' },
];

export const V09Promise: React.FC = () => {
  const frame = useCurrentFrame();
  // yellow, home again: enters small, then takes its whole day back (the inverse of V01's squeeze)
  const yx = tween(frame, YB, YB + 26, -480, YELLOW_FULL.x, 'land');
  const yh = tween(frame, GROW, GROW + 28, 60, YELLOW_FULL.h, 'snap');
  const yw = tween(frame, GROW + 14, GROW + 44, CAL.CW - 8, YELLOW_FULL.w, 'land');
  const headO = 1 - prog(frame, OUT - 6, OUT + 8, 'pushIn');
  const SZ = 120;
  return (
    <>
      <Camera keys={KEYS} background={C.ground}>
        <WeekGrid />
        {ORDER9.map((id, i) => {
          if (frame >= START[i]) return null;
          const b = ALL[id], r = rectOf(b);
          return <ToilBlock key={id} label={b.label} x={r.x} y={r.y} w={r.w} h={r.h} night={b.night} />;
        })}
        {frame >= YB && <YellowBlock x={yx} y={YELLOW_FULL.y} w={yw} h={yh} title={YELLOW_TITLE} sub={YELLOW_SUB} />}
        {BUSINESS.map((b) => frame >= b.t && (
          <YellowBlock key={b.title} x={b.x} y={CAL.G + b.r * CAL.HR + 2} w={CAL.CW - 8} h={tween(frame, b.t, b.t + 22, 0, b.rows * CAL.HR - 4, 'land')} title={b.title} fs={34} />
        ))}
        {/* the headline lives on the time that came back */}
        <div style={{ position: 'absolute', left: CAL.GX + 1, top: 556, width: 5 * CAL.CW - 1, height: 366, background: C.ground, opacity: prog(frame, HEAD - 2, HEAD + 6, 'out') }} />
        <div style={{ position: 'absolute', left: 232, top: 580, width: 1536, opacity: headO }}>
          <Rule frame={frame} a={HEAD} b={HEAD + 26} w={1536} />
          <div style={{ marginTop: 36, display: 'flex', flexDirection: 'column', rowGap: 6 }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', columnGap: SZ * 0.24 }}>
              <Rise text="LEAVE THE TOIL TO" frame={frame} start={HEAD + 8} size={SZ} stagger={4} />
              <div style={{ width: SZ * 0.5, height: SZ * 0.5, marginBottom: SZ * 0.1, background: C.yellow, transform: `scale(${prog(frame, HEAD + 24, HEAD + 40, 'pop')})` }} />
              <Rise text="NEMO." frame={frame} start={HEAD + 26} size={SZ} />
            </div>
            <Rise text="KEEP THE BUSINESS FOR YOUR PEOPLE." frame={frame} start={HEAD + 40} size={106} stagger={4} />
          </div>
        </div>
        <Lane frame={frame} />
        {ORDER9.map((_, i) => <Flight key={i} i={i} frame={frame} />)}
      </Camera>
      <AbsoluteFill style={{ background: C.ink, opacity: prog(frame, 352, 358, 'out'), pointerEvents: 'none' }} />
    </>
  );
};
