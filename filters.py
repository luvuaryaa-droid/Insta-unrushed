#!/usr/bin/env python3
"""Creator Studio filters: colour looks for reels, ads, carousels and any finished video or image.

Filters (strength 0-1, default 1):
  bw        black and white            sepia     warm brown old-photo tone
  warm      golden, cosy               cool      crisp blue
  contrast  punchy high contrast       matte     faded, lifted blacks
  duotone   cobalt shadows, mustard highlights
  vhs       colour split, scanlines, tracking wobble
  riso      poster / risograph: few colours with print grain
plus any .cube 3D LUT (colour grade) exported from another editor.

The renderers take the same options:
  python3 make_ads.py artists --filter warm
  python3 make_video.py --filter vhs:0.6
  python3 make_flipbook.py --filter cool
  python3 make_carousels.py --filter duotone
  python3 make_ads.py --lut my_grade.cube --filter contrast:0.5   # LUT first, then the filter

Or filter something already rendered (audio, e.g. a voice-over, is kept):
  python3 filters.py IN OUT --filter sepia[:0.8] [--lut grade.cube]   # .mp4/.mov, .jpg/.png, or a folder
  python3 filters.py --list
  python3 filters.py --showreel IN.mp4 OUT.mp4    # every filter in turn on one clip, labelled
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np

COBALT = (47, 79, 160)
MUSTARD_LIGHT = (250, 214, 120)
LUMA = np.array([0.299, 0.587, 0.114], np.float32)

DESCRIPTIONS = {
    "bw": "Black and white",
    "sepia": "Sepia: warm brown old-photo tone",
    "warm": "Warm: golden and cosy",
    "cool": "Cool: crisp and blue",
    "contrast": "High contrast: deeper shadows, brighter highlights, richer colour",
    "matte": "Faded matte: lifted blacks, softer contrast",
    "duotone": "Duotone: cobalt shadows, mustard highlights",
    "vhs": "VHS: colour split, scanlines and a rolling tracking wobble",
    "riso": "Poster / riso: a few flat colours with print grain",
}


# --------------------------------------------------------------------------- the looks
# Each takes and returns float32 RGB in 0..255. `frame` lets animated looks (VHS, riso grain) move.

def luma(a):
    return a @ LUMA


def saturate(a, k):
    y = luma(a)[..., None]
    return y + (a - y) * k


def f_bw(a, frame):
    y = luma(a)
    y = 128 + (y - 128) * 1.08
    return np.repeat(y[..., None], 3, axis=2)


def f_sepia(a, frame):
    y = luma(a)[..., None]
    return y * np.array([0.95, 0.82, 0.62], np.float32) + np.array([18, 10, 0], np.float32)


def f_warm(a, frame):
    return a * np.array([1.08, 1.0, 0.86], np.float32) + np.array([8, 2, -6], np.float32)


def f_cool(a, frame):
    return a * np.array([0.9, 0.98, 1.12], np.float32) + np.array([-4, 0, 10], np.float32)


def f_contrast(a, frame):
    # A fixed S-curve rather than per-frame auto levels, so video doesn't flicker.
    x = np.clip(a / 255.0, 0, 1)
    s = x * x * (3 - 2 * x)
    return saturate((x * 0.35 + s * 0.65) * 255 * 1.03 - 4, 1.18)


def f_matte(a, frame):
    return saturate(a, 0.9) * 0.82 + np.array([34, 32, 30], np.float32)


def f_duotone(a, frame, dark=COBALT, light=MUSTARD_LIGHT):
    y = np.clip(luma(a) / 255.0, 0, 1)[..., None]
    y = y * y * (3 - 2 * y) * 0.6 + y * 0.4
    return np.array(dark, np.float32) * (1 - y) + np.array(light, np.float32) * y


def f_vhs(a, frame):
    h, w = a.shape[:2]
    out = a.copy()
    s = max(2, w // 180)                      # colour split, scaled to the frame
    out[..., 0] = np.roll(a[..., 0], -s, axis=1)
    out[..., 2] = np.roll(a[..., 2], s - 1, axis=1)
    rng = np.random.default_rng(frame)
    band_h = max(8, h // 28)                  # tracking band that rolls down the frame
    y0 = int((frame * h / 70) % h)
    shift = int(rng.integers(3, 9) * w / 1080) + 1
    out[y0:y0 + band_h] = np.roll(out[y0:y0 + band_h], shift, axis=1)
    out[y0:y0 + band_h] += 12
    step = max(3, h // 480)                   # scanlines
    out[::step] *= 0.84
    out = saturate(out, 1.12) + rng.normal(0, 4.0, (h, w, 1)).astype(np.float32)
    return out * 0.96 + 6


def f_riso(a, frame):
    rng = np.random.default_rng(1000 + frame // 2)
    noisy = a + rng.normal(0, 14, a.shape[:2] + (1,)).astype(np.float32)   # print grain dithers the bands
    levels = 4
    q = np.floor(np.clip(noisy, 0, 255) / 256 * levels)
    return q * (255 / (levels - 1))


FILTERS = {"bw": f_bw, "sepia": f_sepia, "warm": f_warm, "cool": f_cool, "contrast": f_contrast,
           "matte": f_matte, "duotone": f_duotone, "vhs": f_vhs, "riso": f_riso}
ALIASES = {"blackwhite": "bw", "black-and-white": "bw", "mono": "bw", "high-contrast": "contrast",
           "faded": "matte", "poster": "riso", "risograph": "riso"}


# --------------------------------------------------------------------------- LUTs

def load_cube(path):
    """Read an Adobe/Resolve .cube 3D LUT. Returns (lut[b, g, r, 3] in 0..1, domain_min, domain_max)."""
    size, dmin, dmax, rows = None, np.zeros(3), np.ones(3), []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or line.upper().startswith("TITLE"):
                continue
            key = line.split()[0].upper()
            if key == "LUT_3D_SIZE":
                size = int(line.split()[1])
            elif key == "LUT_1D_SIZE":
                raise ValueError(f"{path}: 1D LUTs are not supported, export a 3D LUT")
            elif key == "DOMAIN_MIN":
                dmin = np.array([float(v) for v in line.split()[1:4]])
            elif key == "DOMAIN_MAX":
                dmax = np.array([float(v) for v in line.split()[1:4]])
            elif key[0].isdigit() or key[0] in "-.":
                rows.append([float(v) for v in line.split()[:3]])
    if not size or len(rows) != size ** 3:
        raise ValueError(f"{path}: expected LUT_3D_SIZE and {size and size ** 3} rows, found {len(rows)}")
    # .cube lists red fastest, then green, then blue.
    return np.array(rows, np.float32).reshape(size, size, size, 3), dmin, dmax


def apply_lut(a, lut):
    """Trilinear 3D LUT lookup on float RGB 0..255."""
    table, dmin, dmax = lut
    n = table.shape[0]
    x = (np.clip(a / 255.0, 0, 1) - dmin) / (dmax - dmin) * (n - 1)
    x = np.clip(x, 0, n - 1)
    i0 = np.minimum(np.floor(x).astype(np.int32), n - 2)
    f = x - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]
    out = 0
    for db, wb in ((0, 1 - fb), (1, fb)):
        for dg, wg in ((0, 1 - fg), (1, fg)):
            for dr, wr in ((0, 1 - fr), (1, fr)):
                out = out + table[b0 + db, g0 + dg, r0 + dr] * (wr * wg * wb)
    return out * 255.0


# --------------------------------------------------------------------------- a look = optional LUT + optional filter

class Look:
    def __init__(self, name=None, strength=1.0, lut_path=None):
        if name:
            name = ALIASES.get(name.lower(), name.lower())
            if name not in FILTERS:
                raise SystemExit(f"unknown filter '{name}'. Choose from: {', '.join(FILTERS)}")
        self.name = name
        self.strength = float(min(1.0, max(0.0, strength)))
        self.lut_path = lut_path
        self.lut = load_cube(lut_path) if lut_path else None

    def __bool__(self):
        return bool(self.name or self.lut is not None)

    def suffix(self):
        parts = []
        if self.lut_path:
            parts.append(os.path.splitext(os.path.basename(self.lut_path))[0])
        if self.name:
            parts.append(self.name if self.strength >= 1 else f"{self.name}{int(round(self.strength * 100))}")
        return "_" + "_".join(parts) if parts else ""

    def apply(self, rgb, frame=0):
        """rgb: HxWx3 uint8 (or float) array. Returns uint8."""
        a = np.asarray(rgb, np.float32)[..., :3]
        if self.lut is not None:
            a = apply_lut(a, self.lut)
        if self.name:
            f = FILTERS[self.name](a, frame)
            a = f if self.strength >= 1 else a + (f - a) * self.strength
        return np.clip(a, 0, 255).astype(np.uint8)

    def apply_bytes(self, buf, w, h, frame=0, channels=3):
        a = np.frombuffer(buf, np.uint8).reshape(h, w, channels)
        out = self.apply(a[..., :3], frame)
        if channels == 4:
            out = np.dstack([out, a[..., 3]])
        return out.tobytes()


def from_argv(argv=None):
    """Read --filter NAME[:STRENGTH] and --lut FILE from argv, remove them (in place) and return a Look,
    or None when neither is given, so callers' own argument parsing is unaffected."""
    argv = sys.argv if argv is None else argv
    name, strength, lut = None, 1.0, None
    for flag in ("--filter", "--lut"):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv):
                raise SystemExit(f"{flag} needs a value")
            val = argv[i + 1]
            del argv[i:i + 2]
            if flag == "--lut":
                lut = val
            else:
                name, _, s = val.partition(":")
                strength = float(s) if s else 1.0
    look = Look(name, strength, lut)
    return look if look else None


def with_suffix(path, look):
    if not look:
        return path
    base, ext = os.path.splitext(path)
    return base + look.suffix() + ext


# --------------------------------------------------------------------------- processing finished files

VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")

_JOB = {}


def _work(args):
    i, buf = args
    return _JOB["look"].apply_bytes(buf, _JOB["w"], _JOB["h"], frame=i)


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate", "-of", "csv=p=0", path]).decode().split(",")
    num, den = out[2].strip().split("/")
    return int(out[0]), int(out[1]), f"{num}/{den}"


def process_video(src, out, look, label_fn=None):
    """Filter every frame of src into out, copying any audio track unchanged."""
    w, h, rate = probe(src)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-r", rate, "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a",
                            "copy", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    size = w * h * 3

    def frames():
        i = 0
        while True:
            buf = dec.stdout.read(size)
            if len(buf) < size:
                return
            yield i, buf
            i += 1

    _JOB.update(look=look, w=w, h=h)
    with Pool(os.cpu_count()) as pool:
        for buf in pool.imap(label_fn or _work, frames(), chunksize=4):
            enc.stdin.write(buf)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    if enc.returncode:
        raise SystemExit(f"encoding {out} failed")
    print("wrote", out)


def process_image(src, out, look):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    Image.fromarray(look.apply(np.asarray(im))).save(out, quality=92)
    print("wrote", out)


def process(src, out, look):
    if os.path.isdir(src):
        os.makedirs(out, exist_ok=True)
        for f in sorted(os.listdir(src)):
            if f.lower().endswith(IMAGE_EXT + VIDEO_EXT):
                process(os.path.join(src, f), os.path.join(out, f), look)
    elif src.lower().endswith(VIDEO_EXT):
        process_video(src, out, look)
    elif src.lower().endswith(IMAGE_EXT):
        process_image(src, out, look)
    else:
        raise SystemExit(f"don't know how to filter {src}")


# --------------------------------------------------------------------------- showreel

SHOW = ["bw", "sepia", "warm", "cool", "contrast", "matte", "duotone", "vhs", "riso"]
_LABELS = {}


def _label_img(name, w):
    from make_video import caveat, text_strip
    strip = text_strip(DESCRIPTIONS[name].split(":")[0], caveat(int(w * 0.075)), seed=len(name), max_w=int(w * 0.8))
    return np.asarray(strip.convert("RGBA"))


def _show_work(args):
    i, buf = args
    w, h, per = _JOB["w"], _JOB["h"], _JOB["per"]
    name = SHOW[min(len(SHOW) - 1, i // per)]
    a = Look(name).apply(np.frombuffer(buf, np.uint8).reshape(h, w, 3), frame=i)
    lab = _LABELS.get(name)
    if lab is None:
        lab = _LABELS[name] = _label_img(name, w)
    lh, lw = lab.shape[:2]
    x0, y0 = (w - lw) // 2, int(h * 0.86) - lh // 2
    region = a[y0:y0 + lh, x0:x0 + lw].astype(np.float32)
    alpha = lab[..., 3:4] / 255.0
    a = a.copy()
    a[y0:y0 + lh, x0:x0 + lw] = (lab[..., :3] * alpha + region * (1 - alpha)).astype(np.uint8)
    return a.tobytes()


def showreel(src, out, seconds_each=3.0):
    """Cut a clip into equal parts, one filter each, with a label."""
    w, h, rate = probe(src)
    num, den = (int(v) for v in rate.split("/"))
    per = int(round(seconds_each * num / den))
    tmp = out + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", str(seconds_each * len(SHOW)), "-c", "copy", tmp],
                   check=True)
    _JOB.update(per=per)
    process_video(tmp, out, Look(), label_fn=_show_work)
    os.remove(tmp)


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    if argv[0] == "--list":
        for k in FILTERS:
            print(f"  {k:9s} {DESCRIPTIONS[k]}")
        return
    if argv[0] == "--showreel":
        showreel(argv[1], argv[2])
        return
    look = from_argv(argv)
    if not look or len(argv) != 2:
        raise SystemExit("usage: filters.py IN OUT --filter NAME[:STRENGTH] [--lut FILE.cube]   (see --help)")
    process(argv[0], argv[1], look)


if __name__ == "__main__":
    main()
