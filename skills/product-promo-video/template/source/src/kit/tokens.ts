// BRAND TOKENS — the only file to change for a new product's look (plus fonts.ts for its typefaces).
// Default = the "signage" house style: white ground, heavy condensed ink type, one accent colour.
// Replace with the product's own brand when it has one (see references/brand.md). Keep the KEYS; change the values.
export const BRAND = {
  name: 'PRODUCT', // the wordmark text drawn by <BrandMark>
} as const;

const base = {
  ground: '#FFFFFF', // light background
  ink: '#0B0B0C', // text, heavy rules, dark panels, dark background
  muted: '#5B5F66', // secondary text on light (never on accent)
  concrete: '#E3E5E8', // inactive fills, tracks
  panel: '#F3F4F5', // quiet panels
  hairline: '#D0D3D8', // row dividers
  accent: '#FFCC00', // ONE accent: the brand mark, a decision, the selected item, the CTA
  onAccent: '#0B0B0C', // text on the accent
  ok: '#0F7B3F', // passed, healthy
  stop: '#C8281E', // failed, blocked, risk
  // on the dark (ink) ground
  dFg: '#F2F3F4',
  dMuted: '#B9BCC2',
  dLine: '#34373C',
  dPanel: '#17181A',
  dOk: '#4CC38A',
  dStop: '#FF5A4E',
} as const;

// Legacy names, used by the example scenes in references/examples (Nemo films).
export const C = { ...base, asphalt: base.muted, yellow: base.accent, green: base.ok, red: base.stop, dGreen: base.dOk, dRed: base.dStop } as const;

export const F = {
  display: '"Barlow Condensed", "Arial Narrow", sans-serif',
  body: '"Barlow", "Helvetica Neue", Arial, sans-serif',
  mono: '"IBM Plex Mono", Menlo, monospace',
} as const;

// FORMAT — set by setup.sh (--format). 16:9 = 1920x1080 · 9:16 = 1080x1920 · 1:1 = 1080x1080
export const W = 1920;
export const H = 1080;
export const FPS = 60;
