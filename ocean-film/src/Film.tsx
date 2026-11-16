// Master timeline + the global film finish (grade, gate weave, flicker, grain, dust, leaks).
import React from 'react';
import { AbsoluteFill, Audio, continueRender, delayRender, staticFile, useCurrentFrame } from 'remotion';
import { Dust, Grain, LightLeak, Vignette } from './fx';
import { Handwriting, InkLine, Scribble } from './parts';
import { FPS, drift, kf, hash } from './lib';
import {
  Collision, Deep, Diya, Dive, EndCard, Flood, GalleryBreak, GalleryOne, InkDrop, Lantern, Latte, Moka, Mosaic,
  Nook, Opening, Portraits, Rising, Sapling, Seasons, Show, Walker,
} from './scenes';

const fontHandle = delayRender('Caveat font');
const caveat = new FontFace('Caveat', `url(${staticFile('Caveat.ttf')})`, { weight: '400 700' });
caveat
  .load()
  .then((ff) => {
    (document.fonts as unknown as { add: (f: FontFace) => void }).add(ff);
    continueRender(fontHandle);
  })
  .catch((e) => {
    console.error(e);
    continueRender(fontHandle);
  });

export const Film: React.FC = () => {
  const fr = useCurrentFrame();
  const t = fr / FPS;
  // monochrome "familiar" self until the drums, then colour floods in
  const sat = kf(t, [[0, 0.5], [17.2, 0.5], [18.4, 1.0], [53, 1.0], [54, 1.06]]);
  const flicker = 1 + (hash(fr * 2.71) - 0.5) * 0.025;
  const wx = drift(t, 501, 3) * 1.1;
  const wy = drift(t, 502, 2.5) * 1.4;
  return (
    <AbsoluteFill style={{ background: '#000' }}>
      <Audio src={staticFile('ocean.mp3')} />
      <AbsoluteFill
        style={{
          transform: `translate(${wx}px,${wy}px) scale(1.004)`,
          filter: `saturate(${sat}) contrast(1.05) brightness(${flicker})`,
        }}
      >
        {/* ACT I */}
        <Show from={0} to={3.4}><Opening /></Show>
        <Show from={0} to={3.4}><InkLine start={0.45} dur={1.6} y={770} out={2.4} /></Show>
        <Show from={1.8} to={9.25}><Moka /></Show>
        <Show from={9.2} to={18.7}><GalleryOne /></Show>
        <Show from={15.4} to={18.7}><InkDrop /></Show>
        {/* ACT II */}
        <Show from={17.8} to={22.8}><Lantern /></Show>
        <Show from={22.25} to={27.3}><Portraits /></Show>
        <Show from={26.7} to={31.6}><Seasons /></Show>
        <Show from={31.1} to={35.65}><Walker /></Show>
        {/* ACT III */}
        <Show from={35.63} to={40.95}><Collision /></Show>
        <Show from={40.09} to={45.05}><Sapling /></Show>
        <Show from={44.53} to={46.79}><Latte /></Show>
        <Show from={46.78} to={49.0}><GalleryBreak /></Show>
        <Show from={49.0} to={53.5}><Diya /></Show>
        <Show from={52.3} to={53.5}><Flood /></Show>
        {/* ACT IV */}
        <Show from={53.42} to={80.4}><Deep /></Show>
        <Show from={53.42} to={67.6}><Dive /></Show>
        <Show from={66.4} to={74.5}><Rising /></Show>
        <Show from={79.3} to={85.9}><Nook /></Show>
        <Show from={73.45} to={80.4}><Mosaic /></Show>
        {/* ENDING */}
        <Show from={85.0} to={87.7}><EndCard /></Show>

        {/* the critic's line, crossed out */}
        <Handwriting
          start={1.1}
          cps={11}
          out={6.5}
          color="#3a3532"
          glow="rgba(255,255,255,0)"
          weight={500}
          seed={2}
          lines={[{ text: 'you change too much', x: 1435, y: 640, size: 60, rot: -3 }]}
        />
        <Scribble x={1430} y={640} w={440} h={56} start={5.75} dur={0.45} color="#1d1a3a" out={6.5} />

        <LightLeak at={2.1} side="l" peak={0.45} />
        <LightLeak at={17.85} side="r" peak={0.8} dur={1.0} />
        <LightLeak at={31.2} side="t" peak={0.7} />
        <LightLeak at={53.5} side="l" peak={0.55} hue="120,175,255" />
        <LightLeak at={79.7} side="r" peak={0.55} dur={1.5} />
        <LightLeak at={85.3} side="t" peak={0.45} dur={1.6} />
      </AbsoluteFill>
      {/* warm print grade + lifted blacks */}
      <AbsoluteFill style={{ background: 'rgba(255,160,80,0.07)', mixBlendMode: 'soft-light' }} />
      <AbsoluteFill style={{ background: 'rgba(40,24,14,0.06)', mixBlendMode: 'screen' }} />
      <Vignette strength={0.5} />
      <Grain amount={0.1} />
      <Dust />
    </AbsoluteFill>
  );
};
