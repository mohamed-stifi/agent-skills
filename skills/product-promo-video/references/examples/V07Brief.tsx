import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Camera, CamKey } from '../kit/Camera';
import { prog } from '../kit/ease';
import { C, F } from '../kit/tokens';
import { Label, Rise, ChapterTag, Tag, NemoMark } from '../kit/ui';

const DUR = 390;

// ---- world geometry ----
const CL = 360, CW = 1200, CT = 180, CH = 880;
const S1_T = 96, S1_H = 240;
const S2_T = 336, S2_H = 88;
const S3_T = 424, S3_H = 456;

const k = (f: number, x: number, y: number, zoom: number, rx = 0, ry = 0, ease?: CamKey['ease']): CamKey => ({ f, x, y, zoom, rx, ry, rz: 0, ease });

const KEYS: CamKey[] = [
  k(0, 540, 280, 5, 14, -14),
  k(24, 960, 410, 1.4, 3, -5, 'land'),
  k(84, 960, 430, 1.42, 0, 0, 'drift'),
  k(112, 960, 560, 1.5, 0, 0, 'whip'),
  k(134, 960, 570, 1.52, 0, 0, 'drift'),
  // the decisive move: onto "Needs you today (3)"
  k(174, 960, 862, 1.45, 0, 0, 'snap'),
  k(250, 960, 866, 1.48, 0, 0, 'drift'),
  k(284, 960, 540, 1.0, 0, 0, 'whip'),
  k(372, 960, 540, 1.03, 0, 0, 'drift'),
  k(389, 1700, 900, 30, 0, 0, 'pushIn'),
];

type Stat = { v: number; label: string; color: string; a: number };
const STATS: Stat[] = [
  { v: 1284, label: 'jobs ran', color: C.ink, a: 32 },
  { v: 1281, label: 'OK at first attempt', color: C.green, a: 40 },
  { v: 3, label: 'failed', color: C.red, a: 48 },
  { v: 2, label: 'recovered', color: C.ink, a: 56 },
];

const mono = (t: string) => <span style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 28, letterSpacing: '0.01em' }}>{t}</span>;

type Item = { n: number; head: React.ReactNode; sub: string; a: number };
const ITEMS: Item[] = [
  { n: 1, head: <>Approve or reject {mono('APR-9931')}</>, sub: 'rerun crm_segment_refresh after the cast fix · Youssef Amrani · by 10:00', a: 176 },
  { n: 2, head: <>Post-implementation review of {mono('CHG-48213')}</>, sub: 'Salma Idrissi · Rachid Benjelloun', a: 190 },
  { n: 3, head: <>Sign or reject the learned runbook {mono('RBP-0147')}</>, sub: 'Youssef Amrani', a: 204 },
];

export const V07Brief: React.FC = () => {
  const f = useCurrentFrame();
  const cardOp = (1 - 0.9 * prog(f, 256, 282, 'out')) * prog(f, 0, 5, 'out');
  const upperOp = 1 - prog(f, 146, 176, 'out');
  const barP = prog(f, 168, 190, 'out');

  return (
    <AbsoluteFill style={{ background: C.ground }}>
      <Camera keys={KEYS} background={C.ground}>
        <div style={{ position: 'absolute', left: CL, top: CT, width: CW, height: CH, boxSizing: 'border-box', border: `1.5px solid ${C.ink}`, borderTop: `3px solid ${C.ink}`, opacity: cardOp }}>
          {/* header row */}
          <div style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: S1_T - 3, display: 'flex', alignItems: 'center', gap: 28, paddingLeft: 32, paddingRight: 32, boxSizing: 'border-box', opacity: prog(f, 4, 18, 'out') }}>
            <NemoMark size={32} />
            <div style={{ width: 1.5, height: 36, background: C.hairline }} />
            <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.ink, whiteSpace: 'nowrap', flex: 1 }}>Morning brief · Data Platform · Thu 12 Nov 2026 · 07:30</div>
            <Tag kind="ink" size={20}>AMBER</Tag>
          </div>

          {/* overnight */}
          <div style={{ position: 'absolute', left: 0, top: S1_T - 3, width: '100%', height: S1_H, borderTop: `1.5px solid ${C.ink}`, opacity: upperOp }}>
            <Label size={18} style={{ position: 'absolute', left: 32, top: 24, opacity: prog(f, 20, 32, 'out') }}>OVERNIGHT</Label>
            {STATS.map((s, i) => {
              const p = prog(f, s.a - 8, s.a + 12, 'land');
              const cnt = Math.round(s.v * prog(f, s.a, s.a + (s.v > 100 ? 40 : 14), 'out'));
              return (
                <div key={s.label} style={{ position: 'absolute', left: 32 + i * 284, top: 60, width: 270, opacity: Math.min(1, p * 3), transform: `translateY(${(1 - p) * 22}px)` }}>
                  <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 108, lineHeight: '104px', letterSpacing: '-0.02em', color: s.color, fontVariantNumeric: 'tabular-nums' }}>{cnt.toLocaleString('en-US')}</div>
                  <Label size={18} color={C.asphalt} style={{ marginTop: 8 }}>{s.label}</Label>
                </div>
              );
            })}
          </div>

          {/* deadline met */}
          <div style={{ position: 'absolute', left: 0, top: S2_T - 3, width: '100%', height: S2_H, borderTop: `1px solid ${C.hairline}`, display: 'flex', alignItems: 'center', gap: 20, paddingLeft: 32, opacity: prog(f, 98, 112, 'out') * upperOp, transform: `translateX(${(1 - prog(f, 98, 116, 'out')) * -30}px)` }}>
            <div style={{ width: 16, height: 16, background: C.green }} />
            <div style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 26, color: C.ink }}>reg_liquidity_feed</div>
            <div style={{ fontFamily: F.mono, fontWeight: 600, fontSize: 26, color: C.green, letterSpacing: '0.04em' }}>MET · 68 MIN SLACK</div>
          </div>

          {/* needs you today */}
          <div style={{ position: 'absolute', left: 0, top: S3_T - 3, width: '100%', height: S3_H, borderTop: `1.5px solid ${C.ink}` }}>
            <div style={{ position: 'absolute', left: 0, top: 0, width: 12, height: S3_H, background: C.yellow, transformOrigin: '50% 0', transform: `scaleY(${barP})` }} />
            <div style={{ position: 'absolute', left: 44, top: 24, fontFamily: F.display, fontWeight: 800, fontSize: 76, lineHeight: '76px', letterSpacing: '-0.02em', color: C.ink, textTransform: 'uppercase', opacity: prog(f, 150, 166, 'out') }}>
              Needs you today (3)
            </div>
            {ITEMS.map((it, i) => {
              const p = prog(f, it.a, it.a + 18, 'land');
              return (
                <div key={it.n} style={{ position: 'absolute', left: 44, right: 32, top: 124 + i * 104, height: 104, borderTop: `1px solid ${C.hairline}`, display: 'flex', alignItems: 'center', gap: 24, opacity: Math.min(1, p * 3), transform: `translateY(${(1 - p) * 26}px)` }}>
                  <div style={{ width: 44, height: 44, boxSizing: 'border-box', border: `1.5px solid ${C.ink}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.mono, fontWeight: 600, fontSize: 24, color: C.ink, flexShrink: 0 }}>{it.n}</div>
                  <div>
                    <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 32, color: C.ink, lineHeight: 1.15 }}>{it.head}</div>
                    <div style={{ marginTop: 6, fontFamily: F.mono, fontWeight: 500, fontSize: 20, color: C.asphalt }}>{it.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* headline */}
        <div style={{ position: 'absolute', left: 280, top: 390 }}>
          <Rise text="While you slept: 1,284 jobs." frame={f} start={272} stagger={5} size={120} style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap' }} />
          <Rise text="3 need you." frame={f} start={292} stagger={5} size={120} style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap', marginTop: 8 }} />
          <div style={{ marginTop: 20, width: 220 * prog(f, 304, 330, 'out'), height: 12, background: C.yellow }} />
        </div>
      </Camera>
      <ChapterTag n={4} name="Brief" line="Every morning at 07:30" frame={f} end={DUR} />
    </AbsoluteFill>
  );
};
