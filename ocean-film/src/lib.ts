// Timing, easing, organic noise and keyframes shared by every scene.
export const FPS = 24;
export const DURATION_S = 87.6;
export const f = (s: number) => Math.round(s * FPS);

// Musical grid measured from the track (librosa): 107.67 BPM, drums enter at 17.80 s.
export const BEAT = 60 / 107.666;
export const BAR = BEAT * 4;
export const DROP = 17.8;

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const prog = (t: number, a: number, b: number) => clamp((t - a) / (b - a));

export const ease = {
  linear: (x: number) => x,
  inOut: (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  sine: (x: number) => -(Math.cos(Math.PI * x) - 1) / 2,
  out: (x: number) => 1 - Math.pow(1 - x, 3),
  outQuart: (x: number) => 1 - Math.pow(1 - x, 4),
  in: (x: number) => x * x * x,
  outBack: (x: number) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2),
};

// Deterministic hash + smooth value noise (no Math.random: renders must be repeatable).
export const hash = (n: number) => {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return s - Math.floor(s);
};
export const noise1 = (x: number, seed = 0) => {
  const i = Math.floor(x);
  const fr = x - i;
  const a = hash(i + seed * 101.3);
  const b = hash(i + 1 + seed * 101.3);
  const u = fr * fr * (3 - 2 * fr);
  return a + (b - a) * u; // 0..1
};
// two-octave signed noise, roughly -1..1
export const drift = (t: number, seed = 0, speed = 0.35) =>
  (noise1(t * speed, seed) * 2 - 1) * 0.7 + (noise1(t * speed * 2.7, seed + 9) * 2 - 1) * 0.3;

// Keyframes: [[time, value], ...] with an easing per segment.
export type KF = [number, number][];
export const kf = (t: number, keys: KF, e: (x: number) => number = ease.sine) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, v0] = keys[i];
    const [t1, v1] = keys[i + 1];
    if (t <= t1) return lerp(v0, v1, e(prog(t, t0, t1)));
  }
  return keys[keys.length - 1][1];
};

// Soft pulse on every kick after the drums enter (decays over ~0.3 s).
export const kick = (t: number, from = DROP, to = 999) => {
  if (t < from || t > to) return 0;
  const ph = ((t - DROP) % BEAT + BEAT) % BEAT;
  return Math.exp(-ph * 9);
};

// Organic blob outline (ink spreading on paper) as a CSS polygon.
export const blobPolygon = (cx: number, cy: number, r: number, seed: number, t: number, rough = 0.22, n = 72) => {
  const pts: string[] = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const k =
      1 +
      rough * (noise1(i * 0.18 + t * 0.4, seed) - 0.5) * 2 +
      rough * 0.5 * (noise1(i * 0.9 + t * 0.7, seed + 3) - 0.5) * 2 +
      0.04 * (hash(i + seed * 7) - 0.5);
    pts.push(`${(cx + Math.cos(a) * r * k).toFixed(1)}px ${(cy + Math.sin(a) * r * k).toFixed(1)}px`);
  }
  return `polygon(${pts.join(',')})`;
};

// A torn-paper edge: vertical (x = edge(y)) or horizontal (y = edge(x)) jagged line.
export const tornEdge = (len: number, seed: number, amp = 14, step = 9) => {
  const out: number[] = [];
  for (let p = 0; p <= len + step; p += step) {
    const v =
      (noise1(p * 0.012, seed) - 0.5) * amp * 2.2 +
      (noise1(p * 0.07, seed + 4) - 0.5) * amp * 0.9 +
      (hash(p + seed) - 0.5) * amp * 0.45;
    out.push(v);
  }
  return out;
};
