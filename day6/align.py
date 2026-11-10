#!/usr/bin/env python3
"""Find the sheet of paper in each process photo and warp it flat to a fixed square.

photos/NN.jpg -> aligned/NN.png (S x S). Writes aligned/contact.jpg for checking.
"""
import glob, os, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1600

def order(pts):
    pts = pts.reshape(4, 2).astype(np.float32)
    s = pts.sum(1); d = np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], np.float32)

def find_paper(img):
    h, w = img.shape[:2]
    k = 1000 / max(h, w)
    small = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2]
    # paper (white or painted) is much lighter than the dark clipboard
    _, m = cv2.threshold(cv2.GaussianBlur(v, (7, 7), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cy, cx = small.shape[0] / 2, small.shape[1] / 2
    best = None
    for c in cs:
        a = cv2.contourArea(c)
        if a < 0.08 * small.shape[0] * small.shape[1]:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        # prefer big blobs near the middle that are not touching the top edge (bedsheet)
        score = a - 4 * abs((x + bw / 2) - cx) * bh - (1e5 if y < 3 else 0)
        if best is None or score > best[0]:
            best = (score, c)
    hull = cv2.convexHull(best[1])
    peri = cv2.arcLength(hull, True)
    for eps in np.linspace(0.01, 0.08, 30):
        ap = cv2.approxPolyDP(hull, eps * peri, True)
        if len(ap) == 4:
            break
    else:
        r = cv2.minAreaRect(hull); ap = cv2.boxPoints(r)
    return order(ap) / k

def main():
    out = os.path.join(HERE, "aligned"); os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, "photos", "*.jpg")))
    dst = np.array([[0, 0], [S, 0], [S, S], [0, S]], np.float32)
    thumbs = []
    for f in files:
        img = cv2.imread(f)
        q = find_paper(img)
        M = cv2.getPerspectiveTransform(q, dst)
        warp = cv2.warpPerspective(img, M, (S, S), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        name = os.path.splitext(os.path.basename(f))[0]
        cv2.imwrite(os.path.join(out, name + ".png"), warp)
        t = cv2.resize(warp, (300, 300)); cv2.putText(t, name, (8, 30), 0, 1, (0, 0, 255), 2)
        thumbs.append(t)
        print(name, np.round(q).astype(int).tolist())
    while len(thumbs) % 5: thumbs.append(np.zeros_like(thumbs[0]))
    rows = [np.hstack(thumbs[i:i + 5]) for i in range(0, len(thumbs), 5)]
    cv2.imwrite(os.path.join(out, "contact.jpg"), np.vstack(rows))

if __name__ == "__main__":
    main()
