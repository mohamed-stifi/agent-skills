import { continueRender, delayRender } from 'remotion';
import '@fontsource/barlow-condensed/600.css';
import '@fontsource/barlow-condensed/700.css';
import '@fontsource/barlow-condensed/800.css';
import '@fontsource/barlow/400.css';
import '@fontsource/barlow/500.css';
import '@fontsource/barlow/600.css';
import '@fontsource/barlow/700.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/600.css';

const handle = delayRender('fonts');
const specs = [
  '600 40px "Barlow Condensed"', '700 40px "Barlow Condensed"', '800 40px "Barlow Condensed"',
  '400 20px "Barlow"', '500 20px "Barlow"', '600 20px "Barlow"', '700 20px "Barlow"',
  '400 20px "IBM Plex Mono"', '500 20px "IBM Plex Mono"', '600 20px "IBM Plex Mono"',
];
Promise.all(specs.map((s) => document.fonts.load(s)))
  .then(() => continueRender(handle))
  .catch(() => continueRender(handle));
