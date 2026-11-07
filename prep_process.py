#!/usr/bin/env python3
"""One-off prep: straighten and align the 12 painting-progress photos.

Finds the light card on the dark table in each photo, warps it to a square
and writes artworks/process/stage_01.jpg ... stage_12.jpg, so every stage
sits in exactly the same place (needed for the stage-to-stage wipes).
Needs opencv-python-headless (only for this step; make_vox_process.py does not).

Usage: python3 prep_process.py photo1 photo2 ... photo12
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artworks", "process")
SIZE = 1600


def order(pts):
    s, d = pts.sum(1), np.diff(pts, axis=1)[:, 0]
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], np.float32)


def card_corners(rgb):
    h, w = rgb.shape[:2]
    k = 900 / max(h, w)
    small = cv2.resize(rgb, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    v = hsv[..., 2]
    mask = (v > 150).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    for eps in np.linspace(0.01, 0.1, 40):
        approx = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
        if len(approx) == 4:
            break
    else:
        approx = cv2.boxPoints(cv2.minAreaRect(c))
    return order(approx.reshape(-1, 2).astype(np.float32)) / k


def load(p):
    return np.asarray(ImageOps.exif_transpose(Image.open(p)).convert("RGB"))


def match(rgb, ref):
    """Homography taking photo `rgb` onto the already-aligned square `ref` (SIFT + RANSAC)."""
    sift = cv2.SIFT_create(6000)
    k = 1600 / max(rgb.shape[:2])
    small = cv2.resize(rgb, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    g1, g2 = (cv2.cvtColor(a, cv2.COLOR_RGB2GRAY) for a in (small, ref))
    k1, d1 = sift.detectAndCompute(g1, None)
    k2, d2 = sift.detectAndCompute(g2, None)
    pairs = cv2.BFMatcher().knnMatch(d1, d2, k=2)
    good = [m for m, n in pairs if m.distance < 0.75 * n.distance]
    a = np.float32([k1[m.queryIdx].pt for m in good]) / k
    b = np.float32([k2[m.trainIdx].pt for m in good])
    H, inl = cv2.findHomography(a, b, cv2.RANSAC, 6.0)
    return H, int(inl.sum()), len(good)


def main(paths, ref_index=11):
    """Stage `ref_index` is squared up from its card corners; every other stage is matched
    to its already-aligned neighbour (walking outwards), so the artwork itself lines up."""
    os.makedirs(OUT, exist_ok=True)
    n = len(paths)
    dst = np.array([[0, 0], [SIZE, 0], [SIZE, SIZE], [0, SIZE]], np.float32)
    aligned = {}
    rgb = load(paths[ref_index - 1])
    H = cv2.getPerspectiveTransform(card_corners(rgb), dst)
    aligned[ref_index] = cv2.warpPerspective(rgb, H, (SIZE, SIZE), flags=cv2.INTER_LANCZOS4)
    order_ = list(range(ref_index - 1, 0, -1)) + list(range(ref_index + 1, n + 1))
    for i in order_:
        nb = i + 1 if i < ref_index else i - 1
        rgb = load(paths[i - 1])
        H, inl, good = match(rgb, aligned[nb])
        aligned[i] = cv2.warpPerspective(rgb, H, (SIZE, SIZE), flags=cv2.INTER_LANCZOS4,
                                         borderMode=cv2.BORDER_REPLICATE)
        print(f"stage {i}: matched to {nb}, {inl}/{good} inliers")
    for i, im in aligned.items():
        Image.fromarray(im).save(os.path.join(OUT, f"stage_{i:02d}.jpg"), quality=92)


if __name__ == "__main__":
    main(sys.argv[1:])
