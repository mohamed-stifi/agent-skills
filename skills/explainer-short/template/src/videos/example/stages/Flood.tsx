import React from 'react';
import {interpolateColors, useCurrentFrame} from 'remotion';
import {Actor, Arrow, c, Chip, El, Hand, Packet, Panel, Takeaway, Title, val} from '../../../kit';
import {cue, sec} from '../t';

// Positions shared with the next stage live here (one source of truth).
export const SERVER = {x: 290, y: 330, w: 500, h: 210};
export const NORMAL = {x: 230, y: 1180};
export const SCRIPT = {x: 850, y: 1180};
export const SCRIPT_CENTER = {x: 540, y: 1180};

/** The server card changes STATE (same object): normal -> overloaded -> normal. */
const Server: React.FC<{flood: number; calm: number}> = ({flood, calm}) => {
  const f = useCurrentFrame();
  const bad = f >= flood + 30 && f < calm;
  return (
    <Panel label="weather API" icon="server" state={bad ? 'error' : 'normal'} status={bad ? 'overloaded' : 'ok'}>
      <Load from={flood} to={calm} />
    </Panel>
  );
};

/** Server load: grows and turns red when the flood starts. */
const Load: React.FC<{from: number; to: number}> = ({from, to}) => {
  const frame = useCurrentFrame();
  const p = val(frame, [
    [from, 0.18],
    [from + 40, 0.95],
    [to, 0.95],
    [to + 30, 0.25],
  ]);
  const color = interpolateColors(p, [0.2, 0.9], [c.green, c.red]);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
      <Hand size={28} color={c.muted}>load</Hand>
      <div style={{flex: 1, height: 18, borderRadius: 9, background: c.panel2}}>
        <div style={{width: `${p * 100}%`, height: '100%', borderRadius: 9, background: color}} />
      </div>
    </div>
  );
};

export const Flood: React.FC = () => {
  const s = sec('scenario');
  const flood = cue('scenario', 'five hundred');
  const end = sec('bucket').from; // things that leave when the bucket appears
  return (
    <>
      <Title at={s.from} out={end} accent={c.cyan}>
        Maya's **weather API**
      </Title>

      {/* The server stays for 4 sections: it is the anchor of the canvas */}
      <El id="server" at={cue('scenario', 'weather')} out={sec('tradeoff').from} x={SERVER.x} y={SERVER.y} w={SERVER.w} h={SERVER.h}>
        <Server flood={flood} calm={cue('burst', 'go')} />
      </El>

      {/* Normal app: one calm request */}
      <El id="normal" at={cue('scenario', 'apps')} out={end} x={NORMAL.x} y={NORMAL.y} anchor="c" enter="pop">
        <Actor icon="phone" label="normal app" color={c.green} />
      </El>
      <Arrow at={cue('scenario', 'apps') + 6} out={end} path={[[NORMAL.x, NORMAL.y - 100], [450, 560]]} color={c.dim} />
      <Packet at={cue('scenario', 'few')} dur={30} out={cue('scenario', 'few') + 32} path={[[NORMAL.x, NORMAL.y - 100], [450, 560]]}>
        <Chip color={c.green} size={22}>GET /weather</Chip>
      </Packet>

      {/* Buggy script: keeps its place, then moves to the center for the next stage */}
      <El
        id="script"
        at={cue('scenario', 'buggy')}
        out={sec('normal').from}
        x={[
          [end, SCRIPT.x],
          [end + 20, SCRIPT_CENTER.x],
        ]}
        y={SCRIPT.y}
        anchor="c"
        enter="pop"
      >
        <Actor icon="terminal" label="buggy script" color={c.red} />
      </El>
      <Arrow id="aScript" at={cue('scenario', 'buggy') + 6} out={end} path={[[SCRIPT.x, SCRIPT.y - 100], [630, 560]]} color={c.red} dashed />
      {Array.from({length: 14}, (_, i) => (
        <Packet key={i} at={flood + i * 5} dur={22} out={flood + i * 5 + 22} path={[[SCRIPT.x, SCRIPT.y - 100], [630, 560]]}>
          <div style={{width: 22, height: 22, borderRadius: 6, background: c.red, boxShadow: `0 0 16px ${c.red}`}} />
        </Packet>
      ))}

      <Takeaway at={cue('scenario', 'slow')} out={end} color={c.red}>
        One user slows down **everyone**.
      </Takeaway>
    </>
  );
};
