// Visual tokens for the "dark canvas + hand-lettered" explainer style.
// Change colors here only if the user asks for a different look.

export const W = 1080;
export const H = 1920;
export const FPS = 30;

export const c = {
  bg: '#0A0A0B', // canvas
  panel: '#161618', // cards / windows
  panel2: '#1F1F23', // inner rows, headers
  line: '#2A2A2F', // borders
  text: '#F2F2F3',
  muted: '#8E8E96',
  dim: '#4A4A52',
  // Accents: give each CONCEPT one color and keep it for the whole video.
  cyan: '#4CC9E0', // default structure / "the main thing"
  amber: '#F5B83D', // focus, the current item, the answer
  pink: '#F2557A', // model / attacker / external party
  purple: '#9D7CF0', // the alternative being compared
  green: '#3DD68C', // success, ok, fast
  red: '#F05252', // failure, slow, danger
  blue: '#4C8DF6', // links, requests
} as const;

export type Color = string;

export const font = {
  hand: 'PatrickHandSC', // titles, labels, takeaways (the signature look)
  mono: 'JetBrainsMono', // code, ids, values, URLs
  sans: 'Inter', // UI mockups (browser/app chrome)
} as const;

// Safe zones (1080x1920). Shorts UI covers the bottom ~380px and the right edge.
export const safe = {
  titleY: 150, // stage title baseline area
  top: 280, // main canvas starts
  bottom: 1480, // main canvas ends
  takeawayY: 1520, // one-line takeaway
  left: 60,
  right: 1020,
} as const;
