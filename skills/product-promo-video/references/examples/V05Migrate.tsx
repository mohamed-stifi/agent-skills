import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/tokens';
import { prog, clamp, EaseName } from '../kit/ease';
import { Camera, CamKey } from '../kit/Camera';
import { Rise, Label, ChapterTag } from '../kit/ui';

const DUR = 360;

/* World: twelve cells in a row (centre line y = 0), the gate at the end, findings below. */
const CELL = 120, STEP = 148;
const cellX = (n: number) => (n - 1) * STEP;            // left edge of cell n (1..12)
const cellCx = (n: number) => cellX(n) + CELL / 2;
const GATE_X = cellX(12) + CELL + 80, GATE_W = 420, GATE_H = 300;
const GATE_CX = GATE_X + GATE_W / 2;

// frame each cycle flips; 1-2 fail, 3-12 pass, accelerating
const FT: Record<number, number> = { 1: 30, 2: 102, 3: 172, 4: 186, 5: 198, 6: 208, 7: 217, 8: 225, 9: 232, 10: 238, 11: 243, 12: 248 };
const FAIL = (n: number) => n <= 2;
const GATE_OPEN = 268;

const k = (f: number, x: number, y: number, zoom: number, rx = 0, ry = 0, rz = 0, ease?: EaseName): CamKey => ({ f, x, y, zoom, rx, ry, rz, ease });

const rideX = (f: number) => {
  for (let n = 3; n < 12; n++) {
    if (f <= FT[n + 1]) {
      const u = (f - FT[n]) / (FT[n + 1] - FT[n]);
      return cellCx(n) + (cellCx(n + 1) - cellCx(n)) * u + 220;
    }
  }
  return cellCx(12) + 220;
};

const buildKeys = (): CamKey[] => {
  const keys: CamKey[] = [
    k(0, 300, -90, 3.0, 18, -14),
    k(22, 560, -110, 1.3, 0, -8, 0, 'land'),
    k(40, 560, -110, 1.32, 0, -8, 0, 'drift'),
    k(54, 400, 400, 1.6, 0, 0, 0, 'whip'),        // dip: read cycle 1
    k(92, 410, 420, 1.62, 0, 0, 0, 'drift'),
    k(100, 330, 190, 1.4, 0, 0, 0, 'whip'),       // back to the row
    k(112, 330, 190, 1.42, 0, 0, 0, 'drift'),
    k(124, 400, 470, 1.6, 0, 0, 0, 'whip'),       // dip: read cycle 2
    k(160, 410, 480, 1.62, 0, 0, 0, 'drift'),
    k(172, rideX(172), 60, 1.35, 0, -8, 0, 'whip'),
  ];
  for (let f = 174; f <= 248; f += 2) keys.push(k(f, rideX(f), 60, 1.35, 0, -8, 0, 'linear'));
  keys.push(
    k(254, cellCx(12) + 120, 40, 1.28, 0, -4, 0, 'drift'),   // anticipation
    k(274, GATE_CX, 0, 1.75, 0, 0, 0, 'snap'),               // decisive: onto the gate
    k(310, GATE_CX + 10, 0, 1.8, 0, 0, 0, 'drift'),
    k(332, 1125, -40, 0.8, 0, 0, 0, 'land'),
    k(342, 1125, -40, 0.82, 0, 0, 0, 'drift'),
  );
  const qx = GATE_X + GATE_W + 90, qy = -40, cx0 = 1125, cy0 = -40, z0 = 0.82;
  for (let f = 343; f <= 359; f++) {
    const e = prog(f, 342, 359, 'linear');
    const z = z0 * Math.pow(60 / z0, e);
    keys.push(k(f, qx + (cx0 - qx) * (z0 / z), qy + (cy0 - qy) * (z0 / z), z, 0, 0, 0, 'linear'));
  }
  return keys;
};
const KEYS = buildKeys();

const Check: React.FC<{ s: number }> = ({ s }) => (
  <svg width={s} height={s} viewBox="0 0 24 24"><polyline points="4,13 9.5,18.5 20,6" fill="none" stroke={C.ground} strokeWidth={3.4} strokeLinecap="butt" strokeLinejoin="miter" /></svg>
);

const Cell: React.FC<{ n: number; f: number }> = ({ n, f }) => {
  const ft = FT[n];
  const t = clamp((f - ft) / 9);
  const res = f >= ft && t >= 0.5;
  const sx = f < ft ? 1 : t < 0.5 ? 1 - 2 * t : 2 * t - 1;
  const fail = FAIL(n);
  const bg = !res ? C.ground : fail ? C.red : C.green;
  const bd = !res ? C.ink : bg;
  const lblC = !res ? C.asphalt : fail ? C.red : C.green;
  return (
    <div style={{ position: 'absolute', left: cellX(n), top: -CELL / 2, width: CELL }}>
      <div style={{ width: CELL, height: CELL, background: bg, border: `${res ? 0 : 1.5}px solid ${bd}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scaleX(${sx})`, opacity: res ? 1 : 1 }}>
        {res && fail && <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 44, color: C.ground, letterSpacing: '0.02em' }}>FAIL</div>}
        {res && !fail && <Check s={64} />}
      </div>
      <div style={{ marginTop: 12, textAlign: 'center', fontFamily: F.mono, fontWeight: res ? 600 : 500, fontSize: 22, letterSpacing: '0.08em', color: lblC, fontVariantNumeric: 'tabular-nums' }}>{String(n).padStart(2, '0')}</div>
    </div>
  );
};

const Finding: React.FC<{ f: number; at: number; top: number; h: number; cycle: number; lines: React.ReactNode[] }> = ({ f, at, top, h, cycle, lines }) => {
  const p = prog(f, at, at + 20, 'out');
  return (
    <div style={{ position: 'absolute', left: 0, top, width: 860, height: h, opacity: clamp((f - at) / 8) * (1 - prog(f, 160, 176, 'out')) }}>
      <div style={{ height: 3, background: C.red, width: 860 * p }} />
      <div style={{ paddingTop: 14, transform: `translateY(${(1 - p) * 24}px)` }}>
        <Label size={20} color={C.red} style={{ fontWeight: 600, marginBottom: 10 }}>CYCLE {cycle} · FAIL</Label>
        {lines.map((l, i) => <div key={i} style={{ marginBottom: 6 }}>{l}</div>)}
      </div>
    </div>
  );
};
const mono = (s: React.ReactNode) => <span style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 24, color: C.ink }}>{s}</span>;
const body = (s: React.ReactNode, c: string = C.ink) => <span style={{ fontFamily: F.body, fontWeight: 500, fontSize: 28, color: c }}>{s}</span>;

const Gate: React.FC<{ f: number }> = ({ f }) => {
  const open = prog(f, GATE_OPEN, GATE_OPEN + 18, 'snap');
  const appear = prog(f, 12, 30, 'out');
  const flip = f >= GATE_OPEN + 4;
  return (
    <div style={{ position: 'absolute', left: GATE_X, top: -GATE_H / 2, width: GATE_W, height: GATE_H, opacity: appear, boxSizing: 'border-box', border: `3px solid ${C.ink}`, background: C.ground, overflow: 'hidden' }}>
      <div style={{ height: 56, borderBottom: `1.5px solid ${C.ink}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', padding: '0 20px', fontFamily: F.mono, fontWeight: 600, fontSize: 22, letterSpacing: '0.08em', color: C.ink }}>CUTOVER GATE</div>
      {/* READY (yellow, a human decision) sits under the DENY panel */}
      <div style={{ position: 'absolute', left: 0, top: 56, right: 0, bottom: 0, background: C.yellow, padding: '16px 20px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 120, lineHeight: '104px', letterSpacing: '-0.02em', color: C.ink, transform: flip ? `scale(${1 + 0.0 * open})` : undefined }}>READY</div>
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 28, lineHeight: '32px', color: C.ink, marginTop: 8 }}>waits for the owner's signature</div>
      </div>
      <div style={{ position: 'absolute', left: 0, top: 56, right: 0, bottom: 0, background: C.red, padding: '16px 20px', boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'center', transform: `translateY(${-open * 110}%)` }}>
        <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 120, lineHeight: '104px', letterSpacing: '-0.02em', color: C.ground }}>DENY</div>
        <div style={{ fontFamily: F.body, fontWeight: 500, fontSize: 26, lineHeight: '30px', color: C.ground, marginTop: 8 }}>until 10/10 passes and the owner signs</div>
      </div>
    </div>
  );
};

export const V05Migrate: React.FC = () => {
  const f = useCurrentFrame();
  const passes = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12].filter((n) => f >= FT[n] + 5).length;
  const dim = 1 - 0.86 * prog(f, 308, 332, 'out');
  const hdrOp = 1 - 0.9 * prog(f, 90, 110, 'out');
  const out = prog(f, 342, 357, 'pushIn');
  const cnt = prog(f, 20, 40, 'out');
  const cntDim = 1 - prog(f, 306, 326, 'out');
  const done = passes === 10;

  return (
    <AbsoluteFill style={{ background: C.ground }}>
      <Camera keys={KEYS} background={C.ground}>
        <div style={{ opacity: dim }}>
          {/* header */}
          <div style={{ position: 'absolute', left: 0, top: -340, opacity: hdrOp * prog(f, 6, 22, 'out') }}>
            <Label size={24} color={C.asphalt} style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>MIG-0007 · FINDW → lakehouse · wave W6 · 57 objects</Label>
            <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 96, lineHeight: '96px', letterSpacing: '-0.02em', color: C.ink, marginTop: 12, whiteSpace: 'nowrap' }}>FINDW.REG_LIQUIDITY_DAILY</div>
            <div style={{ height: 3, background: C.ink, width: 1100 * prog(f, 10, 34, 'out'), marginTop: 14 }} />
          </div>
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((n) => <Cell key={n} n={n} f={f} />)}
          <Finding f={f} at={FT[1] + 12} top={170} h={150} cycle={1} lines={[
            mono('sum(hqla_amount_mad) differs by 1,904,455.20'),
            body('212 keys · cause: lower-case ccy_code · fixed'),
          ]} />
          <Finding f={f} at={FT[2] + 12} top={350} h={210} cycle={2} lines={[
            mono('3 rows differ by 0.01 · rounding'),
            body('Tolerance declined by the owner'),
            body('Imane Tazi: "a regulatory amount must match exactly"', C.asphalt),
          ]} />
          <Gate f={f} />
        </div>
      </Camera>

      {/* passes counter, screen space */}
      <div style={{ position: 'absolute', left: 64, bottom: 56, opacity: cnt * cntDim, transform: `translateY(${(1 - cnt) * 30}px)` }}>
        <Label size={22} color={C.asphalt} style={{ fontWeight: 600 }}>PASSES IN A ROW</Label>
        <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 150, lineHeight: '136px', letterSpacing: '-0.02em', fontVariantNumeric: 'tabular-nums', color: done ? C.green : C.ink }}>
          {String(passes).padStart(2, '0')}<span style={{ color: C.asphalt, fontSize: 90 }}>/10</span>
        </div>
      </div>

      <div style={{ position: 'absolute', left: 150, top: 400, opacity: 1 - out, transform: `translateX(${out * 420}px)` }}>
        {f >= 314 && <Rise text="No cutover without proof." frame={f} start={314} stagger={6} dur={24} size={150} style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap' }} />}
      </div>
      <ChapterTag n={2} name="Migrate" line="Teradata to the lakehouse, with proof" frame={f} end={DUR} />
    </AbsoluteFill>
  );
};
