import React from 'react';
import { C, F } from '../kit/tokens';
import { Cam, CamKey } from '../kit/Camera';
import { keyed, clamp } from '../kit/ease';

// The shared calendar: V01 fills it with toil, V09 empties it again. One component set, one grid.

/** World geometry (px). Everything is a multiple of 4. */
export const CAL = { L: 120, R: 1800, GX: 200, CW: 320, G: 152, HR: 64, NY: 928, NH: 80 } as const;

export type Toil = { id: string; d: number; r: number; h: number; label: string; night?: boolean };
const D = (d: number, r: number, h: number, label: string): Toil => ({ id: `${d}-${r}`, d, r, h, label });
const N = (d: number, label: string): Toil => ({ id: `n${d}`, d, r: 0, h: 1, label, night: true });

export const DAY_BLOCKS: Toil[] = [
  D(0, 0, 1, 'handover notes'), D(0, 1, 2, 'rerun settlement_load_daily'), D(0, 3, 1, 'ticket: stg.settlements stale'),
  D(0, 4, 2, 'Teradata row counts, wave W6'), D(0, 6, 1, 'Spark sizing review'), D(0, 7, 2, 'reconcile FINDW'),
  D(0, 9, 1, 'cost report for finance'), D(0, 10, 2, 'HDFS at 78 %, plan space'),
  D(1, 0, 2, 'Airflow DAG backfill'), D(1, 2, 1, 'Kafka lag on cdr.raw'), D(1, 3, 3, 'reconcile FINDW'),
  D(1, 6, 2, 'ticket: lineage request'), D(1, 8, 1, 'access review export'), D(1, 9, 3, 'rerun crm_segment_refresh'),
  D(2, 0, 1, 'rebalance Kafka partitions'), D(2, 1, 2, 'Teradata row counts, wave W6'), D(2, 3, 2, 'cost report for finance'),
  D(2, 5, 1, 'ticket: stg.settlements stale'), D(2, 6, 2, 'Spark sizing review'), D(2, 8, 1, 'schema drift: cdr_daily'),
  D(2, 9, 3, 'partition cleanup: raw zone'),
  D(3, 0, 2, 'rerun settlement_load_daily'), D(3, 2, 1, 'on-call handover'), D(3, 3, 2, 'HDFS at 78 %, plan space'),
  D(3, 5, 2, 'reg_liquidity_feed check'), D(3, 7, 1, 'Kafka lag on cdr.raw'), D(3, 8, 2, 'reconcile FINDW'),
  D(3, 10, 2, 'patch window: batch hosts'),
  D(4, 0, 2, 'cost report for finance'), D(4, 2, 2, 'ticket: stg.settlements stale'), D(4, 4, 1, 'handover notes'),
  D(4, 5, 3, 'Spark sizing review'), D(4, 8, 1, 'access review export'), D(4, 9, 3, 'rerun crm_segment_refresh'),
];
export const NIGHT_BLOCKS: Toil[] = [
  N(0, 'night batch: rerun failed jobs'), N(1, 'page: cdr.raw lag'), N(2, '02:14 page: prod-b2'),
  N(3, 'stuck replication: restart'), N(4, 'page: feed late'),
];
export const ALL: Record<string, Toil> = Object.fromEntries([...DAY_BLOCKS, ...NIGHT_BLOCKS].map((t) => [t.id, t]));
export const HERO_ID = 'n2';

export const rectOf = (t: Toil) =>
  t.night
    ? { x: CAL.GX + t.d * CAL.CW + 4, y: CAL.NY + 4, w: CAL.CW - 8, h: CAL.NH - 8 }
    : { x: CAL.GX + t.d * CAL.CW + 4, y: CAL.G + t.r * CAL.HR + 2, w: CAL.CW - 8, h: t.h * CAL.HR - 4 };

/** The order toil lands in V01 (V09 plays it backwards). The first dozen respect the yellow block's squeeze. */
export const ORDER: string[] = [
  '0-6', '1-6', '0-7', '1-8', '1-9', '0-9', '0-10', '0-4', '1-3', '0-3', '1-2', '1-0',
  '2-9', '3-10', '4-9', '2-8', '3-8', '4-8', '2-6', '3-7', '4-5', '2-5', '3-5', '4-4', '2-3', '3-3', '4-2', '2-1', '3-2', '4-0', '2-0', '3-0',
  'n0', 'n1', 'n3', 'n4', '0-1', 'n2',
];

const DAYS = ['MON 9 NOV', 'TUE 10 NOV', 'WED 11 NOV', 'THU 12 NOV', 'FRI 13 NOV'];

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mix = (a: string, b: string, t: number) => {
  const A = hex(a), B = hex(b);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`;
};

/** Densify a camera path and bank it into the motion: tilt leans toward the direction of travel, lands frontal at rest. */
export const bank = (keys: CamKey[], end: number, kx = 0.08, ky = 0.05, max = 16): CamKey[] => {
  const out: CamKey[] = [];
  for (let f = 0; f <= end; f++) {
    const c = keyed<Cam>(f, keys), a = keyed<Cam>(f - 1, keys), b = keyed<Cam>(f + 1, keys);
    const vx = ((b.x - a.x) / 2) * c.zoom, vy = ((b.y - a.y) / 2) * c.zoom;
    out.push({ f, ease: 'linear', x: c.x, y: c.y, zoom: c.zoom, rx: c.rx + clamp(vy * ky, -max * 0.7, max * 0.7), ry: c.ry - clamp(vx * kx, -max, max), rz: c.rz });
  }
  return out;
};

const lab: React.CSSProperties = { position: 'absolute', fontFamily: F.mono, fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', whiteSpace: 'nowrap' };

/** Hairline grid, mono day headers, 3 px ink rule, hour gutter and night band. Pure structure, no blocks. */
export const WeekGrid: React.FC = () => {
  const { L, R, GX, CW, G, HR, NY, NH } = CAL;
  const hours = Array.from({ length: 13 }, (_, i) => i);
  return (
    <>
      <div style={{ ...lab, left: L, top: 48, fontSize: 18, lineHeight: '24px', color: C.asphalt }}>DATA PLATFORM · ATLAS BANK · WEEK 46</div>
      <div style={{ ...lab, right: 1920 - R, top: 48, fontSize: 18, lineHeight: '24px', color: C.asphalt }}>TEAM CALENDAR · 08:00–20:00 + NIGHT</div>
      {DAYS.map((d, i) => (
        <div key={d} style={{ ...lab, left: GX + i * CW + 12, top: 104, fontSize: 20, lineHeight: '40px', color: C.ink }}>{d}</div>
      ))}
      <div style={{ position: 'absolute', left: L, top: 144, width: R - L, height: 3, background: C.ink }} />
      <div style={{ position: 'absolute', left: GX, top: NY, width: 5 * CW, height: NH, background: C.panel }} />
      {hours.map((i) => (
        <div key={i} style={{ position: 'absolute', left: GX, top: G + i * HR, width: 5 * CW, height: 1, background: C.hairline }} />
      ))}
      <div style={{ position: 'absolute', left: GX, top: NY, width: 5 * CW, height: 1, background: C.hairline }} />
      <div style={{ position: 'absolute', left: GX, top: NY + NH, width: 5 * CW, height: 1, background: C.hairline }} />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <div key={i} style={{ position: 'absolute', left: GX + i * CW, top: 147, width: 1, height: NY + NH - 147, background: C.hairline }} />
      ))}
      {hours.map((i) => (
        <div key={i} style={{ ...lab, left: L, width: 72, textAlign: 'right', top: G + i * HR - 10, fontSize: 16, lineHeight: '20px', color: C.asphalt, letterSpacing: '0.04em', fontVariantNumeric: 'tabular-nums' }}>
          {String(8 + i).padStart(2, '0')}:00
        </div>
      ))}
      <div style={{ ...lab, left: L, width: 72, textAlign: 'right', top: NY + NH / 2 - 10, fontSize: 16, lineHeight: '20px', color: C.asphalt }}>NIGHT</div>
    </>
  );
};

/** Square check icon (drawn, not an emoji). */
export const Check: React.FC<{ size?: number; scale?: number; color?: string }> = ({ size = 20, scale = 1, color = C.dGreen }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" style={{ flexShrink: 0, transform: `scale(${scale})` }}>
    <rect width="20" height="20" fill={color} />
    <path d="M5 10.5 L8.8 14 L15.5 6.2" stroke={C.ink} strokeWidth="2.6" fill="none" strokeLinecap="square" />
  </svg>
);

/** A grey toil block (or, restyled via props, a done row in the NEMO lane). */
export const ToilBlock: React.FC<{
  label: string; x: number; y: number; w: number; h: number; night?: boolean;
  bg?: string; fg?: string; bar?: string; edge?: string; check?: number; style?: React.CSSProperties;
}> = ({ label, x, y, w, h, night = false, bg = C.concrete, fg = C.ink, bar, edge, check = 0, style }) => (
  <div
    style={{
      position: 'absolute', left: x, top: y, width: w, height: h, boxSizing: 'border-box', background: bg, color: fg, overflow: 'hidden',
      border: night ? `1.5px solid ${edge ?? C.red}` : 'none',
      borderLeft: `${night ? 4 : 3}px solid ${bar ?? (night ? C.red : C.asphalt)}`,
      padding: '6px 12px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8,
      fontFamily: F.mono, fontWeight: 500, fontSize: 18, lineHeight: '22px', ...style,
    }}
  >
    <span>{label}</span>
    {check > 0 && <Check size={20} scale={check} />}
  </div>
);

/** The business work that matters. Type scales with the block so it survives the squeeze. */
export const YellowBlock: React.FC<{ x: number; y: number; w: number; h: number; title: string; sub?: string; fs?: number }> = ({ x, y, w, h, title, sub, fs }) => {
  const size = fs ?? clamp(22 + (h - 60) * (24 / 320), 22, 46);
  const subO = sub ? clamp((h - 150) / 50) : 0;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, height: Math.max(0, h), background: C.yellow, color: C.ink, overflow: 'hidden', boxSizing: 'border-box', padding: '10px 16px', fontFamily: F.body, fontWeight: 600 }}>
      <div style={{ fontSize: size, lineHeight: 1.08, opacity: clamp(h / 40) }}>{title}</div>
      {sub && <div style={{ fontSize: 26, lineHeight: 1.15, marginTop: 8, fontWeight: 500, opacity: subO }}>{sub}</div>}
    </div>
  );
};

export const YELLOW_FULL = { x: CAL.GX + 4, y: CAL.G + 2, w: 2 * CAL.CW - 8, h: 6 * CAL.HR - 4 };
export const YELLOW_TITLE = 'Liquidity data product';
export const YELLOW_SUB = 'the project that matters';
