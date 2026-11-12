import React from 'react';
import {useCurrentFrame} from 'remotion';
import {Actor, Arrow, c, Chip, Code, El, Focus, Packet, Panel, Sticker, Tag, Takeaway, Title} from '../../../kit';
import {cue, sec} from '../t';
import {SCRIPT_CENTER} from './Flood';

const B = {x: 240, y: 700, w: 600, h: 300}; // the bucket panel
const TOKEN = 64;
const GAP = 26;
// center of token i (5 per row) in canvas coords — used to place the Focus box exactly
const tokenPos = (i: number) => ({
  x: B.x + (B.w - (5 * TOKEN + 4 * GAP)) / 2 + (i % 5) * (TOKEN + GAP),
  y: B.y + 110 + Math.floor(i / 5) * (TOKEN + GAP),
});

/** How many tokens are in the bucket at a frame. Derived from the same cues the packets use. */
const useTokens = () => {
  const f = useCurrentFrame();
  const fire = cue('burst', 'fires');
  const normalFrom = sec('normal').from;
  if (f < fire) return 10;
  if (f < normalFrom) {
    let used = 0;
    for (let i = 0; i < 10; i++) if (f >= fire + i * 7 + 10) used++;
    return 10 - used;
  }
  const refill = Math.min(10, Math.floor((f - normalFrom) / 2));
  if (f < cue('normal', 'sends') + 14) return refill;
  if (f < cue('normal', 'refills')) return 9;
  return 10;
};

const BucketPanel: React.FC = () => {
  const f = useCurrentFrame();
  const n = useTokens();
  const owner = f < sec('normal').from ? "buggy script's bucket" : "normal app's bucket";
  return (
    <Panel label={owner} icon="box" color={c.amber} active>
      <div style={{display: 'flex', flexWrap: 'wrap', gap: GAP, justifyContent: 'center', width: 5 * TOKEN + 4 * GAP, margin: '14px auto 0'}}>
        {Array.from({length: 10}, (_, i) => (
          <div
            key={i}
            style={{
              width: TOKEN,
              height: TOKEN,
              borderRadius: '50%',
              boxSizing: 'border-box',
              background: i < n ? c.amber : 'transparent',
              border: `3px ${i < n ? 'solid' : 'dashed'} ${i < n ? c.amber : c.dim}`,
              boxShadow: i < n ? `0 0 18px ${c.amber}55` : undefined,
            }}
          />
        ))}
      </div>
    </Panel>
  );
};

export const Bucket: React.FC = () => {
  const b = sec('bucket');
  const fire = cue('burst', 'fires');
  const eleventh = cue('burst', 'eleventh');
  const r429 = cue('burst', '429');
  const leave = sec('tradeoff').from;
  const up: [number, number][] = [
    [540, 1110],
    [540, 1010],
    [540, 700],
    [540, 548],
  ];
  return (
    <>
      <Title at={b.from} out={sec('normal').from} color={c.amber}>
        Token **bucket**
      </Title>
      <Title at={sec('normal').from} out={leave} color={c.green}>
        A normal app
      </Title>

      <El id="bucket" at={cue('bucket', 'bucket', 2)} out={leave} x={B.x} y={B.y} w={B.w} h={B.h} enter="pop">
        <BucketPanel />
      </El>
      <El at={cue('bucket', 'ten')} out={sec('burst').from} x={B.x} y={B.y - 64}>
        <Tag color={c.amber}>10 tokens</Tag>
      </El>
      <Focus at={cue('bucket', 'takes one')} out={cue('bucket', 'refills')} x={tokenPos(0).x} y={tokenPos(0).y} w={TOKEN} h={TOKEN} />
      <El at={cue('bucket', 'refills')} out={leave} x={B.x + B.w - 290} y={B.y - 64}>
        <Tag color={c.green}>+1 token / second</Tag>
      </El>

      <Arrow id="aIn" at={b.from + 10} out={leave} path={[[540, 1110], [540, 1012]]} color={c.dim} />
      <Arrow at={b.from + 16} out={leave} path={[[540, 696], [540, 552]]} color={c.dim} />

      {/* Burst: 10 requests pass and each takes a token */}
      {Array.from({length: 10}, (_, i) => (
        <Packet key={i} at={fire + i * 7} dur={26} out={fire + i * 7 + 26} path={up}>
          <div style={{width: 24, height: 24, borderRadius: 6, background: c.red, boxShadow: `0 0 14px ${c.red}`}} />
        </Packet>
      ))}
      <Takeaway at={cue('burst', 'go')} out={eleventh} color={c.green} y={1330}>
        10 requests through
      </Takeaway>

      {/* The 11th is stopped at the bucket and gets a 429 back */}
      <Packet at={eleventh} dur={16} out={r429} path={[[540, 1110], [540, 1030]]}>
        <div style={{width: 24, height: 24, borderRadius: 6, background: c.red, boxShadow: `0 0 14px ${c.red}`}} />
      </Packet>
      <Focus at={cue('burst', 'empty')} out={r429} x={B.x} y={B.y} w={B.w} h={B.h} color={c.red} />
      <El at={cue('burst', 'empty')} out={sec('normal').from} x={B.x + B.w - 120} y={B.y + B.h - 30} enter="pop" z={8}>
        <Sticker color={c.red}>EMPTY!</Sticker>
      </El>
      <Packet at={r429} dur={20} out={sec('normal').from} path={[[700, 1030], [700, 1110]]}>
        <Chip color={c.red}>429</Chip>
      </Packet>
      <El id="code" at={r429 + 6} out={sec('normal').from} x={140} y={1310} w={800}>
        <Code
          title="response"
          lines={['HTTP/1.1 429 Too Many Requests', 'Retry-After: 1']}
          at={r429 + 6}
          size={30}
          marks={[
            {line: 0, text: '429 Too Many Requests', at: r429 + 10, color: c.red},
            {line: 1, text: 'Retry-After: 1', at: cue('burst', 'Retry-After')},
          ]}
        />
      </El>

      {/* Normal app: one request, one token, refilled before the next */}
      <El at={sec('normal').from} out={leave} x={SCRIPT_CENTER.x} y={SCRIPT_CENTER.y} anchor="c" enter="pop">
        <Actor icon="phone" label="normal app" color={c.green} />
      </El>
      <Packet at={cue('normal', 'sends')} dur={26} out={cue('normal', 'sends') + 26} path={up}>
        <Chip color={c.green} size={22}>GET /weather</Chip>
      </Packet>
      <Takeaway at={cue('normal', 'never')} out={leave} color={c.green} y={1330}>
        It never notices the limit.
      </Takeaway>
    </>
  );
};
