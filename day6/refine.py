#!/usr/bin/env python3
"""Fine-align aligned/NN.png to each other with SIFT + RANSAC homographies.

Each frame is matched to its already-refined neighbour (walking outward from a
reference frame), so small paper-corner errors don't make the drawing jump.
Writes refined/NN.png and refined/contact.jpg.
"""
import glob, os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REF = 13  # index (0-based) of a mid/late frame with a clean, well-framed photo
sift = cv2.SIFT_create(6000)
bf = cv2.BFMatcher()

def homog(src, dst):
    k = 0.5
    a = cv2.resize(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY), None, fx=k, fy=k)
    b = cv2.resize(cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY), None, fx=k, fy=k)
    ka, da = sift.detectAndCompute(a, None)
    kb, db = sift.detectAndCompute(b, None)
    m = [x for x, y in bf.knnMatch(da, db, k=2) if x.distance < 0.75 * y.distance]
    if len(m) < 30:
        return None, len(m)
    pa = np.float32([ka[x.queryIdx].pt for x in m]) / k
    pb = np.float32([kb[x.trainIdx].pt for x in m]) / k
    H, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 6.0)
    if inl.sum() >= 100:
        return H, int(inl.sum())
    # Few reliable matches (e.g. the frame where every shape got outlined):
    # fall back to a rotation+scale+shift fit at full resolution, which needs far fewer points.
    big = cv2.SIFT_create(20000)
    ka, da = big.detectAndCompute(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY), None)
    kb, db = big.detectAndCompute(cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY), None)
    m = [x for x, y in bf.knnMatch(da, db, k=2) if x.distance < 0.8 * y.distance]
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    A, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=8)
    return np.vstack([A, [0, 0, 1]]), int(inl.sum())

def main():
    files = sorted(glob.glob(os.path.join(HERE, "aligned", "[0-9]*.png")))
    imgs = [cv2.imread(f) for f in files]
    S = imgs[0].shape[0]
    out = [None] * len(imgs)
    out[REF] = imgs[REF]
    order = list(range(REF + 1, len(imgs))) + list(range(REF - 1, -1, -1))
    corners = np.float32([[0, 0], [S, 0], [S, S], [0, S]]).reshape(-1, 1, 2)
    for i in order:
        j = i - 1 if i > REF else i + 1
        H, n = homog(imgs[i], out[j])
        if H is not None:
            moved = np.abs(cv2.perspectiveTransform(corners, H) - corners).max()
        if H is None or n < 20 or moved > 0.25 * S:
            print(f"{i+1:02d}: kept paper alignment (inliers={n})")
            out[i] = imgs[i]
            continue
        print(f"{i+1:02d}: refined vs {j+1:02d}, inliers={n}, max corner shift={moved:.0f}px")
        out[i] = cv2.warpPerspective(imgs[i], H, (S, S), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    od = os.path.join(HERE, "refined"); os.makedirs(od, exist_ok=True)
    thumbs = []
    for f, im in zip(files, out):
        cv2.imwrite(os.path.join(od, os.path.basename(f)), im)
        t = cv2.resize(im, (300, 300))
        cv2.line(t, (150, 0), (150, 300), (0, 0, 255), 1); cv2.line(t, (0, 150), (300, 150), (0, 0, 255), 1)
        thumbs.append(t)
    while len(thumbs) % 5: thumbs.append(np.zeros_like(thumbs[0]))
    cv2.imwrite(os.path.join(od, "contact.jpg"), np.vstack([np.hstack(thumbs[i:i+5]) for i in range(0, len(thumbs), 5)]))

if __name__ == "__main__":
    main()
