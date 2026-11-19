import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Camera, CamKey } from '../kit/Camera';
import { prog, tween } from '../kit/ease';
import { C, F } from '../kit/tokens';
import { Label, Rise } from '../kit/ui';

// ---- world geometry ----
const LX = 210, LW = 1500, SEG = LW / 4;
const LAD_Y = 540, LAD_H = 150;
const CARD_Y = 350, CARD_H = 136, CARD_W = 730;
const VERDICTS = ['allow', 'ask_reviewer', 'ask_human', 'deny'];
const segCx = (i: number) => LX + SEG * i + SEG / 2;

export const S06PolicyGate: React.FC = () => {
  const f = useCurrentFrame();

  const keys: CamKey[] = [
    { f: 0, x: segCx(0), y: LAD_Y + 80, zoom: 5, rx: 18, ry: 14, rz: 0 },
    { f: 22, x: 960, y: 520, zoom: 1.3, rx: 4, ry: 8, rz: 0, ease: 'land' },
    { f: 146, x: 940, y: 526, zoom: 1.34, rx: 4, ry: 8, rz: 0, ease: 'drift' },
    // the decisive move: camera chases the marker, a beat behind it, and lands frontal
    { f: 198, x: segCx(2) + 40, y: 560, zoom: 1.7, rx: 0, ry: 0, rz: 0, ease: 'snap' },
    { f: 212, x: segCx(2) + 40, y: 560, zoom: 1.72, rx: 0, ry: 0, rz: 0, ease: 'drift' },
    { f: 266, x: 960, y: 470, zoom: 1.0, rx: 0, ry: 0, rz: 0, ease: 'land' },
    { f: 312, x: 960, y: 474, zoom: 1.04, rx: 0, ry: 0, rz: 0, ease: 'drift' },
    // exit: into the yellow segment
    { f: 329, x: segCx(2), y: LAD_Y + LAD_H / 2, zoom: 28, rx: 0, ry: 0, rz: 0, ease: 'pushIn' },
  ];

  // marker: lands on allow (f48), anticipates left, snaps to ask_human (f150-190)
  const mArrive = prog(f, 46, 70, 'land');
  const mMove = prog(f, 150, 190, 'snap');
  const mx = segCx(0) + (segCx(2) - segCx(0)) * mMove;
  const mOpacity = Math.min(1, (f - 46) / 5);
  const settled = f >= 168;                     // marker reaches ask_human
  const fillP = prog(f, 178, 194, 'out');
  const allowGreen = f >= 66 && f < 156;

  const card = (start: number) => {
    const p = prog(f, start, start + 22, 'land');
    return { opacity: Math.min(1, p * 4), transform: `translateY(${(1 - p) * -260}px)` };
  };

  return (
    <Camera keys={keys} background={C.ground}>
      {/* headline */}
      <div style={{ position: 'absolute', left: LX, top: 96 }}>
        <Rise text="Strictest rule wins." frame={f} start={206} stagger={6} dur={24} size={150} />
      </div>

      {/* context label */}
      <div style={{ position: 'absolute', left: LX, top: 300 }}>
        <Label size={22} color={C.ink}>CHG-48213 · spark.rerun_job · write · risk tier 2</Label>
      </div>

      {/* rule cards */}
      <div style={{ position: 'absolute', left: LX, top: CARD_Y, width: CARD_W, height: CARD_H, boxSizing: 'border-box', border: `1.5px solid ${C.ink}`, borderTop: `3px solid ${C.ink}`, background: C.ground, padding: '16px 24px', ...card(40) }}>
        <Label size={18}>R1 · tier-2 cluster</Label>
        <div style={{ marginTop: 8, fontFamily: F.body, fontWeight: 500, fontSize: 28, lineHeight: 1.25, color: C.ink }}>tier-2 cluster → allow up to L2</div>
      </div>
      <div style={{ position: 'absolute', left: LX + LW - CARD_W, top: CARD_Y, width: CARD_W, height: CARD_H, boxSizing: 'border-box', border: `1.5px solid ${C.ink}`, borderTop: `3px solid ${C.ink}`, background: C.ground, padding: '16px 24px', ...card(120) }}>
        <Label size={18}>R2 · regulatory feed</Label>
        <div style={{ marginTop: 8, fontFamily: F.body, fontWeight: 500, fontSize: 28, lineHeight: 1.25, color: C.ink }}>downstream of a regulatory feed → cap at L1, a person approves</div>
      </div>

      {/* verdict ladder */}
      <div style={{ position: 'absolute', left: LX, top: LAD_Y, width: LW, height: LAD_H, borderTop: `3px solid ${C.ink}`, borderBottom: `1.5px solid ${C.ink}`, boxSizing: 'border-box' }}>
        {/* yellow fill of the chosen segment */}
        <div style={{ position: 'absolute', left: SEG * 2 + (SEG / 2) * (1 - fillP), top: 0, width: SEG * fillP, height: '100%', background: C.yellow }} />
        {VERDICTS.map((v, i) => {
          const isHuman = i === 2;
          const color = i === 0 ? (allowGreen ? C.green : C.ink) : isHuman && settled ? C.ink : i === 0 ? C.ink : C.ink;
          return (
            <div key={v} style={{ position: 'absolute', left: SEG * i, top: 0, width: SEG, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.mono, fontWeight: i === 2 && settled || (i === 0 && allowGreen) ? 600 : 500, fontSize: 28, letterSpacing: '0.04em', color: i === 0 && allowGreen ? C.green : (i === 0 && f >= 156 ? C.asphalt : color) }}>
              {v}
            </div>
          );
        })}
        {[1, 2, 3].map((i) => (
          <React.Fragment key={i}>
            <div style={{ position: 'absolute', left: SEG * i - 0.75, top: 0, width: 1.5, height: LAD_H / 2 - 22, background: C.ink }} />
            <div style={{ position: 'absolute', left: SEG * i - 0.75, top: LAD_H / 2 + 22, width: 1.5, height: LAD_H / 2 - 22, background: C.ink }} />
            <div style={{ position: 'absolute', left: SEG * i - 18, top: LAD_H / 2 - 18, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: F.mono, fontSize: 24, color: C.ink }}>{'<'}</div>
          </React.Fragment>
        ))}
      </div>

      {/* marker: upward triangle under the ladder */}
      <svg width={60} height={56} viewBox="0 0 60 56" style={{ position: 'absolute', left: mx - 30, top: LAD_Y + LAD_H + 10 + (1 - mArrive) * 50, overflow: 'visible', opacity: mOpacity }}>
        <polygon points="30,4 56,50 4,50" fill={C.yellow} stroke={C.ink} strokeWidth={2.5} strokeLinejoin="miter" />
      </svg>

      {/* caption + error line */}
      <div style={{ position: 'absolute', left: LX, top: LAD_Y + LAD_H + 78 }}>
        <Label size={18}>less strict → more strict</Label>
      </div>
      <div style={{ position: 'absolute', right: 1920 - (LX + LW), top: LAD_Y + LAD_H + 78, opacity: prog(f, 244, 262, 'out'), transform: `translateY(${tween(f, 244, 262, 10, 0)}px)` }}>
        <Label size={24} color={C.ink}>Any error is a deny.</Label>
      </div>
    </Camera>
  );
};
