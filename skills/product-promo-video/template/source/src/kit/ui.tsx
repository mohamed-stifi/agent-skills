import React from 'react';
import { C, F, BRAND } from './tokens';
import { prog, tween, EaseName } from './ease';

/* ---------- Text ---------- */

/** Mono uppercase label, the signage "wayfinding" line. */
export const Label: React.FC<{ children: React.ReactNode; color?: string; size?: number; style?: React.CSSProperties }> = ({ children, color = C.muted, size = 18, style }) => (
  <div style={{ fontFamily: F.mono, fontWeight: 500, fontSize: size, letterSpacing: '0.08em', textTransform: 'uppercase', color, lineHeight: 1.2, ...style }}>{children}</div>
);

/**
 * Masked word-by-word rise. Each word slides up from behind its own mask with the `land` overshoot.
 * start = frame the first word begins; stagger = frames between words.
 */
export const Rise: React.FC<{
  text: string; frame: number; start: number; stagger?: number; dur?: number;
  size: number; color?: string; weight?: number; family?: string; tracking?: string; lineHeight?: number;
  ease?: EaseName; style?: React.CSSProperties; upper?: boolean;
}> = ({ text, frame, start, stagger = 4, dur = 22, size, color = C.ink, weight = 800, family = F.display, tracking = '-0.02em', lineHeight = 0.92, ease = 'land', style, upper = true }) => {
  const words = text.split(' ');
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', columnGap: size * 0.24, fontFamily: family, fontWeight: weight, fontSize: size, letterSpacing: tracking, lineHeight, color, textTransform: upper ? 'uppercase' : 'none', ...style }}>
      {words.map((w, i) => {
        const p = prog(frame, start + i * stagger, start + i * stagger + dur, ease);
        return (
          <span key={i} style={{ display: 'inline-block', overflow: 'hidden', paddingBottom: size * 0.06, marginBottom: -size * 0.06 }}>
            <span style={{ display: 'inline-block', transform: `translateY(${(1 - p) * 105}%)` }}>{w}</span>
          </span>
        );
      })}
    </div>
  );
};

/** Typewriter for mono strings. cps = characters per second at 60fps. Shows a block caret while typing. */
export const Type: React.FC<{ text: string; frame: number; start: number; cps?: number; style?: React.CSSProperties; caret?: string }> = ({ text, frame, start, cps = 45, style, caret = C.ink }) => {
  const n = Math.max(0, Math.min(text.length, Math.floor(((frame - start) / 60) * cps)));
  const typing = frame >= start && n < text.length;
  return (
    <span style={{ fontFamily: F.mono, whiteSpace: 'pre', ...style }}>
      {text.slice(0, n)}
      {typing && <span style={{ display: 'inline-block', width: '0.6em', height: '1.05em', background: caret, verticalAlign: '-0.15em' }} />}
    </span>
  );
};

/* ---------- Signage UI primitives (square corners, rules, no shadows) ---------- */

/** Wordmark: accent square + product name in the display face. Replace with the product's real logo (drawn as SVG) when it has one. */
export const BrandMark: React.FC<{ size?: number; color?: string; square?: string; gap?: number; name?: string }> = ({ size = 40, color = C.ink, square = C.accent, gap, name = BRAND.name }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: gap ?? size * 0.3 }}>
    <div style={{ width: size * 0.62, height: size * 0.62, background: square }} />
    <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: size, lineHeight: 1, letterSpacing: '-0.01em', color }}>{name}</div>
  </div>
);

export type TagKind = 'outline' | 'accent' | 'yellow' | 'ink' | 'red' | 'green' | 'darkOutline';
export const Tag: React.FC<{ children: React.ReactNode; kind?: TagKind; size?: number; style?: React.CSSProperties }> = ({ children, kind = 'outline', size = 18, style }) => {
  const k = {
    outline: { bg: 'transparent', fg: C.ink, bd: C.ink },
    yellow: { bg: C.accent, fg: C.onAccent, bd: C.accent },
    accent: { bg: C.accent, fg: C.onAccent, bd: C.accent },
    ink: { bg: C.ink, fg: C.ground, bd: C.ink },
    red: { bg: 'transparent', fg: C.stop, bd: C.stop },
    green: { bg: 'transparent', fg: C.ok, bd: C.ok },
    darkOutline: { bg: 'transparent', fg: C.dFg, bd: C.dFg },
  }[kind];
  return (
    <div style={{ fontFamily: F.mono, fontWeight: 500, fontSize: size, lineHeight: 1, padding: `${size * 0.42}px ${size * 0.62}px`, background: k.bg, color: k.fg, border: `1.5px solid ${k.bd}`, whiteSpace: 'nowrap', ...style }}>{children}</div>
  );
};

/** Autonomy level badge L0–L4. */
export const Level: React.FC<{ l: 0 | 1 | 2 | 3 | 4; size?: number }> = ({ l, size = 26 }) => {
  const bg = l <= 1 ? C.concrete : l === 2 ? C.accent : C.ink;
  const fg = l >= 3 ? C.ground : C.ink;
  return <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: size, lineHeight: 1, padding: `${size * 0.18}px ${size * 0.32}px ${size * 0.1}px`, background: bg, color: fg }}>L{l}</div>;
};

export const Dot: React.FC<{ color: string; size?: number; style?: React.CSSProperties }> = ({ color, size = 14, style }) => (
  <div style={{ width: size, height: size, background: color, flexShrink: 0, ...style }} />
);

export type BtnKind = 'decision' | 'primary' | 'secondary' | 'onDark';
export const Button: React.FC<{ children: React.ReactNode; kind?: BtnKind; w?: number; h?: number; size?: number; press?: number; style?: React.CSSProperties }> = ({ children, kind = 'decision', w, h = 64, size = 24, press = 0, style }) => {
  const k = {
    decision: { bg: C.accent, fg: C.onAccent, bd: C.accent },
    primary: { bg: C.ink, fg: C.ground, bd: C.ink },
    secondary: { bg: 'transparent', fg: C.ink, bd: C.ink },
    onDark: { bg: 'transparent', fg: C.ground, bd: C.ground },
  }[kind];
  return (
    <div style={{ width: w, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center', background: k.bg, color: k.fg, border: `1.5px solid ${k.bd}`, fontFamily: F.body, fontWeight: 600, fontSize: size, transform: `scale(${1 - press * 0.04})`, ...style }}>{children}</div>
  );
};

/** Heavy ink rule that opens a block; draws left→right between frames a and b. */
export const Rule: React.FC<{ frame?: number; a?: number; b?: number; w: number; h?: number; color?: string; style?: React.CSSProperties }> = ({ frame = 999, a = 0, b = 1, w, h = 3, color = C.ink, style }) => (
  <div style={{ width: w, height: h, background: color, transformOrigin: '0 50%', transform: `scaleX(${prog(frame, a, b, 'out')})`, ...style }} />
);

/** Drawn pointer cursor (vector, crisp at any zoom). Tip is at (0,0). */
export const Cursor: React.FC<{ x: number; y: number; scale?: number; press?: number }> = ({ x, y, scale = 1, press = 0 }) => (
  <svg width={34 * scale} height={46 * scale} viewBox="0 0 34 46" style={{ position: 'absolute', left: x, top: y, overflow: 'visible', transform: `scale(${1 - press * 0.12})`, transformOrigin: '0 0' }}>
    <path d="M1 1 L1 36 L10 28 L16.5 43 L23 40 L16.6 25.6 L28.5 25.6 Z" fill={C.ink} stroke={C.ground} strokeWidth={2.2} strokeLinejoin="round" />
  </svg>
);

/** Scale-in with overshoot for small elements. Returns a transform string. */
export const popT = (frame: number, start: number, dur = 18) => {
  const p = prog(frame, start, start + dur, 'pop');
  return { transform: `scale(${p})`, opacity: Math.min(1, (frame - start) / 4 + 0.0001 > 0 ? Math.min(1, (frame - start) / 4) : 0) };
};

export { tween, prog };

/**
 * Chapter tag for the four solution chapters of the main film (Run, Migrate, Cost, Brief).
 * Sits top-left in SCREEN space (render it outside <Camera>). Enters with a mask slide, exits by sliding back.
 *   [■] 01 / 04   RUN
 *                 nights without the 02:14 page
 */
export const ChapterTag: React.FC<{ n: number; of?: number; name: string; line: string; frame: number; start?: number; end?: number; dark?: boolean }> = ({ n, of = 4, name, line, frame, start = 8, end = 99999, dark = false }) => {
  const pin = prog(frame, start, start + 20, 'out');
  const pout = prog(frame, end - 14, end, 'pushIn');
  const p = pin * (1 - pout);
  const fg = dark ? C.dFg : C.ink;
  const mu = dark ? C.dMuted : C.muted;
  return (
    <div style={{ position: 'absolute', left: 64, top: 56, display: 'flex', alignItems: 'flex-start', gap: 16, overflow: 'hidden', paddingRight: 8 }}>
      <div style={{ width: 22, height: 22, background: C.accent, marginTop: 6, transform: `scale(${prog(frame, start, start + 16, 'pop') * (1 - pout)})` }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, transform: `translateX(${(p - 1) * 110}%)` }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
          <div style={{ fontFamily: F.mono, fontWeight: 500, fontSize: 20, letterSpacing: '0.08em', color: mu, fontVariantNumeric: 'tabular-nums' }}>{String(n).padStart(2, '0')} / {String(of).padStart(2, '0')}</div>
          <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 40, lineHeight: 1, letterSpacing: '-0.01em', color: fg, textTransform: 'uppercase' }}>{name}</div>
        </div>
        <div style={{ fontFamily: F.body, fontWeight: 500, fontSize: 24, color: mu }}>{line}</div>
      </div>
    </div>
  );
};

/** Alias kept for the example scenes in references/examples. */
export const NemoMark = BrandMark;
