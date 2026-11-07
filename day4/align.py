#!/usr/bin/env python3
"""Line up the Day 4 progress photos so the painting sits still while it fills in.

Every photo in stages/ is warped onto stage 09 (the last one still taped down)
with SIFT feature matches and a RANSAC homography. The washi-tape border is in
every taped photo, which gives plenty of shared features even when the painting
itself has changed a lot. Photos that don't match the reference well enough are
chained through their neighbour instead.

Writes aligned/NN.jpg (square crop of the board) and needs opencv-python-headless.
"""
import glob
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "stages")
DST = os.path.join(HERE, "aligned")
REF = 8          # index of the reference photo (stage 09)
OUT = 1400       # side of the square output


def features(img, sift):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.createCLAHE(2.0, (8, 8)).apply(g)
    return sift.detectAndCompute(g, None)


def homography(fa, fb):
    (ka, da), (kb, db) = fa, fb
    m = cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2)
    good = [a for a, b in (p for p in m if len(p) == 2) if a.distance < 0.72 * b.distance]
    if len(good) < 12:
        return None, 0
    pa = np.float32([ka[g.queryIdx].pt for g in good])
    pb = np.float32([kb[g.trainIdx].pt for g in good])
    H, mask = cv2.findHomography(pa, pb, cv2.RANSAC, 4.0)
    return H, int(mask.sum()) if mask is not None else 0


def main():
    os.makedirs(DST, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(SRC, "*.jpg")))
    imgs = [cv2.imread(p) for p in paths]
    sift = cv2.SIFT_create(6000)
    feats = [features(im, sift) for im in imgs]
    ref = imgs[REF]
    hs = [None] * len(imgs)
    hs[REF] = np.eye(3)
    # walk outwards from the reference so a weak direct match can chain through a neighbour
    order = sorted(range(len(imgs)), key=lambda i: abs(i - REF))
    for i in order:
        if i == REF:
            continue
        H, inl = homography(feats[i], feats[REF])
        nb = i + 1 if i < REF else i - 1
        Hn, inln = homography(feats[i], feats[nb])
        if Hn is not None and hs[nb] is not None and (H is None or inln > 2.5 * inl):
            H, inl, how = hs[nb] @ Hn, inln, f"via {nb + 1:02d}"
        else:
            how = "direct"
        print(f"stage {i + 1:02d}: {inl} inliers ({how})")
        hs[i] = H

    # square crop centred on the board in reference coordinates
    h, w = ref.shape[:2]
    side = int(min(w, h) * 0.97)
    cx, cy = w / 2, h * 0.505
    x0, y0 = cx - side / 2, cy - side / 2
    S = np.array([[OUT / side, 0, -x0 * OUT / side], [0, OUT / side, -y0 * OUT / side], [0, 0, 1]])
    for i, (im, H) in enumerate(zip(imgs, hs)):
        out = cv2.warpPerspective(im, S @ H, (OUT, OUT), flags=cv2.INTER_LANCZOS4,
                                  borderMode=cv2.BORDER_REPLICATE)
        cv2.imwrite(os.path.join(DST, f"{i + 1:02d}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print("wrote", DST)


if __name__ == "__main__":
    main()
