#!/usr/bin/env python3
"""Colour-correct the "Painting My Way Back to Myself — Day 1" progress photos
so they match the look of the final scanned painting.

The progress shots were taken under warm indoor light on different tables, so
the paper reads cream/grey and the marker colours look muddy. For each photo:

1. White balance: find the paper (bright, low-saturation pixels) and scale the
   linear RGB channels so the paper becomes the same white as the final image.
2. Tone: remap lightness so the darkest ink and the paper white land where they
   sit in the final image (sets the black point and contrast).
3. Colour: compare chroma hue by hue (reds with reds, greens with greens) against
   the final painting and scale saturation to match, so the hibiscus red, leaf
   greens and tile blues have the same punch at every stage.

Statistics are measured in the centre of each photo, which is always on the
paper, so the table and clipboard don't skew the result. The correction is then
applied to the whole frame.

Usage:  python3 color_correct.py
Reads   day1_self_portrait/raw/NN.*   (17.jpg is the final, used as the reference)
Writes  day1_self_portrait/corrected/NN.jpg        full resolution, original framing
        day1_self_portrait/instagram/NN.jpg        1080x1350 (4:5) carousel slides
        day1_self_portrait/before_after.jpg        contact sheet
"""
import glob
import os

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
DAY = os.path.join(ROOT, "day1_self_portrait")
RAW = os.path.join(DAY, "raw")
REFERENCE = "17"

# ---------------------------------------------------------------- colour maths
_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
_MI = np.linalg.inv(_M).astype(np.float32)
_WHITE = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)


def to_linear(srgb):
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def to_srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def _f(t):
    return np.where(t > 216 / 24389, np.cbrt(t), (24389 / 27 * t + 16) / 116)


def _finv(t):
    return np.where(t ** 3 > 216 / 24389, t ** 3, (116 * t - 16) / (24389 / 27))


def lin_to_lab(lin):
    xyz = lin @ _M.T / _WHITE
    fx, fy, fz = _f(xyz[..., 0]), _f(xyz[..., 1]), _f(xyz[..., 2])
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], -1).astype(np.float32)


def lab_to_lin(lab):
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    xyz = np.stack([_finv(fx), _finv(fy), _finv(fz)], -1) * _WHITE
    return (xyz @ _MI.T).astype(np.float32)


def load(path):
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return np.asarray(img, dtype=np.float32) / 255.0


def centre(a, frac):
    h, w = a.shape[:2]
    dy, dx = int(h * (1 - frac) / 2), int(w * (1 - frac) / 2)
    return a[dy:h - dy, dx:w - dx]


def small(a, n=900):
    step = max(1, max(a.shape[:2]) // n)
    return a[::step, ::step]


# ---------------------------------------------------------------- measurements
HUE_BINS = 12            # 30° wide
CHROMA_MIN = 18.0        # "painted" pixels


def paper_white(srgb):
    """Median linear RGB of the paper: bright, near-neutral pixels."""
    s = small(srgb)
    mx, mn = s.max(-1), s.min(-1)
    neutral = (mx - mn) / np.maximum(mx, 1e-3) < 0.18
    lum = s.mean(-1)
    cand = lum[neutral]
    if cand.size < 500:
        cand_mask = lum > np.percentile(lum, 80)
    else:
        cand_mask = neutral & (lum >= np.percentile(cand, 60))
    # ignore specular glare, unless the paper itself is already pure white
    unclipped = cand_mask & (mx < 0.995)
    if unclipped.sum() >= 500:
        cand_mask = unclipped
    return np.median(to_linear(s[cand_mask]), axis=0)


def hue_chroma(lab):
    c = np.hypot(lab[..., 1], lab[..., 2])
    h = (np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) + 360) % 360
    return c, h


def chroma_profile(lab):
    """Per hue bin: (fraction of pixels, 75th-percentile chroma) for painted pixels."""
    c, h = hue_chroma(lab)
    painted = c > CHROMA_MIN
    bins = (h // (360 / HUE_BINS)).astype(int) % HUE_BINS
    total = c.size
    prof = []
    for b in range(HUE_BINS):
        sel = painted & (bins == b)
        n = int(sel.sum())
        prof.append((n / total, float(np.percentile(c[sel], 75)) if n else 0.0))
    return prof


def measure_reference(path):
    srgb = centre(load(path), 0.82)          # drop the white mount around the scan
    lab = lin_to_lab(to_linear(small(srgb)))
    L = lab[..., 0]
    c, _ = hue_chroma(lab)
    neutral_bright = (c < 6) & (L > 85)
    return {
        "paper_L": float(np.median(L[neutral_bright])) if neutral_bright.any() else 97.0,
        "ink_L": float(np.percentile(L, 0.5)),
        "profile": chroma_profile(lab),
    }


# ---------------------------------------------------------------- correction
def chroma_gains(src_prof, ref_prof):
    gains = np.full(HUE_BINS, np.nan, dtype=np.float32)
    for b, ((fs, cs), (fr, cr)) in enumerate(zip(src_prof, ref_prof)):
        if fs > 0.002 and fr > 0.002 and cs > 0:
            gains[b] = np.clip(cr / cs, 0.9, 1.6)
    known = ~np.isnan(gains)
    fallback = float(np.median(gains[known])) if known.any() else 1.2
    if not known.any():
        return np.full(HUE_BINS, fallback, dtype=np.float32)
    # fill missing bins by circular interpolation between known neighbours
    idx = np.arange(HUE_BINS)
    kx, ky = idx[known], gains[known]
    kx = np.concatenate([kx - HUE_BINS, kx, kx + HUE_BINS])
    ky = np.concatenate([ky, ky, ky])
    filled = np.interp(idx, kx, ky).astype(np.float32)
    # bins far from any measured hue drift toward the global value
    return np.where(known, filled, 0.5 * filled + 0.5 * fallback)


def gain_for_hue(h, gains):
    """Smoothly interpolate per-bin gains at bin centres."""
    width = 360 / HUE_BINS
    pos = h / width - 0.5
    i0 = np.floor(pos).astype(int) % HUE_BINS
    t = pos - np.floor(pos)
    return gains[i0] * (1 - t) + gains[(i0 + 1) % HUE_BINS] * t


def correct(srgb, ref):
    # 1. white balance on the paper
    pw = paper_white(srgb)
    target = to_linear(np.array([1.0, 1.0, 1.0]))
    lin = to_linear(srgb)
    # scale so the paper hits the reference paper lightness, neutral
    ref_Y = _finv(np.array((ref["paper_L"] + 16) / 116))
    gain = (target * ref_Y) / np.maximum(pw, 1e-4)
    lin = (lin * gain.astype(np.float32)).astype(np.float32)

    lab = lin_to_lab(lin)
    stats = lin_to_lab(to_linear(np.clip(small(centre(srgb, 0.5)), 0, 1)) * gain.astype(np.float32))

    # 2. tone: ink -> reference ink, paper stays at reference paper
    src_ink = float(np.percentile(stats[..., 0], 0.5))
    src_paper = ref["paper_L"]
    if src_paper - src_ink > 5:
        L = lab[..., 0]
        scale = (src_paper - ref["ink_L"]) / (src_paper - src_ink)
        lab[..., 0] = np.where(L < src_paper, ref["ink_L"] + (L - src_ink) * scale, L)
        stats[..., 0] = np.where(stats[..., 0] < src_paper,
                                 ref["ink_L"] + (stats[..., 0] - src_ink) * scale, stats[..., 0])
    lab[..., 0] = np.clip(lab[..., 0], 0, 100)

    # 3. colour: hue-matched chroma
    gains = chroma_gains(chroma_profile(stats), ref["profile"])
    c, h = hue_chroma(lab)
    g = gain_for_hue(h, gains)
    # leave near-neutral pixels (paper, ink) alone, ramp in over chroma 4..16
    w = np.clip((c - 4) / 12, 0, 1)
    k = 1 + (g - 1) * w
    lab[..., 1] *= k
    lab[..., 2] *= k

    out = to_srgb(lab_to_lin(lab))
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8), gains


# ---------------------------------------------------------------- outputs
def insta_slide(img, size=(1080, 1350)):
    """Centre-crop to 4:5 and resize for an Instagram carousel slide."""
    return ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))


def contact_sheet(pairs, path, thumb_h=420):
    cols = 4
    cells = []
    for name, before, after in pairs:
        b = before.copy(); b.thumbnail((10_000, thumb_h))
        a = after.copy(); a.thumbnail((10_000, thumb_h))
        cell = Image.new("RGB", (b.width + a.width + 6, thumb_h + 34), "white")
        cell.paste(b, (0, 30)); cell.paste(a, (b.width + 6, 30))
        ImageDraw.Draw(cell).text((4, 8), f"{name}   before | after", fill=(30, 30, 30))
        cells.append(cell)
    cw = max(c.width for c in cells) + 12
    ch = cells[0].height + 12
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, ch * rows), (235, 235, 235))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * cw + 6, (i // cols) * ch + 6))
    sheet.save(path, quality=88)


def main():
    files = sorted(glob.glob(os.path.join(RAW, "*.*")))
    ref_path = next(f for f in files if os.path.splitext(os.path.basename(f))[0] == REFERENCE)
    ref = measure_reference(ref_path)
    print(f"reference: paper L={ref['paper_L']:.1f}  ink L={ref['ink_L']:.1f}")

    out_full = os.path.join(DAY, "corrected")
    out_ig = os.path.join(DAY, "instagram")
    os.makedirs(out_full, exist_ok=True)
    os.makedirs(out_ig, exist_ok=True)

    pairs = []
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        before = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        if name == REFERENCE:
            after = before                      # the final is the target look
        else:
            arr, gains = correct(np.asarray(before, dtype=np.float32) / 255.0, ref)
            after = Image.fromarray(arr)
            print(f"{name}: chroma gains {np.round(gains, 2).tolist()}")
        after.save(os.path.join(out_full, f"{name}.jpg"), quality=93, subsampling=0)
        insta_slide(after).save(os.path.join(out_ig, f"{name}.jpg"), quality=93, subsampling=0)
        pairs.append((name, before, after))

    contact_sheet(pairs, os.path.join(DAY, "before_after.jpg"))
    print("done")


if __name__ == "__main__":
    main()
