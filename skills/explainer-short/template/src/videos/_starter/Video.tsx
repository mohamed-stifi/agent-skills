import React from 'react';
import {Audio, staticFile} from 'remotion';
import {Canvas, EndCard, Hook} from '../../kit';
import script from './script.json';
import {narrationEnd, sec} from './t';

const SLUG = '__SLUG__';
export {total} from './t';

export const Video: React.FC = () => (
  <Canvas brand={script.brand}>
    <Audio src={staticFile(`${SLUG}/voice.wav`)} />
    <Hook out={sec('hook').to}>{script.title}</Hook>
    {/* stages go here — see the example video */}
    <EndCard at={narrationEnd} brand={script.brand} />
  </Canvas>
);
