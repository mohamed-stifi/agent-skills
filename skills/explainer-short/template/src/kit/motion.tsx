import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame} from 'remotion';
import {FPS} from './theme';

/** A value that is either fixed, or keyframed: [[frame, value], ...] (eased between keys). */
export type V = number | [number, number][];

const ease = Easing.inOut(Easing.cubic);

/** Resolve a V at a frame. Keys may be unsorted; duplicate frames are tolerated. */
export const val = (frame: number, v: V): number => {
  if (typeof v === 'number') return v;
  if (v.length === 0) return 0;
  if (v.length === 1) return v[0][1];
  const k = [...v].sort((a, b) => a[0] - b[0]);
  const xs: number[] = [];
  k.forEach(([x], i) => xs.push(i > 0 && x <= xs[i - 1] ? xs[i - 1] + 0.001 : x));
  return interpolate(frame, xs, k.map((p) => p[1]), {
    easing: ease,
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

/**
 * Spotlight plan: [[frame, ['idA','idB']], [frame, []], ...]. From each frame on, every <El id=…>
 * NOT in the list is dimmed to 30%. An empty list = nothing dimmed. Elements without `id` are never dimmed.
 */
export type FocusPlan = [number, string[]][];
const FocusCtx = React.createContext<FocusPlan>([]);
export const FocusProvider = FocusCtx.Provider;

const spot = (frame: number, plan: FocusPlan, id: string) => {
  const k = [...plan].sort((a, b) => a[0] - b[0]);
  let i = -1;
  for (let j = 0; j < k.length; j++) if (k[j][0] <= frame) i = j;
  if (i < 0) return 1;
  const lvl = (set: string[]) => (set.length > 0 && !set.includes(id) ? 0.3 : 1);
  const cur = lvl(k[i][1]);
  const prev = i > 0 ? lvl(k[i - 1][1]) : 1;
  return interpolate(frame, [k[i][0], k[i][0] + 8], [prev, cur], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};

/** Move from a to b between frames [from, from+dur] — shorthand for keyframes. */
export const move = (from: number, a: number, b: number, dur = 18): V => [
  [from, a],
  [from + dur, b],
];

/** 0→1 spring starting at frame `at`. */
export const usePop = (at: number, stiff = 180) => {
  const frame = useCurrentFrame();
  return spring({frame: frame - at, fps: FPS, config: {damping: 16, stiffness: stiff}});
};

/** 0→1 linear progress over [at, at+dur]. */
export const useProgress = (at: number, dur: number) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [at, at + Math.max(1, dur)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
};

export type ElProps = {
  /** name used by the Spotlight plan (<Canvas focus=…>) */
  id?: string;
  /** frame it appears (absolute) */
  at?: number;
  /** frame it starts leaving (absolute). Omit = stays until the end. */
  out?: number;
  x: V;
  y: V;
  w?: V;
  h?: V;
  /** 'tl' = x,y is the top-left corner (default); 'c' = x,y is the center */
  anchor?: 'tl' | 'c';
  enter?: 'up' | 'fade' | 'pop' | 'left' | 'right' | 'none';
  /** frame ranges where it is dimmed to 30% (focus is elsewhere) */
  dim?: [number, number][];
  scale?: V;
  opacity?: V;
  rotate?: V;
  z?: number;
  style?: React.CSSProperties;
  children?: React.ReactNode;
};

/**
 * Absolutely positioned element with enter / exit / dim / keyframed motion.
 * Every visual on the canvas should live inside an <El>.
 */
export const El: React.FC<ElProps> = ({
  id,
  at = 0,
  out,
  x,
  y,
  w,
  h,
  anchor = 'tl',
  enter = 'up',
  dim,
  scale = 1,
  opacity = 1,
  rotate = 0,
  z,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const plan = React.useContext(FocusCtx);
  const p = spring({frame: frame - at, fps: FPS, config: {damping: 18, stiffness: 170}});
  if (frame < at) return null;
  const leave = out === undefined ? 0 : interpolate(frame, [out, out + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (leave >= 1) return null;

  const d = 1 - p;
  const t = {
    up: `translateY(${d * 40}px)`,
    left: `translateX(${-d * 80}px)`,
    right: `translateX(${d * 80}px)`,
    pop: `scale(${0.6 + 0.4 * p})`,
    fade: '',
    none: '',
  }[enter];
  const enterOpacity = enter === 'none' ? 1 : Math.min(1, p * 1.5);

  let dimK = 1;
  for (const [a, b] of dim ?? []) {
    const k = interpolate(frame, [a, a + 8, b, b + 8], [1, 0.3, 0.3, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    dimK = Math.min(dimK, k);
  }
  if (id) dimK = Math.min(dimK, spot(frame, plan, id));

  const X = val(frame, x);
  const Y = val(frame, y);
  return (
    <div
      style={{
        position: 'absolute',
        left: X,
        top: Y,
        width: w === undefined ? undefined : val(frame, w),
        height: h === undefined ? undefined : val(frame, h),
        transform: `${anchor === 'c' ? 'translate(-50%, -50%) ' : ''}${t} scale(${val(frame, scale)}) rotate(${val(frame, rotate)}deg)`,
        transformOrigin: anchor === 'c' ? 'center' : 'top left',
        opacity: enterOpacity * (1 - leave) * dimK * val(frame, opacity),
        zIndex: z,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Zoom/pan the whole canvas (like a camera). Keyframe `zoom`, and the point
 * (cx, cy) in canvas pixels that should be at the center of the screen.
 */
export const Camera: React.FC<{zoom?: V; cx?: V; cy?: V; children: React.ReactNode}> = ({
  zoom = 1,
  cx = 540,
  cy = 960,
  children,
}) => {
  const frame = useCurrentFrame();
  const z = val(frame, zoom);
  const X = val(frame, cx);
  const Y = val(frame, cy);
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        transform: `translate(${540 - X * z}px, ${960 - Y * z}px) scale(${z})`,
        transformOrigin: '0 0',
      }}
    >
      {children}
    </div>
  );
};

/** Reveals children left→right like handwriting, starting at `at`. */
export const Write: React.FC<{at: number; dur?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({
  at,
  dur = 14,
  children,
  style,
}) => {
  const p = useProgress(at, dur);
  const frame = useCurrentFrame();
  if (frame < at) return null;
  return <div style={{clipPath: `inset(-20% ${100 - p * 100}% -20% -5%)`, ...style}}>{children}</div>;
};
