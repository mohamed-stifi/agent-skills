import React from 'react';
import {c, El, Focus, Hand, Icon, Panel, Sticker, Takeaway, Title} from '../../../kit';
import {cue, sec} from '../t';

/** One pro/con line that appears on its cue. */
const Point: React.FC<{at: number; good: boolean; children: React.ReactNode}> = ({at, good, children}) => (
  <El at={at} x={0} y={0} enter="left" style={{position: 'relative'}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
      <Icon name={good ? 'check' : 'x'} size={38} color={good ? c.green : c.red} stroke={2.6} />
      <Hand size={34}>{children}</Hand>
    </div>
  </El>
);

const Tokens: React.FC<{n: number; size: number}> = ({n, size}) => (
  <div style={{display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', padding: '10px 0'}}>
    {Array.from({length: n}, (_, i) => (
      <div key={i} style={{width: size, height: size, borderRadius: '50%', background: c.amber}} />
    ))}
  </div>
);

export const TradeOff: React.FC = () => {
  const t = sec('tradeoff');
  const end = sec('cta').to;
  return (
    <>
      <Title at={t.from} out={end}>
        Trade-**off**
      </Title>

      <El at={cue('tradeoff', 'big bucket')} x={60} y={330} w={465} h={560} enter="left">
        <Panel label="big bucket" icon="box" color={c.amber}>
          <Tokens n={20} size={34} />
          <div style={{display: 'flex', flexDirection: 'column', gap: 18, marginTop: 10}}>
            <Point at={cue('tradeoff', 'allows')} good>allows bursts</Point>
            <Point at={cue('tradeoff', 'abuse')} good={false}>more abuse</Point>
          </div>
        </Panel>
      </El>

      <El at={cue('tradeoff', 'small bucket')} x={555} y={330} w={465} h={560} enter="right">
        <Panel label="small bucket" icon="box" color={c.amber}>
          <Tokens n={4} size={34} />
          <div style={{display: 'flex', flexDirection: 'column', gap: 18, marginTop: 10}}>
            <Point at={cue('tradeoff', 'protects')} good>protects servers</Point>
            <Point at={cue('tradeoff', 'block')} good={false}>blocks real users</Point>
          </div>
        </Panel>
      </El>

      <El at={cue('tradeoff', 'images')} out={cue('tradeoff', 'abuse')} x={60} y={940} w={465}>
        <Hand size={30} color={c.muted} style={{textAlign: 'center'}}>
          e.g. a page loading 30 images
        </Hand>
      </El>

      <El at={cue('tradeoff', 'most')} x={720} y={870} enter="pop" z={8}>
        <Sticker color={c.cyan}>MOST APIs</Sticker>
      </El>
      <Focus at={cue('tradeoff', 'most')} x={60} y={330} w={960} h={560} color={c.cyan} />
      <Takeaway at={cue('tradeoff', 'just big')} color={c.cyan} y={1000}>
        Just big enough for **normal bursts**.
      </Takeaway>
    </>
  );
};
