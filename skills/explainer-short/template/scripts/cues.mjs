// Fast cue lint (no render): finds every literal cue('section', 'words', n?) in a video's source and checks it
// against timing.json with the same matching rules as the kit. usage: node scripts/cues.mjs <slug>
import fs from 'node:fs';
import path from 'node:path';
const slug = process.argv[2];
const dir = `src/videos/${slug}`;
const t = JSON.parse(fs.readFileSync(`${dir}/timing.json`, 'utf8'));
const norm = (s) => s.toLowerCase().replace(/^[^\w]+|[^\w]+$/g, '');
const files = [];
const walk = (d) => fs.readdirSync(d).forEach((f) => { const p = path.join(d, f); fs.statSync(p).isDirectory() ? walk(p) : /\.tsx?$/.test(f) && files.push(p); });
walk(dir);
const re = /\bcue\(\s*(['"`])([^'"`]+)\1\s*,\s*(['"`])([^'"`]+)\3\s*(?:,\s*(\d+))?/g;
const secRe = /\bsec\(\s*(['"`])([^'"`]+)\1\s*\)/g;
let bad = 0, n = 0;
const ids = new Set(t.sections.map((s) => s.id));
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  for (const m of src.matchAll(secRe)) if (!ids.has(m[2])) { bad++; console.log(`${f}: sec('${m[2]}') — no such section. Sections: ${[...ids].join(', ')}`); }
  for (const m of src.matchAll(re)) {
    n++;
    const [, , id, , phrase, nth = '1'] = m;
    if (!ids.has(id)) { bad++; console.log(`${f}: cue('${id}', '${phrase}') — no such section`); continue; }
    const ws = t.words.filter((w) => w.sec === id).map((w) => norm(w.w));
    const want = phrase.split(/\s+/).map(norm);
    let hits = 0;
    for (let i = 0; i + want.length <= ws.length; i++) if (want.every((p, k) => ws[i + k] === p)) hits++;
    if (hits < Number(nth)) { bad++; console.log(`${f}: cue('${id}', '${phrase}', ${nth}) — found ${hits}×. Words: ${ws.join(' ')}`); }
  }
}
console.log(bad ? `CUE ERRORS: ${bad} (of ${n} cues)` : `cues ok (${n})`);
process.exit(bad ? 1 : 0);
