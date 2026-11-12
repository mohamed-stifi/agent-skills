# Kit API (src/kit) — everything you need, no need to read the kit source

Import from `'../../kit'` (in `Video.tsx`) or `'../../../kit'` (in `stages/*.tsx`).
Timing comes from the video's own `t.ts`: `import {cue, sec} from '../t'`.

Canvas is **1080 × 1920, 30 fps**. All coordinates are **absolute canvas pixels**, all times are
**absolute frames**. Safe zones: title y≈150, main content y 280–1480, takeaway y≈1520,
x 60–1020. Nothing important below y=1600 (phone UI covers it).

## Timing

| Call | Returns |
|---|---|
| `cue('sectionId', 'word')` | frame when the word is spoken (case/punctuation ignored) |
| `cue('sectionId', 'two words')` | phrase = consecutive words |
| `cue('sectionId', 'word', 2)` | 2nd occurrence in that section |
| `cue('sectionId', 'word', 1, 'end')` | frame when the word ends |
| `sec('sectionId')` | `{from, to}` frames of the section |
| `narrationEnd`, `total` | end of voice; full length incl. 2.5 s end card |

Words = the script text split on spaces; matching lowercases and strips leading/trailing punctuation only
(`sunflower42.` → `sunflower42`, `bank.example` stays `bank.example`, `Wi-Fi` → `wi-fi`, `can't` → `can't`).
Use the **display** word as written in `script.json` (e.g. `cue('burst','429')`, not "four twenty nine").
A wrong word throws: `cue not found: "x" #1 in section "y". Words: ...` → pick a word from that list.

## Motion

```tsx
<El at={frame} out={frame?} x={…} y={…} w? h? anchor="tl"|"c" enter="up"|"fade"|"pop"|"left"|"right"|"none"
    dim={[[from,to],…]} scale? opacity? rotate? z?>…</El>
```
- Every visual lives in an `<El>`. `out` omitted = stays to the end. `id` = name for the Spotlight plan.
- Any of `x y w h scale opacity rotate` can be keyframed: `[[frame, value], [frame, value]]` (eased).
  `move(from, a, b, dur=18)` is shorthand for a 2-key move.
- `dim` = ranges where it fades to 30% (focus is elsewhere). Prefer dim over removing.
- **Spotlight** (the main focus device): `<Canvas focus={[[frame, ['idA','idB']], [frame, []], …]}>` — from each
  frame on, every `<El id>` / `<Arrow id>` / `<Packet id>` NOT listed dims to 30 % (8-frame fade). `[]` = all lit.
  Elements without `id` (titles, captions) are never dimmed.
- `<Camera zoom={…} cx={…} cy={…}>` wraps canvas content to zoom/pan (keyframe-able). Use for "zoom into this part".
- `<Write at dur>` reveals children left→right like handwriting.
- Hooks: `usePop(at)` (0→1 spring), `useProgress(at, dur)` (0→1), `val(frame, V)`.

## Text

| Component | Use |
|---|---|
| `<Hook out icon? color?>Question?</Hook>` | first seconds: big question + big icon |
| `<Title at out? color? accent? size? y?>Where **QUERY** helps</Title>` | stage title (1–4 words), top slot; `**word**` = accent color |
| `<Takeaway at out? y? color?>Area, **not** road.</Takeaway>` | caption ≤ 7 words under the diagram, only for key claims |
| `<Hand size color bold>` / `<Mono size color>` | raw hand-lettered / monospace text |
| `accentize(text, color)` | turns `**word**` into colored spans (for your own components) |

## Building blocks (size them with the surrounding `<El w h>`)

| Component | Looks like | Typical use |
|---|---|---|
| `<Panel label icon color tags active state status pad>` | dark card + header (icon, hand label, tags/status right) | an app, a service, a server |
| `<Node color dashed fill icon size state>` | outlined box, centered hand text | tree nodes, steps, components |
| `state` = `'normal' \| 'ok' \| 'error' \| 'dead' \| 'off'` | ok green ✓ · error red tint · dead red + crossed · off greyed | change state on the SAME card (compute from `useCurrentFrame() >= cue(...)`) |
| `<Sticker color rotate>` | tilted filled callout | "DEFAULT CHOICE", "HOTSPOT!", "EMPTY!" next to the target |
| `<LogoTile text label color size>` | initials tile | real products (GH = GitHub) — never fetch real logos |
| `<IconGrid icon n cols size gap color at stagger hot={[{items, at, color}]}>` | grid of tiny icons | SCALE: 20 servers, 2,000 users; `hot` = overloaded/failed ones |
| `<BigStat at value suffix label color size>` | counting big number + label | "25 million / checkouts per day" |
| `<Stepper steps={['Detect','Fix']} active={[[frame, idx], …]} color>` | numbered steps joined by arrows | multi-step solutions, pipelines |
| `<Tag color filled>` | small outlined label | MODEL, MCP CLIENT, 30 DAYS |
| `<Chip color>` | filled pill, mono text, glow | the thing that moves: `create_ticket`, `GET /`, `abc123` |
| `<Actor icon label sub color size>` | big line icon + label | user, laptop, server, script |
| `<Badge n color>` | numbered circle | step 1, 2, 3 |
| `<Icon name size color stroke>` | line icon | see list below |
| `<Table cols rows widths at stagger hl={[{row,at,out,color}]} scan={{at,dur}}>` | data table | rows, index, scans |
| `<Code title lines at step size marks={[{line,text,at,out,color}]} dimOthers>` | code window, types in | JSON, YAML, HTTP, config |
| `<Browser url h>` · `<Phone w h>` · `<Bubble who icon color>` | mockups | websites, apps, chats |
| `<Counter at from to dur suffix color size>` | animated number | "4 steps", "10,000,000 rows" |
| `<Bar at to dur color w label>` | progress bar | load, % |
| `<Toggle onAt label color>` | switch | settings, flags |

## Absolute-position helpers (take canvas coords directly, no `<El>` needed)

| Component | Use |
|---|---|
| `<Arrow at out path={[[x,y],[x,y],…]} color dashed head label dur dim>` | line that draws itself; 3+ points = elbow |
| `<Packet at dur out path={…}>child</Packet>` | child travels along the path (requests, tokens, data) |
| `<Focus at out x y w h color pad>` | marching dashed box: "look here" |

## Canvas + end

`<Canvas brand>` (wraps everything; brand mark top-right) · `<EndCard at={narrationEnd} brand line?>`.

## Rendered sizes (for layout math)

| Element | Size |
|---|---|
| `Title` | ≈ 100 px tall at y (default 150) |
| `Takeaway` (size 60) | ≈ 70 px per line, w 960 centered |
| `Panel` header | ≈ 50 px + padding 24 top/bottom; each child adds its own height + 16 gap |
| `Actor` (size 140) | icon 140 + label 50 (+ sub 30); with `anchor="c"` the center is the middle of that block |
| `Code` | title bar 44 + 32 padding + lines × (size × 1.5) |
| `Table` | header 44 + rows × rowH (48) |
| `Stepper` (size 32) | ≈ 60 px tall; width grows with labels (wraps if > El w) |
| `Chip` / `Tag` / `Sticker` | ≈ size × 1.9 tall |

Unsure? Give the `<El>` an explicit `w`/`h` and keep content inside it; `check.sh` single frames show overflow.

## Prop notes

- `Title color` = the text color; `accent` = the color of `**keyword**` parts (default amber).
- `Panel` `status`, `tags`, `icon`, `label` are all optional. `state` defaults to `'normal'`.
- `Arrow` and `Packet` accept `id` for the Spotlight like `El`. Several elements may share one id (a group).
- `Stepper`: before its first `active` frame all steps are dim (index −1).
- `Hand`/`Mono` accept `style` for anything else (alignment, letter-spacing).
- Density rule counts panels/actors/chips/text, not arrows.

## Icons

user users server db laptop phone browser globe lock unlock key robot doc folder cloud terminal
gear check x warn clock bolt chip chart search mail shield hacker box cpu arrowRight refresh
message sparkle cookie network — unknown names fall back to `box`. Add new ones in `src/kit/icons.tsx`
(24×24 stroke paths) only if really needed.

## Colors (`c.*`)

`bg panel panel2 line text muted dim` + accents `cyan amber pink purple green red blue`.
Give each concept ONE accent for the whole video (e.g. MCP = cyan, UTCP = purple, model = pink).
amber = "the current thing / the answer". red = failure/attack. green = success.

## Custom components

When a concept needs a special visual (token bucket, B-tree, map), write a small component in
`stages/` built from plain divs/SVG + `useCurrentFrame()`, and derive its state from cues
(see `example/stages/Bucket.tsx` → `useTokens`). Keep shared positions as exported constants.
