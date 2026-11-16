// Every scene of "I Am an Ocean". Times are absolute seconds in the song.
import React from 'react';
import { AbsoluteFill, Img } from 'remotion';
import { ART, MOCKBOX, WALL } from './art';
import { Caustics, Gobo, Paper } from './fx';
import {
  Backdrop, Cam, Dissolve, Glow, Handwriting, INK, InkReveal, PAPER, RippleFilter, Sheet, TornWipe,
  artSrc, aspect, clamp, drift, ease, hash, lerp, prog, useT,
} from './parts';
import { BAR, blobPolygon, kick, kf } from './lib';

export const Show: React.FC<{ from: number; to: number; children: React.ReactNode }> = ({ from, to, children }) => {
  const t = useT();
  return t >= from && t < to ? <>{children}</> : null;
};

// world point of a fraction (fx, fy) of an un-rotated sheet
const pt = (name: string, cx: number, cy: number, h: number, fx: number, fy: number) => {
  const w = h * aspect(name);
  return { x: cx + (fx - 0.5) * w, y: cy + (fy - 0.5) * h };
};

// ================================================================ ACT I: THE BOX
// A mockup photo shown full height, with its own blurred enlargement filling the sides.
const MockWorld: React.FC<{ name: 'moka' | 'nook' | 'arch' }> = ({ name }) => {
  const [, w, h] = ART['mock_' + name];
  const k = 1080 / h;
  const W = w * k;
  return (
    <div style={{ position: 'absolute', left: 960 - W / 2, top: 0, width: W, height: 1080 }}>
      <Img
        src={artSrc('mock_' + name)}
        style={{
          width: '100%',
          height: '100%',
          WebkitMaskImage: 'linear-gradient(90deg, transparent 0%, #000 7%, #000 93%, transparent 100%)',
          maskImage: 'linear-gradient(90deg, transparent 0%, #000 7%, #000 93%, transparent 100%)',
        }}
      />
    </div>
  );
};
export const mockPaint = (name: 'moka' | 'nook') => {
  const [, w, h] = ART['mock_' + name];
  const k = 1080 / h;
  const left = 960 - (w * k) / 2;
  const b = MOCKBOX[name];
  return { x: left + ((b[0] + b[2]) / 2) * k, y: ((b[1] + b[3]) / 2) * k, w: (b[2] - b[0]) * k, h: (b[3] - b[1]) * k };
};
const MockBackdrop: React.FC<{ name: string }> = ({ name }) => (
  <AbsoluteFill style={{ overflow: 'hidden', background: WALL[name] }}>
    <Img
      src={artSrc('mock_' + name)}
      style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.25)', filter: 'blur(38px) brightness(0.93)', opacity: 0.35 }}
    />
  </AbsoluteFill>
);

export const Opening: React.FC = () => {
  const t = useT();
  return (
    <AbsoluteFill>
      <Paper />
      <AbsoluteFill style={{ background: '#000', opacity: kf(t, [[0, 1], [1.2, 0]]) }} />
    </AbsoluteFill>
  );
};

export const Moka: React.FC = () => {
  const t = useT();
  const p = mockPaint('moka');
  const s = kf(t, [[1.8, 1.0], [9.4, 1.3]], ease.sine);
  const x = kf(t, [[1.8, 960], [9.4, p.x]]);
  const y = kf(t, [[1.8, 540], [9.4, p.y + 20]]);
  return (
    <Dissolve start={1.8} dur={1.3}>
      <MockBackdrop name="moka" />
      <Cam x={x} y={y} s={s} hand={3} seed={11}>
        <MockWorld name="moka" />
      </Cam>
      <Gobo opacity={0.07} seed={2} />
    </Dissolve>
  );
};

// A gallery wall of neat frames, the "box". Optionally the frames break apart.
type Hung = { name: string; x: number; y: number };
const Frame: React.FC<{ it: Hung; i: number; breakAt?: number; box?: number }> = ({ it, i, breakAt, box = 250 }) => {
  const t = useT();
  const a = aspect(it.name);
  const big = it.name === 'arch' ? 1.2 : 1;
  const aw = (a >= 1 ? box : box * a) * big;
  const ah = (a >= 1 ? box / a : box) * big;
  const mat = 34;
  const fr = 13;
  const W = aw + 2 * (mat + fr);
  const H = ah + 2 * (mat + fr);
  const dt = breakAt === undefined ? 0 : Math.max(0, t - (breakAt + i * 0.07));
  const g = 2600;
  const bar = (key: string, st: React.CSSProperties, vx: number, vy: number, w: number) => (
    <div
      key={key}
      style={{
        position: 'absolute',
        background: 'linear-gradient(135deg,#2a2420,#14110f)',
        boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.06)',
        transform: dt > 0 ? `translate(${vx * dt}px, ${vy * dt + 0.5 * g * dt * dt}px) rotate(${w * dt}deg)` : undefined,
        ...st,
      }}
    />
  );
  const out = { x: it.x - 960, y: it.y - 540 };
  const n = Math.hypot(out.x, out.y) || 1;
  const fly = ease.in(clamp(dt / 1.1));
  return (
    <div style={{ position: 'absolute', left: it.x - W / 2, top: it.y - H / 2, width: W, height: H }}>
      {/* mat */}
      <div
        style={{
          position: 'absolute',
          inset: fr,
          background: '#f3ede2',
          boxShadow: 'inset 2px 3px 6px rgba(0,0,0,0.25)',
          opacity: 1 - prog(dt, 0, 0.3),
          filter: 'drop-shadow(0 18px 22px rgba(30,15,5,0.35))',
        }}
      />
      {/* artwork */}
      <div
        style={{
          position: 'absolute',
          left: fr + mat,
          top: fr + mat,
          width: aw,
          height: ah,
          boxShadow: '0 1px 3px rgba(0,0,0,0.35)',
          transform:
            dt > 0
              ? `translate(${(out.x / n) * fly * 1300}px, ${(out.y / n) * fly * 900 - 60 * ease.out(clamp(dt / 0.4))}px) rotate(${(hash(i) - 0.5) * 30 * fly}deg) scale(${1 + ease.out(clamp(dt / 0.5)) * 0.9 + fly * 1.2})`
              : undefined,
        }}
      >
        <Img src={artSrc(it.name)} style={{ width: '100%', height: '100%' }} />
      </div>
      {bar('t', { left: 0, top: 0, width: W, height: fr }, (hash(i + 1) - 0.5) * 300, -700, (hash(i + 2) - 0.5) * 200)}
      {bar('b', { left: 0, top: H - fr, width: W, height: fr }, (hash(i + 3) - 0.5) * 300, 200, (hash(i + 4) - 0.5) * 200)}
      {bar('l', { left: 0, top: 0, width: fr, height: H }, -500, -200, (hash(i + 5) - 0.5) * 250)}
      {bar('r', { left: W - fr, top: 0, width: fr, height: H }, 500, -200, (hash(i + 6) - 0.5) * 250)}
    </div>
  );
};

const GRID = [
  [560, 320], [960, 320], [1360, 320],
  [560, 765], [960, 765], [1360, 765],
];
const Wall: React.FC = () => (
  <AbsoluteFill>
    <Paper tint="#d9c7a8" />
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 35%, rgba(255,240,215,0.35), rgba(0,0,0,0) 70%)' }} />
  </AbsoluteFill>
);

export const GalleryOne: React.FC = () => {
  const t = useT();
  const names = ['sk_camera_polaroid', 'sk_car_awning', 'cat', 'sk_portrait_bob', 'arch', 'sk_flowers_vase'];
  const items: Hung[] = names.map((name, i) => ({ name, x: GRID[i][0], y: GRID[i][1] }));
  // pan the tidy wall, then push through the mat into the ink drawing and travel up the building
  const s = kf(t, [[9.2, 1.04], [13.3, 1.1], [15.3, 5.6], [17.9, 6.4]], ease.inOut);
  const x = kf(t, [[9.2, 880], [13.3, 1010], [15.3, 960], [17.9, 935]], ease.inOut);
  const y = kf(t, [[9.2, 545], [13.3, 535], [15.3, 772], [17.9, 742]], ease.inOut);
  return (
    <AbsoluteFill>
      <Cam x={x} y={y} s={s} hand={2.5} seed={21}>
        <Wall />
        {items.map((it, i) => {
          const appear = ease.out(prog(t, 9.2 + i * 0.09, 9.2 + i * 0.09 + 0.35));
          return (
            <div key={it.name} style={{ opacity: appear, transform: `translateY(${(1 - appear) * -14}px)` }}>
              <Frame it={it} i={i} />
            </div>
          );
        })}
      </Cam>
      <Gobo opacity={0.17 * (1 - prog(t, 13.8, 15))} seed={4} />
    </AbsoluteFill>
  );
};

// One drop of ink falling into the silence before the drums (15.4 - 17.8 s).
export const InkDrop: React.FC = () => {
  const t = useT();
  const p = prog(t, 15.45, 17.75);
  if (p <= 0) return null;
  const r = 760 * ease.out(p) + 4;
  const r2 = 220 * ease.out(prog(t, 16.1, 17.75));
  return (
    <AbsoluteFill style={{ mixBlendMode: 'multiply', filter: 'blur(2.5px)' }}>
      <AbsoluteFill style={{ background: '#1d1b33', opacity: 0.92, clipPath: blobPolygon(1010, 500, r, 11, t, 0.12 + 0.14 * p) }} />
      <AbsoluteFill style={{ background: '#2a1f3f', opacity: 0.85, clipPath: blobPolygon(1420, 760, r2, 17, t, 0.3) }} />
      <AbsoluteFill style={{ background: '#151427', opacity: 0.8, clipPath: blobPolygon(1010, 500, r * 0.55, 23, t, 0.3) }} />
    </AbsoluteFill>
  );
};

// ================================================================ ACT II: "I PAINT, BUT MY NICHE IS ME"
export const Lantern: React.FC = () => {
  const t = useT();
  const cx = 1340, cy = 540, h = 1000;
  const L = pt('lantern', cx, cy, h, 0.91, 0.28);
  const s = kf(t, [[17.8, 1.5], [21.8, 1.0]], ease.inOut);
  const x = kf(t, [[17.8, L.x - 70], [21.8, 1000]], ease.inOut);
  const y = kf(t, [[17.8, L.y + 40], [21.8, 540]], ease.inOut);
  return (
    <InkReveal start={17.8} dur={0.75} cx={1010} cy={500} seed={5}>
      <Backdrop name="lantern" bright={0.42} />
      <Cam x={x} y={y} s={s} hand={5} seed={31}>
        <Sheet name="lantern" cx={cx} cy={cy} h={h} rot={0.8} seed={8}>
          <Glow x={0.905} y={0.29} r={0.16} color="rgba(255,196,110,0.95)" o={0.3 + 0.35 * kick(t) + 0.1 * drift(t, 3, 3)} />
        </Sheet>
      </Cam>
      <Handwriting
        start={18.15}
        cps={10}
        out={21.7}
        lines={[
          { text: 'I paint,', x: 120, y: 330, size: 150, rot: -3 },
          { text: 'but my niche is me.', x: 150, y: 500, size: 92, rot: -2 },
        ]}
      />
    </InkReveal>
  );
};

export const Portraits: React.FC = () => {
  const t = useT();
  return (
    <>
      <TornWipe start={22.25} dir="r" seed={3}>
        <Paper tint="#e8d6bd" />
        <Cam x={kf(t, [[22.2, 1010], [24.8, 940]])} y={540} s={kf(t, [[22.2, 1.06], [24.8, 1.0]])} hand={4} seed={41}>
          <Sheet name="flowerwoman" cx={920} cy={540} h={900} rot={-2.5} seed={12} />
        </Cam>
        <Gobo opacity={0.12} seed={7} />
      </TornWipe>
      <TornWipe start={24.48} dir="l" seed={9}>
        <Paper tint="#d5d9d6" />
        {/* the sketchbook spread sits further back: it moves at half speed */}
        <Cam x={kf(t, [[24.4, 1040], [26.9, 990]])} y={560} s={1.0} hand={2} seed={42}>
          <Sheet name="sk_portraits_stripes" cx={560} cy={560} h={780} rot={-5} seed={13} shadow={0.28} />
        </Cam>
        <Cam x={kf(t, [[24.4, 1120], [26.9, 1000]])} y={540} s={kf(t, [[24.4, 1.0], [26.9, 1.05]])} hand={4} seed={43}>
          <Sheet name="redhead" cx={1290} cy={540} h={960} rot={2} seed={14} />
        </Cam>
        <Gobo opacity={0.1} seed={8} />
      </TornWipe>
    </>
  );
};

// Seasons: paintings land on a pile, one every half bar.
export const Seasons: React.FC = () => {
  const t = useT();
  const T0 = 26.72;
  const pile = [
    { name: 'tulips', at: T0, rot: -3, dx: -40, dy: 10, h: 880 },
    { name: 'jungle', at: T0 + BAR / 2, rot: 2.6, dx: 35, dy: -8, h: 920 },
    { name: 'knit', at: T0 + BAR, rot: -1.6, dx: -18, dy: 14, h: 860 },
    { name: 'fire', at: T0 + BAR * 1.5, rot: 1.1, dx: 12, dy: 0, h: 900 },
  ];
  return (
    <TornWipe start={T0 - 0.02} dir="u" seed={21}>
      <Paper tint="#ead9bf" />
      <Cam x={960} y={540} s={kf(t, [[T0, 1.0], [31.3, 1.08]])} hand={3 + 6 * kick(t)} seed={51}>
        {pile.map((p, i) => {
          const q = prog(t, p.at, p.at + 0.3);
          if (i > 0 && q <= 0) return null;
          const e = i === 0 ? 1 : ease.outBack(q);
          const fire = p.name === 'fire';
          return (
            <Sheet
              key={p.name}
              name={p.name}
              cx={960 + p.dx}
              cy={540 + p.dy - (1 - e) * 40}
              h={p.h}
              rot={p.rot + (1 - e) * 4}
              scale={lerp(1.14, 1, e)}
              opacity={i === 0 ? 1 : clamp(q * 5)}
              shadow={lerp(0.15, 0.4, e)}
              seed={20 + i}
            >
              {fire ? (
                <Glow x={0.54} y={0.47} r={0.15} color="rgba(255,150,50,0.9)" o={0.28 + 0.22 * Math.abs(drift(t, 9, 7))} />
              ) : null}
            </Sheet>
          );
        })}
      </Cam>
      <Gobo opacity={0.11} seed={9} />
    </TornWipe>
  );
};

export const Walker: React.FC = () => {
  const t = useT();
  const cx = 960, cy = 540, h = 980;
  const moon = pt('walker', cx, cy, h, 0.145, 0.1);
  const s = kf(t, [[31.15, 1.12], [35.5, 1.5]], ease.inOut);
  const x = kf(t, [[31.15, 960], [35.5, moon.x + 120]], ease.inOut);
  const y = kf(t, [[31.15, 610], [35.5, moon.y + 140]], ease.inOut);
  const wax = 0.5 + 0.5 * Math.sin((t - 31.2) * 1.5 - 1.2);
  return (
    <Dissolve start={31.1} dur={0.45}>
      <Backdrop name="walker" bright={0.45} />
      <Cam x={x} y={y} s={s} hand={4} seed={61}>
        <Sheet name="walker" cx={cx} cy={cy} h={h} rot={-0.6} seed={30}>
          <Glow x={0.145} y={0.1} r={0.11} color="rgba(255,175,195,0.95)" o={0.18 + 0.42 * wax} />
        </Sheet>
      </Cam>
    </Dissolve>
  );
};

// ================================================================ ACT III: CHORUS
const Strip: React.FC<{ name: string; x: number; w: number; at: number; fromTop: boolean; pan: number; seed: number; pos?: string }> = ({
  name,
  x,
  w,
  at,
  fromTop,
  pan,
  seed,
  pos = '50% 50%',
}) => {
  const t = useT();
  const q = ease.outQuart(prog(t, at, at + 0.38));
  if (t < at) return null;
  const jag = (s: number) => {
    const p: string[] = [];
    for (let y = -20; y <= 1100; y += 12) p.push(`${(Math.abs((hash(y * 0.37 + s) - 0.5)) * 9 + (Math.sin(y * 0.03 + s) + 1) * 3).toFixed(1)}px ${y}px`);
    return p;
  };
  const L = jag(seed);
  const R = jag(seed + 5).map((s) => {
    const [a, b] = s.split(' ');
    return `${(w - parseFloat(a)).toFixed(1)}px ${b}`;
  }).reverse();
  const off = (fromTop ? -1 : 1) * (1 - q) * 1200;
  const drift_ = pan * (t - at);
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: 0, width: w, height: 1080, transform: `translateY(${off}px)`, filter: 'drop-shadow(0 0 14px rgba(0,0,0,0.5))' }}>
      <div style={{ position: 'absolute', inset: 0, background: PAPER, clipPath: `polygon(${[...L, ...R].join(',')})` }}>
        <div style={{ position: 'absolute', left: 8, right: 8, top: -90, bottom: -90, overflow: 'hidden' }}>
          <Img
            src={artSrc(name)}
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, transform: `translateY(${drift_}px) scale(1.04)` }}
          />
        </div>
      </div>
    </div>
  );
};

export const Collision: React.FC = () => {
  const A = 35.63;
  const B = A + BAR;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: '#211b1d' }} />
      <Paper opacity={0.12} />
      <Strip name="scooter" x={330} w={610} at={A} fromTop pan={-22} seed={1} />
      <Strip name="garlic" x={960} w={610} at={A + 0.279} fromTop={false} pan={24} seed={2} />
      <Strip name="diya" x={1590} w={610} at={A + 0.557} fromTop pan={-20} seed={3} />
      <Strip name="sk_car_front" x={192} w={372} at={B} fromTop={false} pan={30} seed={4} />
      <Strip name="egg" x={576} w={372} at={B + 0.07} fromTop pan={-34} seed={5} />
      <Strip name="scooter" x={960} w={372} at={B + 0.14} fromTop={false} pan={26} seed={6} pos="35% 50%" />
      <Strip name="sk_flowers_mosaic" x={1344} w={372} at={B + 0.21} fromTop pan={-30} seed={7} />
      <Strip name="garlic" x={1728} w={372} at={B + 0.28} fromTop={false} pan={28} seed={8} pos="80% 50%" />
    </AbsoluteFill>
  );
};

export const Sapling: React.FC = () => {
  const t = useT();
  const cx = 1340, cy = 540, h = 1000;
  const s = kf(t, [[40.09, 1.0], [44.6, 1.3]], ease.sine);
  const x = kf(t, [[40.09, 1100], [44.6, 1117]], ease.sine);
  const y = kf(t, [[40.09, 540], [44.6, 360]], ease.sine);
  return (
    <InkReveal start={40.09} dur={0.85} cx={1250} cy={380} maxR={1500} seed={9} rim="#3b1c0b">
      <Backdrop name="sapling" bright={0.45} />
      <Cam x={x} y={y} s={s} hand={4} seed={71}>
        <Sheet name="sapling" cx={cx} cy={cy} h={h} rot={1.2} seed={40}>
          <Glow x={0.5} y={0.32} r={0.3} ring color="rgba(255,185,80,0.85)" o={0.2 + 0.3 * kick(t) + 0.1 * Math.sin(t * 2)} />
          <Glow x={0.5} y={0.3} r={0.12} color="rgba(255,245,200,0.8)" o={0.25 + 0.1 * Math.sin(t * 1.3)} />
        </Sheet>
      </Cam>
      <Handwriting
        start={40.3}
        cps={9}
        out={43.9}
        seed={4}
        lines={[
          { text: 'I was never meant', x: 100, y: 380, size: 88, rot: -2.5 },
          { text: 'to stay the same.', x: 140, y: 500, size: 88, rot: -1.5 },
        ]}
      />
    </InkReveal>
  );
};

export const Latte: React.FC = () => {
  const t = useT();
  const cx = 960, cy = 540, h = 1000;
  const cup = pt('latte', cx, cy, h, 0.64, 0.23);
  const s = kf(t, [[44.55, 1.02], [46.85, 1.42]], ease.inOut);
  const x = kf(t, [[44.55, 960], [46.85, cup.x - 20]], ease.inOut);
  const y = kf(t, [[44.55, 540], [46.85, cup.y + 60]], ease.inOut);
  const ang = 3 * Math.sin((t - 44.55) * 1.3);
  return (
    <TornWipe start={44.53} dir="r" seed={31} dur={0.4}>
      <Backdrop name="latte" bright={0.42} />
      <Cam x={x} y={y} s={s} hand={4} seed={81}>
        <Sheet name="latte" cx={cx} cy={cy} h={h} rot={-1} seed={50}>
          {/* the foam slowly turning: same pixels, clipped to the cup, rotated a few degrees */}
          <div style={{ position: 'absolute', inset: 0, clipPath: 'ellipse(19% 6.4% at 64% 23%)' }}>
            <Img
              src={artSrc('latte')}
              style={{ width: '100%', height: '100%', transformOrigin: '64% 23%', transform: `rotate(${ang}deg)` }}
            />
          </div>
        </Sheet>
      </Cam>
    </TornWipe>
  );
};

export const GalleryBreak: React.FC = () => {
  const t = useT();
  const names = ['lantern', 'mother', 'knit', 'cat', 'sapling', 'flowerwoman'];
  const items: Hung[] = names.map((name, i) => ({ name, x: GRID[i][0], y: GRID[i][1] }));
  return (
    <AbsoluteFill>
      <Cam x={960} y={540} s={kf(t, [[46.78, 1.1], [47.75, 1.02], [49.0, 0.96]])} hand={3 + 10 * kick(t)} seed={91}>
        <Wall />
        {items.map((it, i) => (
          <Frame key={it.name} it={it} i={i} breakAt={47.72} />
        ))}
      </Cam>
      <Gobo opacity={0.15} seed={10} />
    </AbsoluteFill>
  );
};

export const Diya: React.FC = () => {
  const t = useT();
  const cx = 960, cy = 540, h = 960;
  const s = kf(t, [[49.0, 1.0], [53.4, 1.22]], ease.sine);
  const y = kf(t, [[49.0, 540], [53.4, 450]], ease.sine);
  return (
    <AbsoluteFill>
      <Backdrop name="diya" bright={0.4} />
      <Cam x={958} y={y} s={s} hand={2.5} seed={101}>
        <Sheet name="diya" cx={cx} cy={cy} h={h} seed={60}>
          <Glow x={0.48} y={0.33} r={0.17} color="rgba(255,190,80,0.9)" o={0.32 + 0.14 * drift(t, 4, 2.2)} />
        </Sheet>
      </Cam>
    </AbsoluteFill>
  );
};

// The screen floods with the diya's blue: going under.
export const Flood: React.FC = () => {
  const t = useT();
  const wave = (lvl: number, ph: number, amp: number) => {
    const p: string[] = [];
    for (let x = -20; x <= 1960; x += 30) p.push(`${x}px ${(lvl + Math.sin(x * 0.006 + t * 3.2 + ph) * amp + Math.sin(x * 0.017 - t * 2 + ph) * amp * 0.35).toFixed(1)}px`);
    p.push('1960px 1200px', '-20px 1200px');
    return `polygon(${p.join(',')})`;
  };
  const a = lerp(1150, -90, ease.in(prog(t, 52.35, 53.42)));
  const b = lerp(1150, -90, ease.in(prog(t, 52.5, 53.45)));
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: '#3d6cb8', opacity: 0.75, clipPath: wave(a, 0, 26) }} />
      <AbsoluteFill style={{ background: 'linear-gradient(180deg,#1d4489,#0e2552)', clipPath: wave(b, 2, 20) }} />
    </AbsoluteFill>
  );
};

// ================================================================ ACT IV: "I AM AN OCEAN"
const Deep: React.FC = () => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: 'linear-gradient(180deg,#1b4180 0%,#11295a 55%,#0a1838 100%)' }} />
    <Paper opacity={0.16} />
    <Caustics opacity={0.1} />
  </AbsoluteFill>
);

const PANO = [
  { name: 'flowerwoman', x: 380, y: 30, h: 640, rot: -3, z: 0.85 },
  { name: 'sk_portrait_bob', x: 1010, y: -20, h: 700, rot: 2, z: 1.0 },
  { name: 'mother', x: 1650, y: 40, h: 720, rot: -1.5, z: 0.9 },
  { name: 'redhead', x: 2290, y: -10, h: 740, rot: 2.5, z: 1.05 },
  { name: 'sk_portraits_stripes', x: 2930, y: 20, h: 640, rot: -2, z: 0.85 },
];

export const Dive: React.FC = () => {
  const t = useT();
  const D = 1300;
  const camY = (tt: number) =>
    kf(tt, [[53.4, 40], [54.6, 540], [56.4, 560], [57.35, 540 + D], [59.7, 560 + D], [60.65, 540 + 2 * D + 60], [66.35, 560 + 2 * D + 60], [67.4, 540 + 3 * D + 400]], ease.inOut);
  const camX = kf(t, [[59.7, 960], [60.65, 760], [66.4, 2560]], ease.sine);
  const y = camY(t);
  const v = Math.abs(camY(t + 1 / 24) - y) * 24; // px/s
  const rip = Math.min(70, v * 0.035);
  const sDive = kf(t, [[53.4, 1.0], [56.4, 1.08], [57.35, 1.0], [59.7, 1.07], [60.65, 1.0]]);
  return (
    <AbsoluteFill>
      <RippleFilter id="dive" scale={rip} freq={0.006} seed={4} />
      <AbsoluteFill style={{ filter: rip > 0.5 ? 'url(#dive)' : undefined }}>
        <Cam x={t < 60 ? 960 : camX} y={y} s={sDive} hand={5} seed={111}>
          <Sheet name="cat_neon" gif cx={960} cy={540} h={880} rot={-1.5} seed={70} />
          <Sheet name="sk_blue_flowers" cx={960} cy={540 + D} h={900} rot={1.2} seed={71} />
          {PANO.map((p, i) => (
            <Sheet
              key={p.name}
              name={p.name}
              cx={p.x + (camX - 960) * (1 - p.z)}
              cy={540 + 2 * D + 60 + p.y}
              h={p.h}
              rot={p.rot + drift(t, i, 0.3) * 1.5}
              seed={72 + i}
            />
          ))}
        </Cam>
      </AbsoluteFill>
      <Handwriting
        start={60.35}
        cps={8.5}
        out={64.9}
        seed={7}
        glow="rgba(5,15,45,0.8)"
        lines={[{ text: 'I am an ocean', x: 560, y: 70, size: 140, rot: -2 }]}
      />
    </AbsoluteFill>
  );
};

// Pattern and folk pieces rising past at different depths.
const RISE = [
  { name: 'scooter', x: 430, z: 1.15, y0: 1150, rot: -6, spin: 3 },
  { name: 'jungle', x: 240, z: 0.7, y0: 1300, rot: 4, spin: -2 },
  { name: 'garlic', x: 1480, z: 0.9, y0: 1210, rot: 5, spin: -3 },
  { name: 'egg', x: 980, z: 1.25, y0: 1480, rot: -3, spin: 2.5 },
  { name: 'tulips', x: 1720, z: 1.05, y0: 1690, rot: 6, spin: -2 },
  { name: 'sk_clock_collage', x: 640, z: 0.8, y0: 1720, rot: -4, spin: 2 },
  { name: 'fire', x: 1260, z: 1.2, y0: 2020, rot: 3, spin: -3 },
  { name: 'sk_flowers_mosaic', x: 1760, z: 0.72, y0: 1900, rot: -5, spin: 2 },
  { name: 'knit', x: 380, z: 1.0, y0: 2080, rot: 4, spin: -2.5 },
  { name: 'sk_car_awning', x: 1050, z: 0.62, y0: 1780, rot: -2, spin: 1.5 },
  { name: 'sk_car_front', x: 1500, z: 0.9, y0: 2450, rot: 3, spin: -2 },
  { name: 'latte', x: 700, z: 1.1, y0: 2750, rot: -4, spin: 2 },
  { name: 'walker', x: 220, z: 0.75, y0: 2500, rot: 5, spin: -1.5 },
  { name: 'diya', x: 1000, z: 1.2, y0: 3550, rot: -2, spin: 1.5 },
];
export const Rising: React.FC = () => {
  const t = useT();
  const tt = t - 66.4;
  const items = [...RISE].sort((a, b) => a.z - b.z);
  return (
    <AbsoluteFill>
      {items.map((r, i) => {
        const y = r.y0 - 430 * r.z * tt - (r.z > 1 ? 40 * tt * tt * 0.1 : 0);
        if (y < -500 || y > 1500) return null;
        return (
          <Sheet
            key={r.name}
            name={r.name}
            cx={r.x + drift(t, i + 30, 0.4) * 40 * r.z}
            cy={y}
            h={520 * r.z}
            rot={r.rot + r.spin * tt}
            blur={r.z < 0.8 ? (0.85 - r.z) * 9 : 0}
            shadow={0.25 + 0.2 * r.z}
            seed={90 + i}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// Every artwork broken into mosaic tiles (the artist's own mosaic language).
const MOS = ['lantern', 'scooter', 'diya', 'flowerwoman', 'latte', 'jungle', 'mother', 'cat', 'garlic', 'redhead', 'sapling', 'egg', 'tulips', 'knit', 'walker', 'fire', 'sk_blue_flowers', 'nook'];
export const Mosaic: React.FC = () => {
  const t = useT();
  const T0 = 73.45;
  const TS = 150, G = 10, P = TS + G, B = 3 * P - G;
  const cols = 15, rows = 9;
  const ox = 960 - (cols * P) / 2, oy = 540 - (rows * P) / 2;
  const swaps = [T0 + BAR, T0 + 2 * BAR];
  const tiles: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const bx = Math.floor(c / 3), by = Math.floor(r / 3);
      const tx = ox + c * P, ty = oy + r * P;
      const d = Math.hypot(tx + TS / 2 - 960, ty + TS / 2 - 540);
      const tA = T0 + (d / 1100) * 0.75 + hash(r * 31 + c) * 0.12;
      const tOut = 79.35 + (1 - d / 1250) * 0.5 + hash(r * 7 + c * 3) * 0.1;
      const appear = ease.outBack(prog(t, tA, tA + 0.22)) * (1 - ease.in(prog(t, tOut, tOut + 0.3)));
      if (appear <= 0.001) continue;
      // which artwork this block shows, advancing at each swap with a card-flip
      let idx = (bx * 7 + by * 5) % MOS.length;
      let flip = 1;
      for (const sw of swaps) {
        const st = sw + c * 0.025 + r * 0.01;
        const q = prog(t, st, st + 0.28);
        if (q >= 0.5) idx = (idx + 5) % MOS.length;
        if (q > 0 && q < 1) flip = Math.abs(Math.cos(q * Math.PI));
      }
      const name = MOS[idx];
      const a = aspect(name);
      const bw = a >= 1 ? B * a : B;
      const bh = a >= 1 ? B : B / a;
      const offx = (bw - B) / 2 + (c % 3) * P;
      const offy = (bh - B) / 2 + (r % 3) * P;
      const drx = drift(t, r * 13 + c, 0.5) * 3;
      const dry = drift(t, r * 13 + c + 50, 0.5) * 3;
      tiles.push(
        <div
          key={`${r}-${c}`}
          style={{
            position: 'absolute',
            left: tx,
            top: ty,
            width: TS,
            height: TS,
            borderRadius: 6,
            backgroundImage: `url(${artSrc(name)})`,
            backgroundSize: `${bw}px ${bh}px`,
            backgroundPosition: `${-offx}px ${-offy}px`,
            boxShadow: '0 4px 10px rgba(0,0,0,0.35)',
            transform: `translate(${drx}px,${dry}px) rotate(${(hash(r * 3 + c * 11) - 0.5) * 3}deg) scale(${appear * flip}, ${appear})`,
          }}
        />,
      );
    }
  }
  const s = kf(t, [[T0, 1.4], [79.8, 0.93]], ease.sine);
  return (
    <AbsoluteFill>
      <Cam x={960} y={540} s={s} hand={4} seed={121} r={kf(t, [[T0, -2], [79.8, 1]])}>
        <AbsoluteFill style={{ background: 'rgba(240,230,210,0)' }} />
        {tiles}
      </Cam>
    </AbsoluteFill>
  );
};

// ================================================================ ENDING
export const Nook: React.FC = () => {
  const t = useT();
  const p = mockPaint('nook');
  const s0 = 1080 / p.h;
  const s = kf(t, [[79.4, s0 * 1.02], [80.3, s0], [83.8, 1.0], [85.6, 0.98]], ease.inOut);
  const x = kf(t, [[79.4, p.x], [80.3, p.x], [83.8, 960]], ease.inOut);
  const y = kf(t, [[79.4, p.y], [80.3, p.y], [83.8, 540]], ease.inOut);
  return (
    <AbsoluteFill>
      <MockBackdrop name="nook" />
      <Cam x={x} y={y} s={s} hand={2.5} seed={131}>
        <MockWorld name="nook" />
      </Cam>
      <Gobo opacity={0.16 * prog(t, 80.5, 82.5)} seed={12} />
      <Handwriting
        start={81.3}
        cps={14}
        out={85.0}
        seed={9}
        color={INK}
        glow="rgba(255,250,240,0.6)"
        weight={500}
        lines={[
          { text: 'at every depth,', x: 1390, y: 370, size: 84, rot: -3 },
          { text: 'a different me.', x: 1430, y: 470, size: 84, rot: -2 },
        ]}
      />
    </AbsoluteFill>
  );
};

export const EndCard: React.FC = () => {
  const t = useT();
  return (
    <Dissolve start={85.0} dur={0.8}>
      <Paper />
      <Gobo opacity={0.08} seed={13} />
      <Handwriting
        start={85.05}
        cps={20}
        out={99}
        color={INK}
        glow="rgba(255,250,240,0)"
        weight={600}
        seed={12}
        lines={[
          { text: 'I Am an Ocean', x: 560, y: 400, size: 150, rot: -2 },
          { text: '@the_Unrushed.whispers', x: 735, y: 600, size: 54, rot: -1 },
        ]}
      />
      <AbsoluteFill style={{ background: '#000', opacity: kf(t, [[87.25, 0], [87.6, 1]]) }} />
    </Dissolve>
  );
};

export { Deep };
