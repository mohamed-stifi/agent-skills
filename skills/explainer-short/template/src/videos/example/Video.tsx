import React from 'react';
import {Audio, staticFile} from 'remotion';
import {c, Canvas, EndCard, Hook, Title} from '../../kit';
import script from './script.json';
import {cue, narrationEnd, sec} from './t';
import {Bucket} from './stages/Bucket';
import {Flood} from './stages/Flood';
import {TradeOff} from './stages/TradeOff';

const SLUG = 'example';
export {total} from './t';

export const Video: React.FC = () => (
  <Canvas
    brand={script.brand}
    focus={[
      // Spotlight plan: from each frame, only these ids stay bright (others dim to 30 %). [] = all lit.
      [cue('scenario', 'buggy'), ['script', 'aScript', 'server']],
      [sec('bucket').from, []],
      [cue('bucket', 'takes one'), ['bucket']],
      [cue('bucket', 'refills'), []],
      [cue('burst', 'eleventh'), ['bucket', 'script', 'code', 'aIn']],
      [sec('normal').from, []],
    ]}
  >
    <Audio src={staticFile(`${SLUG}/voice.wav`)} />

    {/* Hook: the question, then the name of the idea */}
    <Hook out={cue('hook', 'called')} icon="shield" color={c.cyan}>
      How do APIs stop a flood?
    </Hook>
    <Title at={cue('hook', 'rate')} out={sec('scenario').from} y={760} size={130} color={c.cyan}>
      Rate limiting
    </Title>

    <Flood />
    <Bucket />
    <TradeOff />

    <EndCard at={narrationEnd} brand={script.brand} />
  </Canvas>
);
