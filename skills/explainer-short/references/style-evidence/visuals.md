# Visual recipe — KodeKloud-style tech Shorts (23 refs)

Method: all 23 contact sheets (1 frame / 3 s) + ~8 single frames + 2 hi-res crops. Percentages refer to a 1080×1920 canvas.

## 1. Canvas & layout
- **Background**: flat near-black, about #0B0B0C–#0E0E10, with no gradient, grain or vignette. A video's average colour is lighter (#15–#29) only because of the panels on it.
- **One persistent "board"** of stacked dark panels, full-bleed. Panel x-margin is about 3–4% (≈36–44 px) each side, so panels span about 92–94% of the width. Gap between stacked panels is about 1.5–2% of height.
- **Vertical zones**
  - 0–5%: small brand mark, top-right. Skip this for us, but keep the zone empty.
  - 6–13%: section title slot, centred. Empty in about 40% of frames.
  - 13–75%: diagram. Almost all content sits here, stacked top→bottom as a data-flow (client → server → storage).
  - 75–100%: usually **empty** (≈20–25% of the screen is dead space at the bottom, because of the Shorts UI overlay). It is used only by a short caption, a stepper or a big stat.
- **Density**: 2–5 panels on screen. Inside panels the content is sparse, and about 45–55% of the canvas is empty black.
- **Captions/stats** sit just under the diagram (≈55–90% y), centred.

## 2. Typography
- **One hand-lettered family for everything non-code.** It is a bold marker-like hand face set in small caps, and it is heavier than Patrick Hand SC (stroke weight ≈ bold 700). Our Patrick Hand SC is close in shape; add a faux-bold (0.6–1 px text-stroke) or a heavier hand font for titles.
- **Section title**: about 52–64 px, small caps, white #F2F2F2. **One keyword is coloured** with that entity's accent ("Fall back to **POST**", "Where **QUERY** helps", "**NGINX** or **HAProxy**?"). Titles are 1–4 words and only occasionally a question.
- **Opening title**: 72–96 px, 2–3 lines, often yellow #F5B83D or white with an accent keyword, ending in "?".
- **Panel header label**: 22–28 px small caps, coloured with the panel's accent, preceded by a 24–28 px icon or a numbered/lettered dot.
- **Body labels / pills**: 16–20 px.
- **Mono** (≈16–22 px) is used for code, YAML/JSON, terminal commands, URLs, IPs, MACs, hashes, file paths, table cell values and HTTP lines. Never for titles.
- **Big numbers** ("30,000", "25 million", "600 PB", "100 million") are set at 64–80 px in mono or a bold sans, with a 16 px small-caps sub-label underneath.

## 3. Color system (approx.)
| Role | Hex | Meaning |
|---|---|---|
| bg | #0B0B0C | canvas |
| panel | #1A1A1C | outer panel fill (radius ≈ 14–18 px, no border or 1 px #2A2A2D) |
| card | #232326 | inner cards/rows |
| text | #F2F2F2 / dim #6B6B70 | main / inactive |
| cyan-teal | #4FC3E0 / #2BB5A0 | primary flow, arrows, "the system", connections |
| amber | #F5B83D | focus/highlight, data items, search key, keyword in title, "step N" |
| pink-coral | #F2577A / #FF6B8B | error, crash, attacker, danger, disconnected, struggling |
| lavender | #A48BFA | second entity (tokens, frames, B-tree, DB servers) |
| green | #3DDC84 | success, OK checks, "running", active |
| red | #E5484D | real failure (traffic jam, 403, TypeError) |

- **3–4 accents per video.** Each accent is bound to one entity for the whole video (NGINX = green, HAProxy = cyan, app servers = amber, DB = lavender).
- Real product logos keep their own colours (Google, Slack, Jira, Postgres…).

## 4. Element vocabulary (videos using it, /23)
- Dark rounded panels with icon + small-caps header + right-side tags: **22**
- Real product/tool logos as icons (Nginx, k8s, Vault, Slack, Google, Jira, GitHub, Postgres, Ansible, Python…): **21**
- Small pills/tags (status "running", "crashed", "active", "used", key names): **22**
- Arrows/connector lines between panels (thin, 1.5–2 px, cyan or neutral grey, arrowheads, often orthogonal elbows): **22**
- Moving token/packet pill along a connector (request card, "git clone", "SUP-142", JSON chip): **16**
- Dashed focus rectangles (white/amber/pink/cyan, around a panel, row or token): **21**
- Terminal / code / YAML / JSON window with traffic-light dots + inline highlighted substrings: **12**
- Tables or key→value lists (DNS records, routing table, redis sessions, cookies, users table, stats): **10**
- People: outline user glyphs, photo avatars ("Alan", "Paul"), a hacker icon, crowds: **13**
- Browser chrome / URL bar: **8**. Phone mockup: **4**. Laptop mockup: **4**.
- Crowd/scale grids (many tiny icons: 20 servers, 200 volumes, 2,000 users, 25 M checkouts): **7**
- Big stat number + sub-label: **6**
- Progress/meter bars (disk usage, shard load, upload %, expiry timeline, speedometer): **7**
- Tilted "sticker" callouts (rotated −6°…−10° filled pill: "DEFAULT CHOICE", "HOTSPOT!", "POP STAR!", "NO AUTHORITY"), sometimes as speech bubbles with a tail: **8**
- Trees: B-tree/B+tree, parse trees, fan-out tree to servers: **5**
- Numbered step dots/badges on path (1→2→3 hops) or a top/bottom stepper: **7**
- Check ✓ / ✗ / lock / key glyph state icons: **15**
- Chat UI (assistant conversation): **2**. Calendar card ("2 weeks later", "Dec 2023"): **2**. Toggle switch: **1**. Cookie-consent/modal mockup: **1**.
- Maps (world map, city map, isometric 3D street with cars): **3** (G5 is the only "3D" one). Network graph of router nodes: **2**. Sequence diagram with two lifelines: **1**. Crash "crack" overlay on a card: **2**.

## 5. Motion grammar
- **Never cut, rarely clear.** The board is built incrementally. Panels persist for 30–90 s and are reused (re-labelled, re-highlighted). Full clears happen 0–3 times per video, as a fade to black of everything and then a rebuild. Even then, anchor panels are often kept.
- **Change cadence**: practically every 3-s sample differs. Something new appears, highlights or moves every **≈1.5–3 s** (≈1 visual beat per spoken clause).
- **Entrances**: fade + slight scale/slide (≈250–400 ms). Arrows draw on. Pills pop in. Rows type/stagger in.
- **Focus is shown by** (in order of frequency):
  1. **dimming everything else** to ≈25–35% opacity (in nearly every video, constantly);
  2. a dashed rectangle around the target;
  3. recolouring the target's border/fill with an accent (e.g. a red-tinted crashed card, an amber row);
  4. a tilted sticker or arrow-callout label;
  5. numbered badges for hops/steps.
- **Camera**: mostly locked. Occasional slow push-in on one panel with the rest **blurred** (≈4–8 px) and dimmed (YVt, G5, H5, If). Sometimes a pan to a new region, or a shrink of the old diagram to a thumbnail (H5, NDA). Blur is also used under an overlay title or question.
- **Sections**: the top title text cross-fades to the next section name in the same slot while the diagram morphs underneath. Coloured keyword continuity ties titles to the diagram.
- **States animate on existing objects**: a server card turns red with a crack and a "CRASHED" pill, a bar fills, a lock opens, ✓ appears, a counter ticks.

## 6. Text on screen
- **No word-by-word subtitles in any of the 23 videos.** No burned-in transcript at all.
- Section titles: 0–9 per video, median ≈4. Several videos (7at, H5, 9ws, YVt) run with almost no titles.
- Short centred captions (≤7 words, 22–28 px hand font, white): "Dark red means a traffic jam.", "Area, not road.", "Default choice", "Full scan". They appear in about 12/23 videos, ~2–8 per video, under the diagram.
- Question prompts as text: "How do servers recognize John?", "Why is it not slow?"
- Labels are 1–3 words. Total on-screen words at any moment: about 15–40, mostly small labels.
- No persistent takeaway bar. The "takeaway" is a final section title ("Big picture", "Trade-off") plus the fully lit diagram.

## 7. Opening & ending
- **Opening (0–3 s)**, 17/23 videos: a centred hook at 8–40% y. It is a big hand-lettered question/title plus a hero visual: logo(s), "A vs B" logos with a diagonal split line, a single icon (DB cylinder, cookie, AI chip), or a mini-diagram. The rest of the videos (G5, lVW, wEj, Rs, o-x) open directly in the scenario (phone map, browser, network graph, equation) with the title arriving at 3–9 s. Within 3–6 s the hero shrinks or moves away and the first panel appears.
- **Ending (last 3 s)**, ~14/23: the final diagram is Gaussian-blurred and dimmed. A small centred dark card (≈55% width, y≈88–93%) shows the logo, a YouTube glyph, "Subscribe" and "Follow" buttons, and a cursor clicks Subscribe, which turns into "Subscribed". The rest end on the completed diagram (1 promotes another video thumbnail).

## 8. Per-video main visual
- **0tcV5uKaGo4**: Stacked client→front-server→3 app-server panels; NGINX vs HAProxy columns, crashed server.
- **6dzjd6wk1EE**: Build-server disk bar + pipeline; image/writable-layer/volume stack; terminal `docker` commands.
- **7VfKiaGOZcA**: Agent app → MCP server → Jira stack vs UTCP manual.json; three-service trade-off grid.
- **7atGIcL-vRY**: Codebase file tree, CI-machine fleets, central Git server vs Scion + region cache.
- **9wseviktBwI**: Claude Code → Playwright MCP → browser signup form inside "your laptop" frame.
- **G5YdN3N3sPk**: Phone map with traffic colours; isometric 3D street, numbered GPS points.
- **H5NR9Ocqhvc**: Nested Vault / Kubernetes / pod panels; agent, token, policy, lock states.
- **Ifd31fTxzgc**: Phone (Instagram) + login server + Redis table; crowd scaling; token pills, hacker.
- **IwnefaLZhGs**: User crowd above 4–5 shard columns with load bars; 3-step solution stepper.
- **NDABiL0N6Dw**: Cluster panel (control plane, pods, DB) dies; backups; RPO/RTO timeline.
- **RsJWze1YP8U**: Laptop→Wi-Fi→ISP→routers ladder; IP-packet card wrapped in MAC frame; routing tables.
- **SfS3yJeKVYQ**: Laptop + Apple server + DB rows; Set-Cookie line annotated; cookie jar; ad-company tracking.
- **YVt6vTpYpwY**: World map → Slack message → web server → Vitess shards → channel servers → gateways.
- **_2WPVe4dw_8**: B-tree above B+ tree, same 9 names; search path with numbered steps.
- **b3bBGEzi4lg**: Users table full scan → sorted index → B-tree levels pointing to table rows.
- **ig2JpD_sAHE**: Pink AI chip inside a yellow fence (input/action/output gates); chat UI attacks.
- **kTBWEkqBIgg**: Phone shop filters → long GET URL window → CDN/LB/server stack; QUERY pills.
- **lVWXZb_4tU8**: Browser + Google server; TCP/TLS/HTTP/IP layer rows; handshake sequence arrows.
- **o-xyWQ7I2fQ**: Equation, two avatars' answers; parse trees side by side; Python REPL error.
- **tfIPJVW3Pgs**: 20-server grid, control node + inventory/playbook YAML; per-server ✓ ticks.
- **wEjgtknhLUQ**: Browser + Google; resolver chain to root / .com / authoritative panels, numbered hops.
- **weFC9-w9J6s**: YouTube server panel above laptop; Wi-Fi link breaks; upload progress bars.
- **zWFj0_C2a2w**: Root-directory grid persistent at bottom; top panel explains each folder with icons.

## 9. Rules for designing a video in this style
1. Use one continuous board: zero hard cuts, and at most 3 full clears per video.
2. Keep the background flat #0B0B0C. All content goes in rounded panels #1A1A1C (radius 14–18 px) with 36–44 px side margins.
3. Keep all diagram content between 13% and 75% height. Leave the bottom ~22% empty except for a caption, stat or stepper.
4. Put the section title only in the 6–13% slot, 1–4 words, small-caps hand font, with exactly one keyword in its entity colour.
5. Use 3–4 accents per video and bind each to one entity for the whole video. Pink = failure/attack, green = success, amber = current focus.
6. Every panel header is icon (or numbered dot) + small-caps label in the panel's accent, plus optional right-aligned tag pills.
7. Use real tool/product glyphs as icons wherever a real product is named.
8. Introduce or change something every 1.5–3 s, synced to the narration clause that names it.
9. Show focus by dimming non-focused elements to ~30% opacity. Add a dashed box or accent border on the target. Never leave more than one thing at full emphasis for long.
10. Show state changes on the same object (recolour, crack + "CRASHED" pill, ✓/✗, lock, bar fill) instead of replacing it.
11. Move data as small pills/cards travelling along connectors. Label the pill with the actual payload (URL, ID, token).
12. Show code, configs and terminal output in a mono window with dots, and highlight the one substring being discussed.
13. Show scale with a grid of ≥20 tiny icons or a big mono number with a small-caps sub-label.
14. No word-by-word subtitles. On-screen captions are ≤7 words and appear only for key claims or questions.
15. Open on a centred hook (question title + hero logo/icon) or directly inside the concrete scenario. Move into the first panel by 3–6 s.
16. End by blurring the final full diagram and showing a small follow/subscribe card (with our own branding).
17. Name a person ("Alan", "John") or a concrete product scenario in the first 10 s and keep that avatar on screen as an anchor.
18. Use camera moves sparingly (≤3 per video): a slow push-in with the rest blurred, or a shrink of the old diagram into a thumbnail.

## 10. Gaps vs our kit (prioritized)
1. **Global Spotlight/Dim controller.** A declarative "focus set" per beat. Everything else animates to 30% opacity, with optional 4–8 px blur. This is the single most used device, and our Focus box alone is not enough.
2. **TitleSlot with cross-fade + keyword colouring.** A fixed top slot that swaps section names. Our stage Title appears to be a one-off; this needs to be persistent and swappable, with `**word**` → accent.
3. **Sticker / Callout.** A tilted (−8°) filled pill with an optional speech tail or pointer line ("DEFAULT CHOICE", "HOTSPOT!"). Also a plain centred short Caption under the diagram.
4. **State/Status system for Nodes and Panels.** Variants ok/warn/error/dead: red tint, crack overlay, status pill, ✓/✗/lock/key badges, and a "dim/disabled" state.
5. **Crowd/IconGrid + BigStat.** An N×M grid of tiny icons (users, servers, files) with staggered fill/colour wave, plus a big number with a sub-label.
6. **Meter/ProgressBar + Timeline.** Horizontal and vertical fill bars (load, disk, upload %, TTL), and a simple time axis with markers (RPO/RTO, token expiry). Also a Stepper (1→2→3 chips joined by "+", or dots) at the top or bottom.
7. **Logo/Avatar tiles.** A generic icon-tile slot that takes an SVG product glyph, a photo/illustrated avatar with a name label, and a hacker icon. We will supply our own assets, but the slot and layout are needed.
8. **Blurred-scene EndCard + Tree/Sequence helpers.** The EndCard should overlay a blurred final board (not a separate slide). Add a Tree layout (B-tree/parse tree auto-layout) and a two-lifeline SequenceDiagram for handshakes.

Doing differently today: the Takeaway line should be a final section title or short caption, not a persistent bar. Use the Camera zoom rarely, and pair it with background blur. Phone/Browser mockups should be small (≈35–60% width) components inside the board, not full-screen.
