# Brand: take the product's own, else the house style

## Where to find it (in this order, stop at the first that gives colours + type)
1. **Design docs in the repo**: `DESIGN*.md`, `docs/design/`, design tokens (`tokens.json`, `theme.ts`, `tailwind.config.*`,
   CSS variables `--color-*`), a Figma/Paper export.
2. **The website** (URL given): fetch the page and its main CSS; read `:root` custom properties, `font-family`
   declarations, the `<link>` to Google Fonts, the logo SVG, `theme-color` meta. Take colours by role (background, text,
   primary/accent, success, danger), not by frequency.
3. **Screens**: product screenshots or the live app, as *reference only*: redraw what matters, never embed.
4. Nothing found → keep the **house style** (the default tokens: white ground, ink type, one yellow accent, Barlow
   Condensed / Barlow / IBM Plex Mono, square corners). Say so in the final reply.

## Applying it
- `source/src/kit/tokens.ts`: change VALUES, keep KEYS (`ground ink muted concrete panel hairline accent onAccent ok stop`
  + the `d*` dark-ground set). Contrast: text on `accent` uses `onAccent` (≥ 4.5:1).
- Fonts: add `@fontsource/<family>` packages (exact versions) to `source/package.json`, import the weights in
  `src/kit/fonts.ts` (and add them to the `document.fonts.load` list), set `F.display/body/mono`. A font that is not on
  Fontsource: put the woff2 in `source/public/fonts/` with an `@font-face` in fonts.ts, and check its licence.
- `BRAND.name` = the wordmark. If the product has a logo, draw it as inline SVG in a `Logo` component (trace simple
  marks by hand from the SVG source; never paste a raster logo).
- Brand rules beat house rules: if the brand uses rounded corners or soft shadows, use them consistently.
