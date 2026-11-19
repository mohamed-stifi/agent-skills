import { Easing, interpolate } from 'remotion';

// The motion vocabulary. Every move in the film uses one of these, nothing ad hoc.
//  whip   – pure speed: slow start, violent middle, long soft stop. Camera travel between subjects.
//  snap   – anticipation (pulls back ~8%) then fast travel then overshoot (~6%) and settle. The signature "decisive" move.
//  land   – no anticipation, arrives fast and overshoots once (~10%). Elements entering.
//  pop    – stronger overshoot for small things (badges, dots, stamps).
//  out    – fast-out decel, no overshoot. Text reveals, line draws.
//  drift  – near-linear slow push. Holds that must still feel alive.
//  pushIn – accelerating ease-in. Exits (whip-through into the next scene).
export const E = {
  whip: Easing.bezier(0.75, 0, 0.12, 1),
  snap: Easing.bezier(0.55, -0.32, 0.18, 1.22),
  land: Easing.bezier(0.16, 1, 0.3, 1.14),
  pop: Easing.out(Easing.back(2.2)),
  out: Easing.bezier(0.16, 1, 0.3, 1),
  drift: Easing.bezier(0.35, 0, 0.65, 1),
  pushIn: Easing.bezier(0.7, 0, 0.95, 0.4),
  linear: (t: number) => t,
} as const;
export type EaseName = keyof typeof E;

/** Progress 0..1 between frames a and b with an ease. Clamped. */
export const prog = (frame: number, a: number, b: number, ease: EaseName = 'out') =>
  E[ease](Math.min(1, Math.max(0, (frame - a) / Math.max(1, b - a))));

/** Map frame to value range with an ease. */
export const tween = (frame: number, a: number, b: number, from: number, to: number, ease: EaseName = 'out') =>
  from + (to - from) * prog(frame, a, b, ease);

export type Key<T extends Record<string, number>> = { f: number; ease?: EaseName } & T;

/** Keyframe interpolation for many numeric props. ease on a key applies to the segment arriving at that key. */
export function keyed<T extends Record<string, number>>(frame: number, keys: Key<T>[]): T {
  const out: Record<string, number> = {};
  const props = Object.keys(keys[0]).filter((k) => k !== 'f' && k !== 'ease');
  for (const p of props) {
    if (frame <= keys[0].f) { out[p] = (keys[0] as any)[p]; continue; }
    const last = keys[keys.length - 1];
    if (frame >= last.f) { out[p] = (last as any)[p]; continue; }
    for (let i = 0; i < keys.length - 1; i++) {
      const a = keys[i], b = keys[i + 1];
      if (frame >= a.f && frame <= b.f) {
        const t = E[b.ease ?? 'whip']((frame - a.f) / Math.max(1, b.f - a.f));
        out[p] = (a as any)[p] + ((b as any)[p] - (a as any)[p]) * t;
        break;
      }
    }
  }
  return out as T;
}

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export { interpolate };
