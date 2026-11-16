// Building blocks: painted sheets, camera, glows, handwriting, ink/torn/ripple transitions.
import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { Gif } from '@remotion/gif';
import { ART } from './art';
import { FPS, blobPolygon, clamp, drift, ease, hash, lerp, prog, tornEdge } from './lib';

export const useT = () => useCurrentFrame() / FPS;

export const artSrc = (name: string) =>
  name.startsWith('mock_') ? staticFile(`mock/${name.slice(5)}.jpg`) : staticFile(`art/${ART[name][0]}`);
export const aspect = (name: string) => ART[name][1] / ART[name][2];

export const PAPER = '#f2e9d6';
export const INK = '#231c1a';

// ---------------------------------------------------------------- camera
// Looks at world point (x, y) with zoom s and roll r (deg). `hand` adds handheld drift in px.
export const Cam: React.FC<{
  x?: number; y?: number; s?: number; r?: number; hand?: number; seed?: number; children: React.ReactNode;
}> = ({ x = 960, y = 540, s = 1, r = 0, hand = 4, seed = 1, children }) => {
  const t = useT();
  const hx = drift(t, seed, 0.45) * hand;
  const hy = drift(t, seed + 3, 0.4) * hand;
  const hr = drift(t, seed + 6, 0.3) * hand * 0.06;
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: 1920,
          height: 1080,
          transformOrigin: '0 0',
          transform: `translate(960px,540px) rotate(${r + hr}deg) scale(${s}) translate(${-x - hx}px,${-y - hy}px)`,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- sheets
const jaggedRect = (w: number, h: number, seed: number, amp: number, inset = 0) => {
  const step = 10;
  const top = tornEdge(w, seed, amp, step);
  const right = tornEdge(h, seed + 1, amp, step);
  const bot = tornEdge(w, seed + 2, amp, step);
  const left = tornEdge(h, seed + 3, amp, step);
  const p: string[] = [];
  const P = (x: number, y: number) => p.push(`${x.toFixed(1)}px ${y.toFixed(1)}px`);
  for (let i = 0; i * step <= w; i++) P(i * step, inset + Math.abs(top[i]) * 0.6);
  for (let i = 0; i * step <= h; i++) P(w - inset - Math.abs(right[i]) * 0.6, i * step);
  for (let i = Math.floor(w / step); i >= 0; i--) P(i * step, h - inset - Math.abs(bot[i]) * 0.6);
  for (let i = Math.floor(h / step); i >= 0; i--) P(inset + Math.abs(left[i]) * 0.6, i * step);
  return `polygon(${p.join(',')})`;
};

// A painting laid on the scene as a physical sheet of paper: deckled paper margin + soft shadow.
// Children are positioned inside the painting area (use % units).
export const Sheet: React.FC<{
  name: string;
  cx: number;
  cy: number;
  h?: number;
  w?: number;
  rot?: number;
  margin?: number;
  seed?: number;
  shadow?: number;
  opacity?: number;
  scale?: number;
  blur?: number;
  gif?: boolean;
  children?: React.ReactNode;
}> = ({ name, cx, cy, h, w, rot = 0, margin = 9, seed = 3, shadow = 0.38, opacity = 1, scale = 1, blur = 0, gif, children }) => {
  const a = aspect(name);
  const H = h ?? (w as number) / a;
  const W = w ?? H * a;
  const OW = W + margin * 2;
  const OH = H + margin * 2;
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - OW / 2,
        top: cy - OH / 2,
        width: OW,
        height: OH,
        opacity,
        transform: `rotate(${rot}deg) scale(${scale})`,
        filter: `${shadow > 0 ? `drop-shadow(0 ${14 * shadow + 4}px ${26 * shadow + 6}px rgba(25,12,5,${shadow}))` : ''}${blur > 0 ? ` blur(${blur}px)` : ''}`,
      }}
    >
      <div style={{ position: 'absolute', inset: 0, background: PAPER, clipPath: jaggedRect(OW, OH, seed, 3.2) }}>
        <div style={{ position: 'absolute', left: margin, top: margin, width: W, height: H, overflow: 'hidden' }}>
          {gif ? (
            <Gif src={artSrc(name)} width={W} height={H} fit="fill" />
          ) : (
            <Img src={artSrc(name)} style={{ width: '100%', height: '100%', display: 'block' }} />
          )}
          {children}
        </div>
      </div>
    </div>
  );
};

// Blurred, darkened enlargement of a painting used as a colour field behind it.
export const Backdrop: React.FC<{ name: string; blur?: number; bright?: number; sat?: number; seed?: number }> = ({
  name,
  blur = 45,
  bright = 0.55,
  sat = 1.15,
  seed = 2,
}) => {
  const t = useT();
  const s = 1.35 + drift(t, seed, 0.1) * 0.04;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: '#1a1410' }}>
      <Img
        src={artSrc(name)}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${s}) translate(${drift(t, seed + 1, 0.08) * 30}px, ${drift(t, seed + 2, 0.08) * 20}px)`,
          filter: `blur(${blur}px) brightness(${bright}) saturate(${sat})`,
        }}
      />
    </AbsoluteFill>
  );
};

// Light that breathes inside a painting (lantern, moon, flame). Coordinates are fractions of the painting.
export const Glow: React.FC<{ x: number; y: number; r: number; color: string; o: number; ring?: boolean }> = ({
  x,
  y,
  r,
  color,
  o,
  ring,
}) => (
  <div
    style={{
      position: 'absolute',
      left: `${x * 100}%`,
      top: `${y * 100}%`,
      width: `${r * 200}%`,
      transform: 'translate(-50%,-50%)',
      aspectRatio: '1',
      borderRadius: '50%',
      mixBlendMode: 'screen',
      opacity: clamp(o),
      background: ring
        ? `radial-gradient(circle, rgba(0,0,0,0) 30%, ${color} 52%, rgba(0,0,0,0) 72%)`
        : `radial-gradient(circle, ${color} 0%, rgba(0,0,0,0) 68%)`,
    }}
  />
);

// ---------------------------------------------------------------- handwriting
export type Line = { text: string; x: number; y: number; size: number; rot?: number };
export const Handwriting: React.FC<{
  lines: Line[];
  start: number;
  cps?: number;
  out: number;
  color?: string;
  glow?: string;
  seed?: number;
  weight?: number;
}> = ({ lines, start, cps = 14, out, color = '#f6ecd8', glow = 'rgba(0,0,0,0.45)', seed = 1, weight = 600 }) => {
  const t = useT();
  if (t < start - 0.1 || t > out + 1) return null;
  const fade = 1 - prog(t, out, out + 0.7);
  let k = 0;
  return (
    <AbsoluteFill style={{ opacity: fade, filter: `blur(${(1 - fade) * 3}px)` }}>
      {lines.map((ln, li) => {
        const chars = [...ln.text];
        const lineStart = start + k / cps + li * 0.25;
        const el = (
          <div
            key={li}
            style={{
              position: 'absolute',
              left: ln.x,
              top: ln.y,
              fontFamily: 'Caveat',
              fontWeight: weight,
              fontSize: ln.size,
              lineHeight: 1,
              color,
              whiteSpace: 'pre',
              transform: `rotate(${ln.rot ?? -1.5}deg)`,
              textShadow: `0 0 1px ${color}, 0 3px 18px ${glow}`,
            }}
          >
            {chars.map((c, ci) => {
              const ct = lineStart + ci / cps;
              const p = prog(t, ct, ct + 0.14);
              const h = (o: number) => hash(seed * 31 + li * 17 + ci * 3.3 + o);
              return (
                <span
                  key={ci}
                  style={{
                    display: 'inline-block',
                    opacity: p,
                    transform: `translateY(${(h(1) - 0.5) * 0.07 * ln.size + (1 - p) * 6}px) rotate(${(h(2) - 0.5) * 7}deg) scale(${0.97 + h(3) * 0.06})`,
                    filter: p < 1 ? `blur(${(1 - p) * 2}px)` : undefined,
                  }}
                >
                  {c}
                </span>
              );
            })}
          </div>
        );
        k += chars.length;
        return el;
      })}
    </AbsoluteFill>
  );
};

// A pen scribble that crosses something out.
export const Scribble: React.FC<{ x: number; y: number; w: number; h: number; start: number; dur: number; color: string; out: number }> = ({
  x,
  y,
  w,
  h,
  start,
  dur,
  color,
  out,
}) => {
  const t = useT();
  if (t < start) return null;
  const n = 7;
  let d = `M ${x} ${y + h * 0.6}`;
  for (let i = 1; i <= n; i++) {
    const px = x + (w * i) / n + (hash(i) - 0.5) * 18;
    const py = y + (i % 2 ? h * 0.2 : h * 0.85) + (hash(i + 4) - 0.5) * 10;
    d += ` Q ${px - w / n / 2} ${py + (i % 2 ? -8 : 8)} ${px} ${py}`;
  }
  d += ` M ${x - 10} ${y + h * 0.52} C ${x + w * 0.3} ${y + h * 0.4}, ${x + w * 0.7} ${y + h * 0.66}, ${x + w + 14} ${y + h * 0.48}`;
  const p = ease.out(prog(t, start, start + dur));
  const o = 1 - prog(t, out, out + 0.7);
  return (
    <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0, opacity: o }}>
      <path d={d} fill="none" stroke={color} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p} />
    </svg>
  );
};

// A single hand-inked line drawing itself across the paper.
export const InkLine: React.FC<{ start: number; dur: number; y: number; out: number }> = ({ start, dur, y, out }) => {
  const t = useT();
  const p = ease.inOut(prog(t, start, start + dur));
  const o = 1 - prog(t, out, out + 0.8);
  let d = `M 180 ${y}`;
  for (let i = 1; i <= 12; i++) d += ` L ${180 + i * 130} ${y + (noise(i) - 0.5) * 22 + Math.sin(i * 0.9) * 10}`;
  return (
    <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0, opacity: o }}>
      <path d={d} fill="none" stroke={INK} strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p} opacity={0.85} />
      <path d={d} fill="none" stroke={INK} strokeWidth={1.2} transform="translate(2,3)" pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p} opacity={0.4} />
    </svg>
  );
};
const noise = (i: number) => hash(i * 2.3);

// ---------------------------------------------------------------- transitions
// Incoming layer revealed by a torn-paper edge sweeping across, with a white deckle on the tear.
export const TornWipe: React.FC<{ start: number; dur?: number; dir: 'l' | 'r' | 'u' | 'd'; seed?: number; children: React.ReactNode }> = ({
  start,
  dur = 0.45,
  dir,
  seed = 5,
  children,
}) => {
  const t = useT();
  if (t < start) return null;
  const p = ease.inOut(prog(t, start, start + dur));
  if (p >= 1) return <AbsoluteFill>{children}</AbsoluteFill>;
  const horiz = dir === 'l' || dir === 'r';
  const L = horiz ? 1080 : 1920;
  const span = horiz ? 1920 : 1080;
  const jag = tornEdge(L, seed, 22, 12);
  // position of the edge along the sweep axis, from the entry side towards the far side
  const pos = lerp(-80, span + 80, p);
  const mk = (off: number, widthFn: (i: number) => number) => {
    const a: string[] = [];
    const b: string[] = [];
    for (let i = 0; i < jag.length; i++) {
      const along = i * 12;
      const e = pos + jag[i] + off;
      const e2 = e - widthFn(i);
      // map (sweep coordinate, along coordinate) -> screen
      const S = (s: number) => {
        if (dir === 'r') return `${(span - s).toFixed(1)}px ${along}px`; // enters from right
        if (dir === 'l') return `${s.toFixed(1)}px ${along}px`;
        if (dir === 'd') return `${along}px ${s.toFixed(1)}px`; // enters from top
        return `${along}px ${(span - s).toFixed(1)}px`; // enters from bottom
      };
      a.push(S(e));
      b.unshift(S(e2));
    }
    return { a, b };
  };
  // region already covered by the new sheet: from the entry side up to the edge
  const { a } = mk(0, () => 0);
  const entry = (() => {
    if (dir === 'r') return [`${span + 200}px ${L + 50}px`, `${span + 200}px -50px`];
    if (dir === 'l') return [`-200px ${L + 50}px`, `-200px -50px`];
    if (dir === 'd') return [`${L + 50}px -200px`, `-50px -200px`];
    return [`${L + 50}px ${span + 200}px`, `-50px ${span + 200}px`];
  })();
  const covered = `polygon(${[...a, ...entry].join(',')})`;
  const strip = (() => {
    const outer: string[] = [];
    const inner: string[] = [];
    for (let i = 0; i < jag.length; i++) {
      const along = i * 12;
      const e = pos + jag[i];
      const w = 6 + hash(i * 1.7 + seed) * 12 + (noise(i + seed) - 0.5) * 6;
      const S = (s: number) => {
        if (dir === 'r') return `${(span - s).toFixed(1)}px ${along}px`;
        if (dir === 'l') return `${s.toFixed(1)}px ${along}px`;
        if (dir === 'd') return `${along}px ${s.toFixed(1)}px`;
        return `${along}px ${(span - s).toFixed(1)}px`;
      };
      outer.push(S(e + w));
      inner.unshift(S(e - 1));
    }
    return `polygon(${[...outer, ...inner].join(',')})`;
  })();
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: 'drop-shadow(0 0 10px rgba(20,10,5,0.45))' }}>
        <AbsoluteFill style={{ background: PAPER, clipPath: strip }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ clipPath: covered }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// Incoming layer blooms out of an ink blot.
export const InkReveal: React.FC<{
  start: number;
  dur?: number;
  cx?: number;
  cy?: number;
  maxR?: number;
  seed?: number;
  rim?: string;
  children: React.ReactNode;
}> = ({ start, dur = 0.8, cx = 960, cy = 540, maxR = 1250, seed = 2, rim = '#1b1a2a', children }) => {
  const t = useT();
  if (t < start) return null;
  const p = prog(t, start, start + dur);
  if (p >= 1) return <AbsoluteFill>{children}</AbsoluteFill>;
  const r = maxR * ease.outQuart(p);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: rim, clipPath: blobPolygon(cx, cy, r * 1.06 + 14, seed + 1, t), opacity: 0.92 }} />
      <AbsoluteFill style={{ clipPath: blobPolygon(cx, cy, r, seed, t) }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// Simple dissolve (optionally through an over-exposed flash), for the gentler moments.
export const Dissolve: React.FC<{ start: number; dur?: number; children: React.ReactNode }> = ({ start, dur = 0.6, children }) => {
  const t = useT();
  if (t < start) return null;
  return <AbsoluteFill style={{ opacity: ease.sine(prog(t, start, start + dur)) }}>{children}</AbsoluteFill>;
};

// SVG displacement filter used for water ripples. Apply with style={{filter:'url(#id)'}}.
export const RippleFilter: React.FC<{ id: string; scale: number; freq?: number; seed?: number }> = ({ id, scale, freq = 0.008, seed = 3 }) => {
  const t = useT();
  return (
    <svg width={0} height={0} style={{ position: 'absolute' }}>
      <filter id={id} x="-5%" y="-5%" width="110%" height="110%">
        <feTurbulence
          type="fractalNoise"
          baseFrequency={`${freq * 0.6} ${freq + Math.sin(t * 2) * freq * 0.15}`}
          numOctaves={2}
          seed={seed}
        />
        <feDisplacementMap in="SourceGraphic" scale={scale} xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </svg>
  );
};

export { clamp, lerp, ease, prog, hash, drift };
