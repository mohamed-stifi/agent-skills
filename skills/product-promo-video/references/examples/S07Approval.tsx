import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/tokens';
import { prog, tween, EaseName, E } from '../kit/ease';
import { Camera, CamKey } from '../kit/Camera';
import { Rise, Label, Tag, Cursor } from '../kit/ui';

/* ------------------------------------------------------------------ */
/* World (px). Part 1: the approval screen, centred on (0,0).           */
/* Part 2: three identities, centred on (0,1290).                       */
/* ------------------------------------------------------------------ */

const PX = 360;          // decision panel left
const PY = -466;         // decision panel top
const PW = 640;
const PAD = 44;
const PH = 932;
const BTN_Y = PY + 564;  // approve button top (world)
const BTN_H = 80;
const BTN_CX = PX + PW / 2;
const BTN_CY = BTN_Y + BTN_H / 2;

const CLICK = 134;       // cursor press frame
const STAMP = 138;       // label becomes the approval stamp

const LINE_A = 216, LINE_B = 296;
const LINE_X0 = -950, LINE_X1 = 950, LINE_Y = 1360;
const BLOCK_W = 540, BLOCK_H = 360, BLOCK_Y = 1180;
const BLOCK_X = [-950, -270, 410];

const cursorAt = (f: number) => {
  const t = prog(f, 56, 128, 'whip');
  const sx = -100, sy = 520, ex = BTN_CX + 24, ey = BTN_CY + 12;
  return { x: sx + (ex - sx) * t, y: sy + (ey - sy) * t + Math.sin(Math.PI * t) * 90 };
};

const headX = (f: number) => LINE_X0 + (LINE_X1 - LINE_X0) * prog(f, LINE_A, LINE_B, 'drift');
const blockStart = BLOCK_X.map((bx) => {
  for (let f = LINE_A; f <= LINE_B; f++) if (headX(f) >= bx - 20) return f;
  return LINE_B;
});

const k = (f: number, x: number, y: number, zoom: number, rx = 0, ry = 0, rz = 0, ease?: EaseName): CamKey => ({ f, x, y, zoom, rx, ry, rz, ease });

const buildKeys = (): CamKey[] => {
  const keys: CamKey[] = [
    k(0, -300, -240, 3.0, 22, -16),
    k(18, -400, -230, 1.25, 0, 0, 0, 'land'),
    k(40, -460, -210, 1.3, 0, 0, 0, 'drift'),
    k(62, 480, 10, 1.0, 0, 6, 0, 'whip'),
  ];
  // follow the cursor: the eye rides the pointer, zoom grows as it nears the button
  for (let f = 66; f <= 126; f += 4) {
    const c = cursorAt(f);
    const z = tween(f, 62, 126, 1.0, 2.2, 'whip');
    const m = tween(f, 62, 126, 0.45, 0.85, 'whip');
    keys.push(k(f, 520 + (c.x - 520) * m, 40 + (c.y - 40) * m, z, 0, 6 * (1 - prog(f, 62, 126, 'whip')), 0, 'linear'));
  }
  keys.push(
    k(128, BTN_CX, BTN_CY, 2.2, 0, 0, 0, 'drift'),
    k(154, BTN_CX - 6, BTN_CY + 4, 2.7, 0, 0, 0, 'snap'),   // decisive: the click / stamp
    k(176, BTN_CX - 6, BTN_CY + 4, 2.76, 0, 0, 0, 'drift'),
    k(LINE_A, LINE_X0 + 160, 1300, 1.35, 12, -8, 0, 'snap'), // snap down to the identities
  );
  for (let f = LINE_A + 4; f <= LINE_B; f += 4) {
    const t = (f - LINE_A) / (LINE_B - LINE_A);
    keys.push(k(f, headX(f) + 160, 1300, 1.35, 12 * (1 - t), -8 * (1 - t), 0, 'linear'));
  }
  keys.push(
    k(332, 0, 1250, 0.92, 0, 0, 0, 'land'),
    k(372, 0, 1250, 0.95, 0, 0, 0, 'drift'),
  );
  // exit: exponential push past the EXECUTED block's top-right corner; the frame ends on white ground
  const qx = 1010, qy = 1196, cx0 = 0, cy0 = 1250, z0 = 0.95;
  for (let f = 373; f <= 390; f++) {
    const e = prog(f, 372, 389, 'linear');
    const z = z0 * Math.pow(40 / z0, e);
    keys.push(k(f, qx + (cx0 - qx) * (z0 / z), qy + (cy0 - qy) * (z0 / z), z, 0, 0, 0, 'linear'));
  }
  return keys;
};
const KEYS = buildKeys();

/* ------------------------------------------------------------------ */

const Row: React.FC<{ h: number; last?: boolean; children: React.ReactNode }> = ({ h, last, children }) => (
  <div style={{ height: h, borderBottom: last ? undefined : `1px solid ${C.dLine}`, boxSizing: 'border-box', padding: '20px 0', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 8 }}>{children}</div>
);

const DecisionPanel: React.FC<{ frame: number }> = ({ frame }) => {
  const press = frame < CLICK ? 0 : frame < CLICK + 3 ? (frame - CLICK) / 3 : frame < CLICK + 9 ? 1 - (frame - CLICK - 3) / 6 : 0;
  const stamped = frame >= STAMP;
  const sp = prog(frame, STAMP, STAMP + 16, 'pop');
  const dim = 1 - 0.65 * prog(frame, STAMP + 8, STAMP + 28, 'out');
  const lbl: React.CSSProperties = { fontFamily: F.mono, fontWeight: 400, fontSize: 18, lineHeight: '22px', color: C.dMuted };
  const val: React.CSSProperties = { fontFamily: F.body, fontWeight: 400, fontSize: 28, lineHeight: '40px', color: C.dFg };
  return (
    <div style={{ position: 'absolute', left: PX, top: PY, width: PW, height: PH, background: C.ink, boxSizing: 'border-box', padding: `0 ${PAD}px` }}>
      <div style={{ height: 132, borderBottom: `1px solid ${C.dLine}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', fontFamily: F.display, fontWeight: 800, fontSize: 48, color: C.ground, textTransform: 'uppercase', letterSpacing: '-0.01em', lineHeight: 1 }}>Your decision</div>
      <Row h={120}><div style={lbl}>requested by</div><div style={val}>Run agent, Data Platform</div></Row>
      <Row h={160}><div style={lbl}>separation of duties</div><div style={{ ...val, lineHeight: '38px' }}>You did not raise this request, so you may approve it.</div></Row>
      <Row h={120}><div style={lbl}>second approver</div><div style={val}>Not required at tier 2.</div></Row>
      <div style={{ height: 28 }} />
      <div style={{ height: BTN_H, background: C.yellow, border: stamped ? `3px solid ${C.ink}` : `1.5px solid ${C.yellow}`, outline: stamped ? `1.5px solid ${C.yellow}` : undefined, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 - press * 0.04})`, position: 'relative' }}>
        {!stamped && <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 32, color: C.ink }}>Approve and run</div>}
        {stamped && (
          <div style={{ fontFamily: F.mono, fontWeight: 600, fontSize: 20, color: C.ink, whiteSpace: 'nowrap', letterSpacing: 0, transform: `scale(${0.88 + 0.12 * sp})`, fontVariantNumeric: 'tabular-nums' }}>
            Approved · Rachid Benjelloun · 02:31:12
          </div>
        )}
      </div>
      <div style={{ opacity: dim }}>
        <div style={{ height: 16 }} />
        <div style={{ height: 72, border: `1.5px solid ${C.ground}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.body, fontWeight: 500, fontSize: 28, color: C.ground }}>Deny with a reason</div>
        <div style={{ height: 36, marginTop: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.body, fontWeight: 500, fontSize: 28, color: C.ground, textDecoration: 'underline', textUnderlineOffset: 4 }}>Take over manually</div>
        <div style={{ marginTop: 28, fontFamily: F.body, fontWeight: 400, fontSize: 22, lineHeight: '32px', color: C.dMuted }}>Your decision and the full trace are written to the audit log.</div>
      </div>
    </div>
  );
};

const Table: React.FC = () => {
  const rows: [string, React.ReactNode][] = [
    ['Tool', 'spark.rerun_job · write · risk tier 2'],
    ['Target', 'settlement_load_daily on cluster prod-b2'],
    ['Change', (
      <>executor memory <s style={{ color: C.red, textDecorationThickness: 2 }}>8g</s> <b style={{ color: C.green, fontWeight: 600 }}>14g</b> · shuffle partitions <s style={{ color: C.red, textDecorationThickness: 2 }}>400</s> <b style={{ color: C.green, fontWeight: 600 }}>1200</b></>
    )],
    ['Runs as', 'agent://atlas-bank/data-platform/run · credential valid 30 min'],
  ];
  return (
    <div style={{ position: 'absolute', left: -1000, top: 44, width: 1180 }}>
      <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 44, textTransform: 'uppercase', color: C.ink, lineHeight: 1, paddingBottom: 16 }}>What will run</div>
      <div style={{ height: 3, background: C.ink }} />
      {rows.map(([a, b], i) => (
        <div key={i} style={{ height: 64, borderBottom: `1px solid ${C.hairline}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center' }}>
          <div style={{ width: 200, fontFamily: F.body, fontSize: 26, color: C.asphalt }}>{a}</div>
          <div style={{ fontFamily: F.mono, fontSize: 22, color: C.ink, whiteSpace: 'nowrap' }}>{b}</div>
        </div>
      ))}
    </div>
  );
};

type Id = { tag: string; name: string; mono?: boolean; role?: string; time: string; kind: 'plain' | 'yellow' | 'ink' };
const IDS: Id[] = [
  { tag: 'PROPOSED', name: 'agent://atlas-bank/data-platform/run', mono: true, role: 'Run agent', time: '02:17', kind: 'plain' },
  { tag: 'APPROVED', name: 'Rachid Benjelloun', role: 'change manager', time: '02:31:12', kind: 'yellow' },
  { tag: 'EXECUTED', name: 'Salma Idrissi', role: 'on-call engineer', time: '02:31:40', kind: 'ink' },
];

const IdentityBlock: React.FC<{ d: Id; x: number; frame: number; start: number }> = ({ d, x, frame, start }) => {
  const p = prog(frame, start, start + 26, 'land');
  const op = Math.min(1, Math.max(0, (frame - start) / 6));
  const bg = d.kind === 'yellow' ? C.yellow : d.kind === 'ink' ? C.ink : C.ground;
  const fg = d.kind === 'ink' ? C.ground : C.ink;
  const sub = d.kind === 'ink' ? C.dMuted : d.kind === 'yellow' ? C.ink : C.asphalt;
  const rule = d.kind === 'ink' ? C.dLine : d.kind === 'yellow' ? C.ink : C.hairline;
  return (
    <div style={{ position: 'absolute', left: x, top: BLOCK_Y, width: BLOCK_W, height: BLOCK_H, boxSizing: 'border-box', padding: 32, background: bg, color: fg, border: d.kind === 'plain' ? `1.5px solid ${C.ink}` : undefined, opacity: op, transform: `translateY(${(1 - p) * 70}px)`, display: 'flex', flexDirection: 'column' }}>
      <Label color={d.kind === 'ink' ? C.dMuted : C.ink} size={20} style={{ fontWeight: 600 }}>{d.tag}</Label>
      <div style={{ marginTop: 20, fontFamily: d.mono ? F.mono : F.body, fontWeight: d.mono ? 500 : 700, fontSize: d.mono ? 22 : 40, lineHeight: d.mono ? '30px' : '44px', color: fg, whiteSpace: 'nowrap' }}>{d.name}</div>
      <div style={{ marginTop: 8, fontFamily: F.body, fontWeight: 500, fontSize: 28, lineHeight: '32px', color: sub }}>{d.role}</div>
      <div style={{ flex: 1 }} />
      <div style={{ height: 1, background: rule }} />
      <div style={{ marginTop: 12, fontFamily: F.display, fontWeight: 800, fontSize: 96, lineHeight: '88px', letterSpacing: '-0.01em', fontVariantNumeric: 'tabular-nums', color: fg }}>{d.time}</div>
    </div>
  );
};

export const S07Approval: React.FC = () => {
  const frame = useCurrentFrame();
  const c = cursorAt(frame);
  const press = frame < CLICK ? 0 : frame < CLICK + 3 ? (frame - CLICK) / 3 : frame < CLICK + 9 ? 1 - (frame - CLICK - 3) / 6 : 0;
  const curOp = Math.min(1, (frame - 52) / 6) * (1 - prog(frame, 160, 176, 'out'));
  const hx = headX(frame);
  const lineW = Math.max(0, hx - LINE_X0);

  return (
    <AbsoluteFill style={{ background: C.ground }}>
      <Camera keys={KEYS} background={C.ground}>
        {/* ---- part 1: the screen ---- */}
        <Label size={20} style={{ position: 'absolute', left: -1000, top: -490, textTransform: 'none', letterSpacing: 0, fontWeight: 400, color: C.asphalt }}>Changes / CHG-48213 · raised 02:17 by the Run agent · from INV-2291</Label>
        <div style={{ position: 'absolute', left: -1000, top: -444, display: 'flex', gap: 16 }}>
          <Tag size={22} style={{ fontWeight: 400 }}>Tier 2</Tag>
          <Tag size={22} style={{ fontWeight: 400 }}>Window open until 05:30</Tag>
          <Tag kind="yellow" size={22} style={{ fontWeight: 600 }}>{frame >= STAMP + 10 ? 'Approved' : 'Waiting for you'}</Tag>
        </div>
        <div style={{ position: 'absolute', left: -1000, top: -372 }}>
          <Rise text="Approve the" frame={frame} start={4} size={132} stagger={3} />
          <Rise text="settlement rerun?" frame={frame} start={10} size={132} stagger={3} />
        </div>
        <div style={{ position: 'absolute', left: -1000, top: -98, width: 1100, fontFamily: F.body, fontSize: 32, lineHeight: '44px', color: C.ink, opacity: prog(frame, 14, 30, 'out') }}>
          The Run agent asks to rerun one Spark job with more memory. It cannot act alone here, because a regulatory feed depends on the result.
        </div>
        <Table />
        <DecisionPanel frame={frame} />
        <div style={{ opacity: Math.max(0, curOp) }}>
          <Cursor x={c.x} y={c.y} press={press} />
        </div>

        {/* ---- part 2: three identities ---- */}
        <div style={{ position: 'absolute', left: -950, top: 940 }}>
          <Rise text="Three identities on every change." frame={frame} start={176} size={110} stagger={3} />
        </div>
        <div style={{ position: 'absolute', left: LINE_X0, top: LINE_Y - 1.5, width: lineW, height: 3, background: C.ink }} />
        {IDS.map((d, i) => (
          <IdentityBlock key={i} d={d} x={BLOCK_X[i]} frame={frame} start={blockStart[i] + (i === 0 ? 0 : 0)} />
        ))}
      </Camera>
      <AbsoluteFill style={{ background: C.yellow, opacity: 1 - prog(frame, 0, 14, 'out'), pointerEvents: 'none' }} />
    </AbsoluteFill>
  );
};
