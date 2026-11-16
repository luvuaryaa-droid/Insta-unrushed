// Analogue finishing layers: paper, grain, gobo shadows, light leaks, dust, vignette, caustics.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { FPS, drift, hash, kf, KF } from './lib';

export const Paper: React.FC<{ tint?: string; opacity?: number }> = ({ tint, opacity = 1 }) => (
  <AbsoluteFill style={{ opacity }}>
    <Img src={staticFile('tex/paper.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
    {tint ? <AbsoluteFill style={{ background: tint, mixBlendMode: 'multiply' }} /> : null}
  </AbsoluteFill>
);

export const Grain: React.FC<{ amount?: number }> = ({ amount = 0.11 }) => {
  const fr = useCurrentFrame();
  const i = Math.floor(hash(fr * 3.1) * 8);
  const ox = Math.floor(hash(fr + 0.5) * 120);
  const oy = Math.floor(hash(fr + 7.5) * 80);
  return (
    <AbsoluteFill style={{ overflow: 'hidden', mixBlendMode: 'overlay', opacity: amount * 3 }}>
      <Img
        src={staticFile(`tex/grain${i}.png`)}
        style={{ position: 'absolute', left: -ox, top: -oy, width: 2040, height: 1160, imageRendering: 'auto' }}
      />
    </AbsoluteFill>
  );
};

// Dust, hairs and the odd scratch, like a projected 16mm print.
export const Dust: React.FC = () => {
  const fr = useCurrentFrame();
  const specks: React.ReactNode[] = [];
  const n = Math.floor(hash(fr * 1.7) * 4);
  for (let k = 0; k < n; k++) {
    const h = (o: number) => hash(fr * 13.1 + k * 7.7 + o);
    const big = h(4) > 0.85;
    specks.push(
      <div
        key={k}
        style={{
          position: 'absolute',
          left: h(1) * 1920,
          top: h(2) * 1080,
          width: big ? 2 + h(3) * 3 : 1.5 + h(3) * 2.5,
          height: big ? 14 + h(5) * 26 : 1.5 + h(3) * 2.5,
          borderRadius: big ? 2 : '50%',
          transform: `rotate(${h(6) * 180}deg)`,
          background: h(7) > 0.3 ? 'rgba(20,14,10,0.55)' : 'rgba(255,248,235,0.6)',
          filter: 'blur(0.4px)',
        }}
      />,
    );
  }
  // a faint vertical scratch every so often
  if (hash(Math.floor(fr / 3) * 5.3) > 0.93) {
    specks.push(
      <div
        key="scratch"
        style={{
          position: 'absolute',
          left: hash(Math.floor(fr / 3)) * 1920,
          top: 0,
          width: 1,
          height: 1080,
          background: 'rgba(255,250,240,0.18)',
        }}
      />,
    );
  }
  return <AbsoluteFill style={{ pointerEvents: 'none' }}>{specks}</AbsoluteFill>;
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.55 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(18,10,6,${strength}) 100%)`,
    }}
  />
);

// Drifting window/leaf shadow, the same light that falls across the mockup walls.
export const Gobo: React.FC<{ opacity?: number; seed?: number }> = ({ opacity = 0.16, seed = 1 }) => {
  const fr = useCurrentFrame();
  const t = fr / FPS;
  const x = -300 + drift(t, seed, 0.08) * 120 + t * 4;
  const y = -180 + drift(t, seed + 2, 0.06) * 60;
  const sway = drift(t, seed + 5, 0.5) * 1.2;
  return (
    <AbsoluteFill style={{ mixBlendMode: 'multiply', opacity, overflow: 'hidden' }}>
      <Img
        src={staticFile('tex/gobo.png')}
        style={{ position: 'absolute', left: x, top: y, width: 2600, height: 1500, transform: `rotate(${sway}deg)`, filter: 'blur(3px)' }}
      />
    </AbsoluteFill>
  );
};

export const Caustics: React.FC<{ opacity?: number }> = ({ opacity = 0.12 }) => {
  const t = useCurrentFrame() / FPS;
  return (
    <AbsoluteFill style={{ mixBlendMode: 'screen', opacity, overflow: 'hidden' }}>
      <Img
        src={staticFile('tex/caustic.png')}
        style={{
          position: 'absolute',
          left: -200 + Math.sin(t * 0.3) * 80,
          top: -150 + t * 6 - 300,
          width: 2400,
          height: 1350,
          transform: `scale(${1.1 + Math.sin(t * 0.21) * 0.05}) rotate(${Math.sin(t * 0.13) * 3}deg)`,
          filter: 'blur(1.5px) sepia(0.2) hue-rotate(150deg)',
        }}
      />
    </AbsoluteFill>
  );
};

// Warm light leak burning in from a frame edge. `at` = peak time in seconds.
export const LightLeak: React.FC<{ at: number; dur?: number; side?: 'l' | 'r' | 't'; peak?: number; hue?: string }> = ({
  at,
  dur = 1.2,
  side = 'r',
  peak = 0.85,
  hue = '255,150,70',
}) => {
  const t = useCurrentFrame() / FPS;
  const keys: KF = [
    [at - dur * 0.45, 0],
    [at, peak],
    [at + dur * 0.55, 0],
  ];
  const o = kf(t, keys);
  if (o <= 0.001) return null;
  const pos = side === 'l' ? '0% 40%' : side === 't' ? '55% 0%' : '100% 55%';
  const wob = drift(t, at, 1.5) * 8;
  return (
    <AbsoluteFill
      style={{
        mixBlendMode: 'screen',
        opacity: o,
        background: `radial-gradient(ellipse 60% 85% at ${pos}, rgba(${hue},0.95) 0%, rgba(255,90,60,0.45) ${35 + wob}%, rgba(0,0,0,0) 75%)`,
      }}
    />
  );
};
