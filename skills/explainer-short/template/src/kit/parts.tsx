import React from 'react';
import {loadFont} from '@remotion/fonts';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {c, font, FPS} from './theme';
import {El, FocusPlan, FocusProvider, useProgress, usePop, Write} from './motion';
import {Icon} from './icons';

loadFont({family: font.hand, url: staticFile('fonts/PatrickHandSC-Regular.ttf')});
loadFont({family: font.mono, url: staticFile('fonts/JetBrainsMono.ttf')});
loadFont({family: font.sans, url: staticFile('fonts/Inter.ttf')});

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/* ───────────────────────── canvas ───────────────────────── */

/**
 * Dark canvas + small brand mark top-right. Put everything inside.
 * `focus` = Spotlight plan: [[frame, ['id1','id2']], ...] dims every other <El id> to 30%.
 */
export const Canvas: React.FC<{brand?: string; focus?: FocusPlan; children: React.ReactNode}> = ({brand, focus = [], children}) => (
  <AbsoluteFill style={{background: c.bg, fontFamily: font.hand, color: c.text, overflow: 'hidden'}}>
    <FocusProvider value={focus}>{children}</FocusProvider>
    {brand ? (
      <div style={{position: 'absolute', top: 44, right: 56, display: 'flex', alignItems: 'center', gap: 10, opacity: 0.9}}>
        <div style={{width: 22, height: 22, borderRadius: 6, border: `3px solid ${c.cyan}`}} />
        <span style={{fontFamily: font.sans, fontWeight: 600, fontSize: 24, color: c.text}}>{brand}</span>
      </div>
    ) : null}
  </AbsoluteFill>
);

/** Hand-lettered text. size in px. `bold` = marker weight (titles, headers). */
export const Hand: React.FC<{size?: number; color?: string; bold?: boolean; style?: React.CSSProperties; children: React.ReactNode}> = ({
  size = 40,
  color = c.text,
  bold,
  style,
  children,
}) => (
  <div
    style={{
      fontFamily: font.hand,
      fontSize: size,
      color,
      lineHeight: 1.15,
      WebkitTextStroke: bold ? `${Math.max(0.8, size * 0.022)}px currentColor` : undefined,
      ...style,
    }}
  >
    {children}
  </div>
);

/** "Fall back to **POST**" -> POST in the accent color. Non-strings pass through. */
export const accentize = (children: React.ReactNode, accent: string): React.ReactNode =>
  typeof children === 'string'
    ? children.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
        part.startsWith('**') ? (
          <span key={i} style={{color: accent}}>
            {part.slice(2, -2)}
          </span>
        ) : (
          part
        ),
      )
    : children;

/** Monospace text (ids, values, code, URLs). */
export const Mono: React.FC<{size?: number; color?: string; style?: React.CSSProperties; children: React.ReactNode}> = ({
  size = 26,
  color = c.text,
  style,
  children,
}) => <div style={{fontFamily: font.mono, fontSize: size, color, ...style}}>{children}</div>;

/**
 * The stage title (top slot, hand-lettered, written on). 1–4 words, one per stage:
 * "**MCP** server", "Trade-off". `**word**` is drawn in `accent`. Swap titles with at/out (they cross-fade).
 */
export const Title: React.FC<{at: number; out?: number; color?: string; accent?: string; size?: number; y?: number; children: React.ReactNode}> = ({
  at,
  out,
  color = c.text,
  accent = c.amber,
  size = 84,
  y = 150,
  children,
}) => (
  <El at={at} out={out} x={0} y={y} w={1080} enter="fade">
    <Write at={at} dur={12}>
      <Hand size={size} color={color} bold style={{textAlign: 'center'}}>
        {accentize(children, accent)}
      </Hand>
    </Write>
  </El>
);

/** Opening question (first 2–3 s): big, centered higher, 2 lines max, with an optional icon under it. */
export const Hook: React.FC<{at?: number; out: number; icon?: string; color?: string; children: React.ReactNode}> = ({
  at = 0,
  out,
  icon,
  color = c.amber,
  children,
}) => (
  <>
    <El at={at} out={out} x={80} y={360} w={920} enter="fade">
      <Write at={at} dur={16}>
        <Hand size={92} bold style={{textAlign: 'center'}}>
          {accentize(children, color)}
        </Hand>
      </Write>
    </El>
    {icon ? (
      <El at={at + 10} out={out} x={540} y={820} anchor="c" enter="pop">
        <Icon name={icon} size={220} color={color} stroke={1.3} />
      </El>
    ) : null}
  </>
);

/** Short caption (≤7 words) just under the diagram, only for key claims ("Area, not road."). `**word**` = accent. */
export const Takeaway: React.FC<{at: number; out?: number; y?: number; color?: string; size?: number; children: React.ReactNode}> = ({
  at,
  out,
  y = 1520,
  color = c.text,
  size = 60,
  children,
}) => (
  <El at={at} out={out} x={60} y={y} w={960} enter="fade">
    <Write at={at} dur={14}>
      <Hand size={size} color={color} style={{textAlign: 'center'}}>
        {accentize(children, c.amber)}
      </Hand>
    </Write>
  </El>
);

/* ───────────────────────── building blocks ───────────────────────── */

export type State = 'normal' | 'ok' | 'error' | 'dead' | 'off';
const stateColor = (st: State, fallback: string) =>
  st === 'ok' ? c.green : st === 'error' || st === 'dead' ? c.red : st === 'off' ? c.dim : fallback;

/**
 * Dark card with a header (icon + hand label) and optional tags on the right.
 * Size it with the surrounding <El w h>. `active` = colored border (it is the focus now).
 * `state` changes the SAME card (don't replace it): ok (green), error (red tint), dead (red, faded, crossed),
 * off (greyed). `status` = small pill in the header, e.g. "running", "crashed".
 */
export const Panel: React.FC<{
  label?: string;
  icon?: string;
  color?: string;
  tags?: React.ReactNode;
  active?: boolean;
  state?: State;
  status?: string;
  pad?: number;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({label, icon, color = c.cyan, tags, active, state = 'normal', status, pad = 24, style, children}) => {
  const sc = stateColor(state, color);
  const lit = active || state === 'error' || state === 'ok' || state === 'dead';
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        background: state === 'error' || state === 'dead' ? '#2A1416' : c.panel,
        border: `2px solid ${lit ? sc : c.line}`,
        borderRadius: 20,
        boxShadow: lit ? `0 0 40px ${sc}30` : undefined,
        padding: pad,
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        opacity: state === 'off' ? 0.45 : state === 'dead' ? 0.7 : 1,
        transition: 'none',
        ...style,
      }}
    >
      {label || tags || status ? (
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          {icon ? <Icon name={icon} size={40} color={state === 'normal' ? color : sc} /> : null}
          <Hand size={42} bold style={{flex: 1}}>
            {label}
          </Hand>
          <div style={{display: 'flex', gap: 10}}>
            {tags}
            {status ? <Tag color={sc} filled={state !== 'normal'}>{status}</Tag> : null}
          </div>
        </div>
      ) : null}
      {children}
      {state === 'dead' ? (
        <svg style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} viewBox="0 0 100 100" preserveAspectRatio="none">
          <path d="M8 12 L40 46 L30 55 L92 90" stroke={c.red} strokeWidth={1.2} fill="none" vectorEffect="non-scaling-stroke" style={{strokeWidth: 4}} />
        </svg>
      ) : null}
    </div>
  );
};

/** Small outlined (or filled) label, e.g. MODEL, MCP CLIENT, 30 DAYS. */
export const Tag: React.FC<{color?: string; filled?: boolean; size?: number; children: React.ReactNode}> = ({
  color = c.cyan,
  filled,
  size = 32,
  children,
}) => (
  <span
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      padding: '4px 14px',
      borderRadius: 10,
      border: `2px solid ${color}`,
      background: filled ? color : `${color}14`,
      color: filled ? c.bg : color,
      fontFamily: font.hand,
      fontSize: size,
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </span>
);

/** Filled pill with mono text: the "thing that moves" (create_ticket, GET /, session_id=abc123). */
export const Chip: React.FC<{color?: string; size?: number; children: React.ReactNode}> = ({color = c.amber, size = 28, children}) => (
  <span
    style={{
      display: 'inline-block',
      padding: '8px 18px',
      borderRadius: 10,
      background: color,
      color: '#111',
      fontFamily: font.mono,
      fontWeight: 600,
      fontSize: size,
      whiteSpace: 'nowrap',
      boxShadow: `0 0 30px ${color}55`,
    }}
  >
    {children}
  </span>
);

/** Outlined box with centered hand text (tree nodes, steps, components). `state` as in Panel. */
export const Node: React.FC<{
  color?: string;
  dashed?: boolean;
  fill?: boolean;
  size?: number;
  icon?: string;
  state?: State;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({color = c.cyan, dashed, fill, size = 34, icon, state = 'normal', style, children}) => {
  const col = stateColor(state, color);
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        border: `2.5px ${dashed ? 'dashed' : 'solid'} ${col}`,
        borderRadius: 14,
        background: fill || state === 'error' || state === 'ok' ? `${col}22` : c.panel,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 12,
        padding: '10px 16px',
        fontFamily: font.hand,
        fontSize: size,
        color: state === 'off' ? c.muted : c.text,
        textAlign: 'center',
        opacity: state === 'off' ? 0.45 : 1,
        textDecoration: state === 'dead' ? 'line-through' : undefined,
        ...style,
      }}
    >
      {icon ? <Icon name={icon} size={size * 1.1} color={col} /> : null}
      {children}
      {state === 'ok' ? <Icon name="check" size={size} color={c.green} stroke={2.6} /> : null}
      {state === 'error' || state === 'dead' ? <Icon name="x" size={size} color={c.red} stroke={2.6} /> : null}
    </div>
  );
};

/** Tilted filled callout ("DEFAULT CHOICE", "HOTSPOT!"). Put it in an <El enter="pop"> next to its target. */
export const Sticker: React.FC<{color?: string; rotate?: number; size?: number; children: React.ReactNode}> = ({
  color = c.amber,
  rotate = -8,
  size = 38,
  children,
}) => (
  <div
    style={{
      display: 'inline-block',
      transform: `rotate(${rotate}deg)`,
      background: color,
      color: '#111',
      padding: '8px 22px',
      borderRadius: 12,
      fontFamily: font.hand,
      fontSize: size,
      WebkitTextStroke: '1px #111',
      whiteSpace: 'nowrap',
      boxShadow: `0 6px 30px ${color}55`,
    }}
  >
    {children}
  </div>
);

/** Square tile with initials, for a real product/tool (no logos needed): <LogoTile text="GH" label="GitHub" />. */
export const LogoTile: React.FC<{text: string; label?: string; color?: string; size?: number}> = ({text, label, color = c.blue, size = 96}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.24,
        background: `${color}22`,
        border: `2.5px solid ${color}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: font.sans,
        fontWeight: 800,
        fontSize: size * (text.length > 2 ? 0.3 : 0.4),
        color,
      }}
    >
      {text}
    </div>
    {label ? <Hand size={30}>{label}</Hand> : null}
  </div>
);

/**
 * Grid of many small icons to show SCALE (20 servers, 2,000 users). Items appear in a wave from `at`.
 * `hot` recolors some items from a frame on (e.g. the overloaded shard, the failed servers).
 */
export const IconGrid: React.FC<{
  icon: string;
  n: number;
  cols: number;
  size?: number;
  gap?: number;
  color?: string;
  at?: number;
  stagger?: number;
  hot?: {items: number[]; at: number; color?: string}[];
}> = ({icon, n, cols, size = 44, gap = 14, color = c.muted, at = 0, stagger = 1, hot = []}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, ${size}px)`, gap}}>
      {Array.from({length: n}, (_, i) => {
        const h = [...hot].reverse().find((x) => frame >= x.at && x.items.includes(i));
        const show = frame >= at + i * stagger;
        return (
          <div key={i} style={{opacity: show ? 1 : 0, transform: `scale(${show ? 1 : 0.5})`}}>
            <Icon name={icon} size={size} color={h ? h.color ?? c.red : color} stroke={1.8} />
          </div>
        );
      })}
    </div>
  );
};

/** Big number + small label ("25 million" / "checkouts per day"). Counts up from `at`. */
export const BigStat: React.FC<{at: number; value: number; suffix?: string; label: string; color?: string; size?: number}> = ({
  at,
  value,
  suffix = '',
  label,
  color = c.amber,
  size = 110,
}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4}}>
    <Counter at={at} to={value} suffix={suffix} color={color} size={size} />
    <Hand size={32} color={c.muted}>
      {label}
    </Hand>
  </div>
);

/**
 * Row of steps joined by arrows. `active` = [[frame, index], ...]: from that frame, steps up to index are lit
 * (index -1 = none). Use for "3-step solution", pipelines, handshakes.
 */
export const Stepper: React.FC<{steps: string[]; active: [number, number][]; color?: string; size?: number}> = ({
  steps,
  active,
  color = c.amber,
  size = 32,
}) => {
  const frame = useCurrentFrame();
  let idx = -1;
  for (const [f, i] of [...active].sort((a, b) => a[0] - b[0])) if (frame >= f) idx = i;
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', justifyContent: 'center'}}>
      {steps.map((st, i) => (
        <React.Fragment key={i}>
          {i > 0 ? <Icon name="arrowRight" size={size} color={i <= idx ? color : c.dim} /> : null}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 18px',
              borderRadius: 12,
              border: `2.5px solid ${i <= idx ? color : c.line}`,
              background: i === idx ? `${color}22` : c.panel,
              fontFamily: font.hand,
              fontSize: size,
              color: i <= idx ? c.text : c.muted,
            }}
          >
            <Badge n={i + 1} color={i <= idx ? color : c.dim} size={size * 1.1} />
            {st}
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};

/** Icon with a hand label under it (User, Server, Database, Laptop...). */
export const Actor: React.FC<{icon: string; label?: string; color?: string; size?: number; sub?: string}> = ({
  icon,
  label,
  color = c.text,
  size = 140,
  sub,
}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
    <Icon name={icon} size={size} color={color} stroke={1.5} />
    {label ? <Hand size={42}>{label}</Hand> : null}
    {sub ? <Mono size={24} color={c.muted}>{sub}</Mono> : null}
  </div>
);

/** Numbered step circle. */
export const Badge: React.FC<{n: number | string; color?: string; size?: number}> = ({n, color = c.amber, size = 46}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      color: '#111',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: font.hand,
      fontSize: size * 0.62,
      boxShadow: `0 0 20px ${color}66`,
    }}
  >
    {n}
  </div>
);

/** Animated dashed rectangle that says "look here". Absolute canvas coords. */
export const Focus: React.FC<{at: number; out?: number; x: number; y: number; w: number; h: number; color?: string; pad?: number}> = ({
  at,
  out,
  x,
  y,
  w,
  h,
  color = c.amber,
  pad = 10,
}) => {
  const frame = useCurrentFrame();
  return (
    <El at={at} out={out} x={x - pad} y={y - pad} enter="pop" z={5}>
      <svg width={w + pad * 2} height={h + pad * 2} style={{overflow: 'visible', display: 'block'}}>
        <rect
          x={1.5}
          y={1.5}
          width={w + pad * 2 - 3}
          height={h + pad * 2 - 3}
          rx={16}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeDasharray="12 9"
          strokeDashoffset={-frame * 0.8}
        />
      </svg>
    </El>
  );
};

type Pt = [number, number];
const lenOf = (pts: Pt[]) => pts.slice(1).reduce((s, p, i) => s + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);
const pointAt = (pts: Pt[], d: number): {p: Pt; ang: number; upto: Pt[]} => {
  let left = d;
  for (let i = 1; i < pts.length; i++) {
    const [a, b] = [pts[i - 1], pts[i]];
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    if (left <= L || i === pts.length - 1) {
      const k = L === 0 ? 0 : Math.min(1, left / L);
      const p: Pt = [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
      return {p, ang, upto: [...pts.slice(0, i), p]};
    }
    left -= L;
  }
  return {p: pts[0], ang: 0, upto: [pts[0]]};
};

/**
 * Line that draws itself from the first point to the last. `path` = [[x,y], ...]
 * (2 points = straight, more = elbow). Absolute canvas coords.
 */
export const Arrow: React.FC<{
  id?: string;
  at: number;
  out?: number;
  path: Pt[];
  color?: string;
  dashed?: boolean;
  head?: boolean;
  dur?: number;
  width?: number;
  label?: string;
  dim?: [number, number][];
}> = ({id, at, out, path, color = c.muted, dashed, head = true, dur = 14, width = 3, label, dim}) => {
  const p = useProgress(at, dur);
  const frame = useCurrentFrame();
  const total = lenOf(path);
  const {p: tip, ang, upto} = pointAt(path, total * p);
  const mid = pointAt(path, total / 2).p;
  return (
    <El id={id} at={at} out={out} x={0} y={0} enter="none" dim={dim}>
      <svg width={1080} height={1920} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible', pointerEvents: 'none'}}>
        <polyline
          points={upto.map((q) => q.join(',')).join(' ')}
          fill="none"
          stroke={color}
          strokeWidth={width}
          strokeDasharray={dashed ? '10 9' : undefined}
          strokeDashoffset={dashed ? -frame * 0.6 : undefined}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {head && p > 0.05 ? (
          <polygon
            points="0,0 -16,-9 -16,9"
            fill={color}
            transform={`translate(${tip[0]},${tip[1]}) rotate(${(ang * 180) / Math.PI})`}
          />
        ) : null}
      </svg>
      {label && p > 0.6 ? (
        <div
          style={{
            position: 'absolute',
            left: mid[0] + 14,
            top: mid[1] - 22,
            fontFamily: font.hand,
            fontSize: 30,
            color,
            whiteSpace: 'nowrap',
            opacity: interpolate(p, [0.6, 1], [0, 1], clamp),
          }}
        >
          {label}
        </div>
      ) : null}
    </El>
  );
};

/** Something that travels along a path (a request, a packet, a token). Centered on the path. */
export const Packet: React.FC<{id?: string; at: number; dur?: number; out?: number; path: Pt[]; children: React.ReactNode}> = ({
  id,
  at,
  dur = 24,
  out,
  path,
  children,
}) => {
  const p = useProgress(at, dur);
  const {p: pos} = pointAt(path, lenOf(path) * p);
  return (
    <El id={id} at={at} out={out} x={pos[0]} y={pos[1]} anchor="c" enter="pop" z={6}>
      {children}
    </El>
  );
};

/** Table with optional row highlights. Rows can appear one by one with `stagger`. */
export const Table: React.FC<{
  cols: string[];
  rows: (string | number)[][];
  widths: number[];
  at?: number;
  stagger?: number;
  rowH?: number;
  /** highlight a row (0-based) from frame `at` (to `out`) */
  hl?: {row: number; at: number; out?: number; color?: string}[];
  /** dim rows (e.g. scanned and rejected) */
  scan?: {at: number; dur: number};
}> = ({cols, rows, widths, at = 0, stagger = 0, rowH = 48, hl = [], scan}) => {
  const frame = useCurrentFrame();
  const scanRow = scan ? Math.floor(interpolate(frame, [scan.at, scan.at + scan.dur], [-1, rows.length], clamp)) : -2;
  return (
    <div style={{background: c.panel, border: `2px solid ${c.line}`, borderRadius: 14, overflow: 'hidden'}}>
      <div style={{display: 'flex', background: c.panel2, borderBottom: `2px solid ${c.line}`}}>
        {cols.map((h, i) => (
          <div key={i} style={{width: widths[i], padding: '8px 16px', fontFamily: font.hand, fontSize: 26, color: c.muted}}>
            {h}
          </div>
        ))}
      </div>
      {rows.map((r, ri) => {
        const visible = frame >= at + ri * stagger;
        const h = hl.find((x) => frame >= x.at && (x.out === undefined || frame < x.out) && x.row === ri);
        const scanning = scanRow === ri;
        return (
          <div
            key={ri}
            style={{
              display: 'flex',
              height: rowH,
              alignItems: 'center',
              borderBottom: ri < rows.length - 1 ? `1px solid ${c.line}` : undefined,
              background: h ? `${h.color ?? c.amber}22` : scanning ? `${c.text}12` : undefined,
              outline: h ? `2px dashed ${h.color ?? c.amber}` : undefined,
              outlineOffset: -2,
              opacity: visible ? 1 : 0,
            }}
          >
            {r.map((cell, ci) => (
              <div
                key={ci}
                style={{
                  width: widths[ci],
                  padding: '0 16px',
                  fontFamily: font.hand,
                  fontSize: 34,
                  color: h ? h.color ?? c.amber : ci === 0 ? c.muted : c.text,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                }}
              >
                {cell}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
};

/**
 * Code / config window. Lines type in from `at` (one line every `step` frames).
 * `marks` highlight a substring on a line from a frame on (chip background).
 */
export const Code: React.FC<{
  title?: string;
  lines: string[];
  at?: number;
  step?: number;
  size?: number;
  marks?: {line: number; text: string; at: number; out?: number; color?: string}[];
  dimOthers?: boolean;
}> = ({title, lines, at = 0, step = 3, size = 24, marks = [], dimOthers}) => {
  const frame = useCurrentFrame();
  const activeMarks = marks.filter((m) => frame >= m.at && (m.out === undefined || frame < m.out));
  return (
    <div style={{background: c.panel, border: `2px solid ${c.line}`, borderRadius: 16, overflow: 'hidden'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 10, padding: '12px 18px', background: c.panel2}}>
        {['#F05252', '#F5B83D', '#3DD68C'].map((col) => (
          <div key={col} style={{width: 14, height: 14, borderRadius: '50%', background: col}} />
        ))}
        {title ? <span style={{fontFamily: font.mono, fontSize: 20, color: c.muted, marginLeft: 10}}>{title}</span> : null}
      </div>
      <div style={{padding: '16px 22px', fontFamily: font.mono, fontSize: size, lineHeight: 1.5}}>
        {lines.map((ln, i) => {
          const shown = frame >= at + i * step;
          const m = activeMarks.find((x) => x.line === i);
          const faded = dimOthers && activeMarks.length > 0 && !m;
          let body: React.ReactNode = <Syntax text={ln} />;
          if (m && ln.includes(m.text)) {
            const [a, ...rest] = ln.split(m.text);
            body = (
              <>
                <Syntax text={a} />
                <span style={{background: m.color ?? c.amber, color: '#111', borderRadius: 6, padding: '0 6px'}}>{m.text}</span>
                <Syntax text={rest.join(m.text)} />
              </>
            );
          }
          return (
            <div key={i} style={{whiteSpace: 'pre', minHeight: '1.5em', opacity: shown ? (faded ? 0.3 : 1) : 0}}>
              {body}
            </div>
          );
        })}
      </div>
    </div>
  );
};

/** Tiny JSON/YAML/HTTP coloring: keys, strings, numbers, comments. */
const Syntax: React.FC<{text: string}> = ({text}) => {
  if (/^\s*(#|\/\/)/.test(text)) return <span style={{color: c.dim}}>{text}</span>;
  const parts = text.split(/("[^"]*"\s*:|"[^"]*"|\b\d+(?:\.\d+)?\b|^\s*[\w-]+:)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (!p) return null;
        let color: string = c.text;
        if (/^"[^"]*"\s*:$/.test(p) || /^\s*[\w-]+:$/.test(p)) color = c.cyan;
        else if (/^"/.test(p)) color = '#E6C07B';
        else if (/^\d/.test(p)) color = c.purple;
        else if (/^[\s{}[\],]+$/.test(p)) color = c.muted;
        return (
          <span key={i} style={{color}}>
            {p}
          </span>
        );
      })}
    </>
  );
};

/** Big animated number with a label ("4 steps", "10,000,000 rows"). */
export const Counter: React.FC<{at: number; from?: number; to: number; dur?: number; suffix?: string; color?: string; size?: number}> = ({
  at,
  from = 0,
  to,
  dur = 20,
  suffix = '',
  color = c.amber,
  size = 96,
}) => {
  const p = useProgress(at, dur);
  const n = Math.round(from + (to - from) * p);
  return (
    <Hand size={size} color={color} style={{textAlign: 'center'}}>
      {n.toLocaleString('en-US')}
      {suffix}
    </Hand>
  );
};

/** On/off switch (feature flags, settings). Flips at `onAt`. */
export const Toggle: React.FC<{onAt: number; label?: string; color?: string}> = ({onAt, label, color = c.green}) => {
  const p = usePop(onAt, 220);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
      <div style={{width: 76, height: 42, borderRadius: 21, background: p > 0.5 ? color : c.dim, position: 'relative'}}>
        <div style={{position: 'absolute', top: 5, left: 5 + p * 34, width: 32, height: 32, borderRadius: '50%', background: '#fff'}} />
      </div>
      {label ? <Hand size={30}>{label}</Hand> : null}
    </div>
  );
};

/** Progress bar that fills (loading, % complete, speed). */
export const Bar: React.FC<{at: number; to: number; dur?: number; color?: string; w?: number; label?: string}> = ({
  at,
  to,
  dur = 20,
  color = c.green,
  w = 400,
  label,
}) => {
  const p = useProgress(at, dur);
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 6, width: w}}>
      {label ? <Hand size={26} color={c.muted}>{label}</Hand> : null}
      <div style={{height: 16, borderRadius: 8, background: c.panel2, overflow: 'hidden'}}>
        <div style={{height: '100%', width: `${p * to * 100}%`, background: color, borderRadius: 8}} />
      </div>
    </div>
  );
};

/* ───────────────────────── mockups ───────────────────────── */

/** Browser window with a URL bar. */
export const Browser: React.FC<{url: string; children?: React.ReactNode; h?: number}> = ({url, children, h = 420}) => (
  <div style={{background: c.panel, border: `2px solid ${c.line}`, borderRadius: 16, overflow: 'hidden'}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: c.panel2}}>
      {['#F05252', '#F5B83D', '#3DD68C'].map((col) => (
        <div key={col} style={{width: 13, height: 13, borderRadius: '50%', background: col}} />
      ))}
      <div style={{flex: 1, marginLeft: 10, padding: '6px 16px', borderRadius: 999, background: c.bg, fontFamily: font.sans, fontSize: 22, color: c.muted}}>
        <span style={{color: c.green}}>🔒 </span>
        {url}
      </div>
    </div>
    <div style={{height: h, position: 'relative'}}>{children}</div>
  </div>
);

/** Phone frame. Put app UI inside. */
export const Phone: React.FC<{children?: React.ReactNode; w?: number; h?: number}> = ({children, w = 360, h = 740}) => (
  <div style={{width: w, height: h, borderRadius: 52, border: `10px solid #2B2B30`, background: '#101012', overflow: 'hidden', position: 'relative'}}>
    <div style={{position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)', width: 110, height: 28, borderRadius: 14, background: '#000'}} />
    <div style={{position: 'absolute', inset: '52px 14px 14px 14px'}}>{children}</div>
  </div>
);

/** Chat bubble (Slack/ChatGPT style). */
export const Bubble: React.FC<{who?: string; icon?: string; color?: string; children: React.ReactNode}> = ({
  who,
  icon = 'user',
  color = c.cyan,
  children,
}) => (
  <div style={{display: 'flex', gap: 14, alignItems: 'flex-start'}}>
    <div style={{width: 52, height: 52, borderRadius: 14, background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
      <Icon name={icon} size={32} color={color} />
    </div>
    <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
      {who ? <Hand size={26} color={color}>{who}</Hand> : null}
      <div style={{fontFamily: font.sans, fontSize: 28, color: c.text, background: c.panel2, padding: '12px 18px', borderRadius: 14, lineHeight: 1.35}}>
        {children}
      </div>
    </div>
  </div>
);

/* ───────────────────────── end card ───────────────────────── */

/** Last 2.5 s: content dims, brand + Follow button gets "clicked". */
export const EndCard: React.FC<{at: number; brand: string; line?: string}> = ({at, brand, line = 'Follow for more'}) => {
  const frame = useCurrentFrame();
  const p = usePop(at);
  const click = frame > at + 30;
  if (frame < at) return null;
  return (
    <AbsoluteFill
      style={{
        background: `rgba(10,10,11,${0.6 * Math.min(1, (frame - at) / 10)})`,
        backdropFilter: `blur(${8 * Math.min(1, (frame - at) / 10)}px)`,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{transform: `scale(${0.8 + 0.2 * p})`, opacity: p, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
          <div style={{width: 64, height: 64, borderRadius: 16, border: `7px solid ${c.cyan}`}} />
          <span style={{fontFamily: font.sans, fontWeight: 700, fontSize: 72}}>{brand}</span>
        </div>
        <div
          style={{
            fontFamily: font.sans,
            fontWeight: 700,
            fontSize: 46,
            padding: '20px 56px',
            borderRadius: 999,
            background: click ? c.panel2 : c.blue,
            color: click ? c.muted : '#fff',
            transform: `scale(${frame > at + 26 && frame < at + 32 ? 0.92 : 1})`,
          }}
        >
          {click ? '✓ Following' : `+ ${line}`}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const sec2f = (s: number) => Math.round(s * FPS);
