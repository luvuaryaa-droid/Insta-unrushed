"""Teal-orange matte film grade, baked into a .cube 3D LUT for ffmpeg's lut3d.

    python3 grade.py output/teal_orange.cube

Look:
  * shadows and skies pushed toward teal, skin / warm colours kept orange
  * greens bent toward olive-yellow and toned down
  * overall saturation -15 %
  * lifted blacks (no pure black), soft contrast, slightly warm highlights
"""

import sys

import numpy as np


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    safe = np.where(d == 0, 1, d)
    h = np.where(mx == r, ((g - b) / safe) % 6, h)
    h = np.where(mx == g, (b - r) / safe + 2, h)
    h = np.where(mx == b, (r - g) / safe + 4, h)
    h = np.where(d == 0, 0, h) * 60.0
    s = np.where(mx == 0, 0, d / np.where(mx == 0, 1, mx))
    return np.stack([h % 360, s, mx], -1)


def hsv_to_rgb(hsv):
    h, s, v = hsv[..., 0] % 360, hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    z = np.zeros_like(h)
    i = (h // 60).astype(int) % 6
    r = np.choose(i, [c, x, z, z, x, c])
    g = np.choose(i, [x, c, c, x, z, z])
    b = np.choose(i, [z, z, x, c, c, x])
    return np.stack([r + m, g + m, b + m], -1)


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def hue_weight(h, centre, width):
    """Smooth 0..1 weight around a hue (degrees), zero beyond +-width."""
    return smooth(1 - np.abs((h - centre + 180) % 360 - 180) / width)


def grade(rgb):
    hsv = rgb_to_hsv(rgb)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    # greens -> olive / yellow, a bit quieter
    wg = hue_weight(h, 115, 60)
    h = h - 35 * wg
    s = s * (1 - 0.30 * wg)
    v = v * (1 - 0.06 * wg)

    # skies / blues -> teal
    wb = hue_weight(h, 215, 50)
    h = h - 22 * wb
    s = s * (1 - 0.08 * wb)

    # oranges / skin: hold them warm and rich so they survive the desaturation
    wo = hue_weight(h, 30, 28)
    h = h - 3 * wo
    s = s * (1 + 0.12 * wo)

    # overall saturation -15 %
    s = np.clip(s * 0.85, 0, 1)
    out = hsv_to_rgb(np.stack([h, s, v], -1))

    # split tone: teal shadows, warm highlights
    lum = out @ np.array([0.2126, 0.7152, 0.0722])
    sh = ((1 - lum) ** 2)[..., None]
    hi = (lum ** 2)[..., None]
    out = out + sh * np.array([-0.045, 0.012, 0.035]) + hi * np.array([0.035, 0.010, -0.030])

    # soft contrast (gentle S) then lift blacks / roll off whites: matte film
    out = np.clip(out, 0, 1)
    out = 0.85 * out + 0.15 * smooth(out)
    out = 0.065 + out * (0.955 - 0.065)
    return np.clip(out, 0, 1)


def write_cube(path, size=33):
    t = np.linspace(0, 1, size)
    # .cube order: red varies fastest
    b, g, r = np.meshgrid(t, t, t, indexing="ij")
    rgb = np.stack([r, g, b], -1).reshape(-1, 3)
    out = grade(rgb)
    with open(path, "w") as f:
        f.write('TITLE "unrushed teal-orange matte"\n')
        f.write(f"LUT_3D_SIZE {size}\n")
        for px in out:
            f.write(f"{px[0]:.6f} {px[1]:.6f} {px[2]:.6f}\n")


if __name__ == "__main__":
    write_cube(sys.argv[1] if len(sys.argv) > 1 else "teal_orange.cube")
