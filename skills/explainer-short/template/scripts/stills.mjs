// Render check frames for one video, fast (bundles once), and tile them into one contact sheet.
// usage: node scripts/stills.mjs <slug> [sec,sec,...]
// Default frames: for every section -> just after start, middle, just before end.
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';

const [slug, list] = process.argv.slice(2);
if (!slug) { console.error('usage: node scripts/stills.mjs <slug> [sec,sec,...]'); process.exit(1); }
const timing = JSON.parse(fs.readFileSync(`src/videos/${slug}/timing.json`, 'utf8'));
const FPS = 30;
let shots = [];
for (const s of timing.sections) {
  const a = s.start * FPS, b = s.end * FPS;
  shots.push({label: `${s.id} start`, frame: Math.round(a + 20)}, {label: `${s.id} mid`, frame: Math.round((a + b) / 2)}, {label: `${s.id} end`, frame: Math.round(b - 8)});
}
if (list) for (const x of list.split(',').filter(Boolean)) shots.push({label: `extra t=${x}s`, frame: Math.round(Number(x) * FPS)});
shots.sort((a, b) => a.frame - b.frame);
shots.push({label: 'end card', frame: Math.round(timing.totalSec * FPS) + 60});
const outDir = path.resolve(`out/${slug}/check`);
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: slug});
shots = shots.filter((s) => s.frame >= 0 && s.frame < composition.durationInFrames);
let i = 0;
for (const s of shots) {
  const file = path.join(outDir, `${String(++i).padStart(2, '0')}.jpg`);
  await renderStill({serveUrl, composition, frame: s.frame, output: file, imageFormat: 'jpeg', scale: 0.5});
  console.log(`${String(i).padStart(2, '0')}  frame ${String(s.frame).padStart(5)}  ${(s.frame / FPS).toFixed(1).padStart(6)}s  ${s.label}`);
}
const cols = 6;
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-pattern_type', 'glob', '-i', path.join(outDir, '*.jpg'),
  '-vf', `scale=270:480,tile=${cols}x${Math.ceil(shots.length / cols)}:padding=6:color=white`, '-frames:v', '1', path.join(outDir, 'sheet.jpg')]);
console.log(`\nSheet: out/${slug}/check/sheet.jpg  (tiles left->right, top->bottom, numbered as above)`);
console.log(`Single frames (larger): out/${slug}/check/NN.jpg`);
