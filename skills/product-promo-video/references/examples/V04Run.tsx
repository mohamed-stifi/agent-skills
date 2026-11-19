import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/tokens';
import { prog, tween, clamp, EaseName } from '../kit/ease';
import { Camera, CamKey } from '../kit/Camera';
import { Rise, Label, Tag, ChapterTag } from '../kit/ui';

const DUR = 420;

/* World: one change card, 1400 x 700, at (260,190). Header 72, four rows of 112, result strip 180. */
const CX = 260, CY = 190, CW = 1400, CH = 700;
const HEAD = 72, RH = 112;
const AT = [24, 66, 148, 184];           // frame each row arrives
const STAMP = 154;                       // the approval stamp lands (decisive snap)
const rowCy = (i: number) => CY + HEAD + RH * i + RH / 2;
const STRIP_Y = CY + HEAD + RH * 4;      // 710

const k = (f: number, x: number, y: number, zoom: number, rx = 0, ry = 0, rz = 0, ease?: EaseName): CamKey => ({ f, x, y, zoom, rx, ry, rz, ease });

const buildKeys = (): CamKey[] => {
  const keys: CamKey[] = [
    k(0, 600, 300, 2.6, 20, -14),
    k(22, 960, 520, 1.1, 0, 0, 0, 'land'),
    k(58, 980, 390, 1.35, 0, 0, 0, 'whip'),
    k(96, 980, 450, 1.35, 0, 0, 0, 'drift'),
    k(128, 980, 500, 1.2, 0, 0, 0, 'drift'),          // anticipation: pull back
    k(158, 780, rowCy(2), 1.8, 0, 0, 0, 'snap'),     // decisive: onto the approval
    k(190, 790, rowCy(2) + 30, 1.85, 0, 0, 0, 'drift'),
    k(212, 960, rowCy(3) + 20, 1.35, 0, 0, 0, 'whip'),
    k(228, 960, 690, 1.35, 0, 0, 0, 'drift'),        // anticipation
    k(256, 960, 800, 1.4, 0, 0, 0, 'snap'),           // onto the result strip
    k(296, 960, 800, 1.45, 0, 0, 0, 'drift'),
    k(322, 960, 540, 1.0, 0, 0, 0, 'land'),
    k(404, 960, 540, 1.04, 0, 0, 0, 'drift'),
  ];
  // exit: exponential push into empty white to the right of the card
  const qx = 1860, qy = 330, cx0 = 960, cy0 = 540, z0 = 1.04;
  for (let f = 405; f <= 419; f++) {
    const e = prog(f, 404, 419, 'linear');
    const z = z0 * Math.pow(60 / z0, e);
    keys.push(k(f, qx + (cx0 - qx) * (z0 / z), qy + (cy0 - qy) * (z0 / z), z, 0, 0, 0, 'linear'));
  }
  return keys;
};
const KEYS = buildKeys();

const Strike: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <s style={{ color: C.red, textDecorationThickness: 3 }}>{children}</s>
);

type RowDef = { time: string; title: string; actor: string; titleColor: string; sub: React.ReactNode };
const rows = (f: number): RowDef[] => {
  const fixP = prog(f, 98, 112, 'out');
  return [
    { time: '02:14', title: 'Failed', actor: 'PROD-B2', titleColor: C.red, sub: <>Out of memory · input 3.1× the 30-day median (412 GB)</> },
    {
      time: '02:16', title: 'Cause found · fix proposed', actor: 'RUN AGENT', titleColor: C.ink,
      sub: (
        <span style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 28 }}>
          executor memory <Strike>8g</Strike>
          <span style={{ display: 'inline-block', opacity: fixP, transform: `translateX(${(1 - fixP) * 16}px)` }}>
            {' '}<span style={{ color: C.asphalt }}>→</span> <b style={{ color: C.green, fontWeight: 600 }}>14g</b>
          </span>
        </span>
      ),
    },
    { time: '02:31:12', title: 'Approved', actor: 'RACHID BENJELLOUN · CHANGE MANAGER', titleColor: C.ink, sub: <>Not the requester · written to the audit log</> },
    { time: '02:31:40', title: 'Executed', actor: 'SALMA IDRISSI · ON-CALL ENGINEER', titleColor: C.ink, sub: <>Rerun on prod-b2 with the approved change</> },
  ];
};

const Card: React.FC<{ f: number }> = ({ f }) => {
  const R = rows(f);
  const ruleP = prog(f, 6, 26, 'out');
  const state: [string, 'red' | 'outline' | 'yellow' | 'ink' | 'green'] =
    f < AT[0] ? ['', 'outline'] : f < AT[1] ? ['Failed', 'red'] : f < AT[2] ? ['Fix proposed', 'outline'] : f < AT[3] ? ['Approved', 'yellow'] : f < 232 ? ['Executed', 'ink'] : ['Done', 'green'];
  const lineH = Math.min(3, 1) * (RH * [1, 2, 3].reduce((a, i) => a + prog(f, AT[i] - 6, AT[i] + 12, 'out'), 0));
  const sp = prog(f, STAMP, STAMP + 12, 'out');
  const ring = prog(f, STAMP, STAMP + 20, 'out');
  const flash = f >= STAMP ? 0.4 * (1 - prog(f, STAMP, STAMP + 26, 'out')) : 0;
  const stripP = prog(f, 232, 252, 'out');
  const count = Math.round(tween(f, 250, 296, 0, 68, 'out'));
  const dim = 1 - 0.88 * prog(f, 298, 322, 'out');

  return (
    <div style={{ position: 'absolute', left: CX, top: CY, width: CW, height: CH, opacity: dim }}>
      <div style={{ position: 'absolute', inset: 0, border: `1.5px solid ${C.ink}`, boxSizing: 'border-box', background: C.ground }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: CW, height: 3, background: C.ink, transformOrigin: '0 50%', transform: `scaleX(${ruleP})` }} />
      {/* header */}
      <div style={{ position: 'absolute', left: 0, top: 3, width: CW, height: HEAD - 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 40px', boxSizing: 'border-box', borderBottom: `1px solid ${C.hairline}`, opacity: prog(f, 8, 22, 'out') }}>
        <div style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 22, letterSpacing: '0.04em', color: C.ink }}>
          CHG-48213 · settlement_load_daily · prod-b2 · tier 2
        </div>
        {state[0] && <Tag kind={state[1]} size={18} style={{ fontWeight: 600, textTransform: 'uppercase' }}>{state[0]}</Tag>}
      </div>
      {/* timeline spine */}
      <div style={{ position: 'absolute', left: 330 - 1.5, top: HEAD + RH / 2, width: 3, height: lineH, background: C.ink }} />
      {/* approval row flash */}
      <div style={{ position: 'absolute', left: 0, top: HEAD + RH * 2, width: CW, height: RH, background: C.yellow, opacity: flash }} />
      {R.map((r, i) => {
        const p = prog(f, AT[i], AT[i] + 18, 'out');
        const op = clamp((f - AT[i]) / 6);
        const top = HEAD + RH * i;
        const mp = prog(f, AT[i], AT[i] + 14, 'pop');
        const approved = i === 2;
        return (
          <div key={i} style={{ position: 'absolute', left: 0, top, width: CW, height: RH, opacity: op, borderBottom: i < 3 ? `1px solid ${C.hairline}` : undefined, boxSizing: 'border-box' }}>
            <div style={{ position: 'absolute', left: 40, top: 0, height: RH, width: 270, display: 'flex', alignItems: 'center', fontFamily: F.display, fontWeight: 800, fontSize: 64, letterSpacing: '-0.01em', fontVariantNumeric: 'tabular-nums', color: C.ink, transform: `translateX(${(1 - p) * -40}px)` }}>{r.time}</div>
            {/* marker */}
            {!approved && (
              <div style={{ position: 'absolute', left: 330 - 14, top: RH / 2 - 14, width: 28, height: 28, background: i === 0 ? C.red : i === 3 ? C.ink : C.ground, border: i === 1 ? `3px solid ${C.ink}` : undefined, boxSizing: 'border-box', transform: `scale(${mp})` }} />
            )}
            {approved && (
              <>
                <div style={{ position: 'absolute', left: 330 - 22 - 22 * ring * 1.2, top: RH / 2 - 22 - 22 * ring * 1.2, width: 44 + 44 * ring * 1.2, height: 44 + 44 * ring * 1.2, border: `3px solid ${C.yellow}`, boxSizing: 'border-box', opacity: f >= STAMP ? 1 - ring : 0 }} />
                <div style={{ position: 'absolute', left: 330 - 22, top: RH / 2 - 22, width: 44, height: 44, background: C.yellow, border: `3px solid ${C.ink}`, boxSizing: 'border-box', opacity: f >= STAMP - 3 ? 1 : 0, transform: `scale(${f >= STAMP ? 1 + 1.8 * (1 - sp) : 0.0001})` }} />
              </>
            )}
            <div style={{ position: 'absolute', left: 380, top: 0, height: RH, right: 40, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 6, transform: `translateX(${(1 - p) * 40}px)` }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 20, whiteSpace: 'nowrap' }}>
                <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 46, lineHeight: 1, textTransform: 'uppercase', letterSpacing: '-0.01em', color: r.titleColor }}>{r.title}</div>
                <Label size={18} color={C.asphalt} style={{ fontWeight: 500 }}>{r.actor}</Label>
              </div>
              <div style={{ fontFamily: F.body, fontWeight: 500, fontSize: 28, lineHeight: '32px', color: C.ink, whiteSpace: 'nowrap' }}>{r.sub}</div>
            </div>
          </div>
        );
      })}
      {/* result strip */}
      <div style={{ position: 'absolute', left: 0, top: HEAD + RH * 4, width: CW, height: CH - HEAD - RH * 4, boxSizing: 'border-box' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: CW, height: 3, background: C.ink, transformOrigin: '0 50%', transform: `scaleX(${stripP})` }} />
        <div style={{ position: 'absolute', left: 40, top: 0, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 10, opacity: stripP }}>
          <Label size={22} color={C.ink} style={{ fontWeight: 600 }}>04:52 · reg_liquidity_feed submitted</Label>
          <div style={{ fontFamily: F.body, fontWeight: 500, fontSize: 28, color: C.asphalt }}>Regulatory deadline 06:00</div>
        </div>
        <div style={{ position: 'absolute', right: 56, top: 0, height: '100%', display: 'flex', alignItems: 'center', gap: 28, opacity: clamp((f - 248) / 5) }}>
          <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 190, lineHeight: '170px', letterSpacing: '-0.02em', color: C.green, fontVariantNumeric: 'tabular-nums', minWidth: 200, textAlign: 'right' }}>{count}</div>
          <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 84, lineHeight: '76px', letterSpacing: '-0.02em', color: C.green, transform: `translateX(${(1 - prog(f, 262, 282, 'land')) * 40}px)`, opacity: prog(f, 262, 272, 'out') }}>MIN TO<br />SPARE</div>
        </div>
      </div>
    </div>
  );
};

export const V04Run: React.FC = () => {
  const f = useCurrentFrame();
  const out = prog(f, 404, 416, 'pushIn');
  return (
    <AbsoluteFill style={{ background: C.ground }}>
      <Camera keys={KEYS} background={C.ground}>
        <Card f={f} />
      </Camera>
      <div style={{ position: 'absolute', left: 150, top: 430, opacity: 1 - out, transform: `translateX(${out * 420}px)` }}>
        {f >= 304 && <Rise text="Handled before the morning." frame={f} start={304} stagger={6} dur={24} size={150} style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap' }} />}
      </div>
      <ChapterTag n={1} name="Run" line="Nights without the 02:14 page" frame={f} end={130} />
    </AbsoluteFill>
  );
};
