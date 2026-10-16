#!/usr/bin/env python3
"""Lock off a handheld clip like a tripod shot, straighten it, and add a
smooth push-in, all in one warp per frame.

    python3 stabilize.py in.mp4 out.mkv --rotate -5.2 --keystone 23 \
        --zoom 1.08 1.18 --size 1920x1080

Corner features from the first frame are tracked through the whole clip
(Lucas-Kanade). Each frame's similarity transform back to the first frame is
fitted with RANSAC, so things moving on their own (sunlight patches) don't
pull the result. Measuring against the first frame, not the previous one,
means errors don't accumulate into drift.
Needs ffmpeg, numpy and opencv-python-headless.
"""
import argparse
import json
import subprocess

import cv2
import numpy as np


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def read_frames(path, w, h):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    frames = []
    while True:
        buf = p.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        frames.append(np.frombuffer(buf, np.uint8).reshape(h, w, 3))
    p.wait()
    return frames


def track(frames):
    """Return per-frame 3x3 matrices mapping frame k -> frame 0 coordinates."""
    gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    ref = cv2.createCLAHE(3.0, (8, 8)).apply(gray[0])
    pts0 = cv2.goodFeaturesToTrack(ref, maxCorners=800, qualityLevel=0.005,
                                   minDistance=12, blockSize=9)
    lk = dict(winSize=(31, 31), maxLevel=4,
              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
    mats = [np.eye(3)]
    ref_pts, cur_pts, prev = pts0, pts0, gray[0]
    for k in range(1, len(gray)):
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray[k], cur_pts, None, **lk)
        # Forward-backward check drops points that slid along an edge.
        back, st2, _ = cv2.calcOpticalFlowPyrLK(gray[k], prev, nxt, None, **lk)
        ok = (st.ravel() == 1) & (st2.ravel() == 1) & \
             (np.linalg.norm((back - cur_pts).reshape(-1, 2), axis=1) < 0.5)
        ref_pts, cur_pts = ref_pts[ok], nxt[ok]
        m, inl = cv2.estimateAffinePartial2D(cur_pts, ref_pts, method=cv2.RANSAC,
                                             ransacReprojThreshold=1.0, maxIters=5000,
                                             confidence=0.999)
        mats.append(np.vstack([m, [0, 0, 1]]))
        prev = gray[k]
    return mats, len(pts0), len(cur_pts)


def straighten(w, h, rotate_deg, keystone):
    """Source -> straightened source: keystone (pull top corners in), then rotate."""
    src = np.float32([[-keystone, 0], [w + keystone, 0], [0, h], [w, h]])
    dst = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    k = cv2.getPerspectiveTransform(src, dst)
    a = np.radians(rotate_deg)  # negative = anticlockwise on screen
    c, s = np.cos(a), np.sin(a)
    cx, cy = w / 2, h / 2
    r = np.array([[c, -s, cx - c * cx + s * cy], [s, c, cy - s * cx - c * cy], [0, 0, 1]])
    return r @ k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--rotate", type=float, default=0)
    ap.add_argument("--keystone", type=float, default=0)
    ap.add_argument("--zoom", type=float, nargs=2, default=[1.08, 1.18])
    ap.add_argument("--size", default="1920x1080")
    a = ap.parse_args()

    w, h, rate = probe(a.inp)
    ow, oh = map(int, a.size.split("x"))
    frames = read_frames(a.inp, w, h)
    mats, n0, n1 = track(frames)
    shifts = np.array([[m[0, 2], m[1, 2], np.degrees(np.arctan2(m[1, 0], m[0, 0]))] for m in mats])
    print(f"tracked {n1}/{n0} points over {len(frames)} frames; correction "
          f"dx {shifts[:,0].min():.1f}..{shifts[:,0].max():.1f}px "
          f"dy {shifts[:,1].min():.1f}..{shifts[:,1].max():.1f}px "
          f"rot {shifts[:,2].min():.2f}..{shifts[:,2].max():.2f}deg")

    fix = straighten(w, h, a.rotate, a.keystone)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{ow}x{oh}", "-r", rate, "-i", "-", "-c:v", "ffv1",
                            "-pix_fmt", "yuv444p", a.out], stdin=subprocess.PIPE)
    n = len(frames)
    for k, (f, m) in enumerate(zip(frames, mats)):
        t = k / max(n - 1, 1)
        t = t * t * (3 - 2 * t) * 0.35 + t * 0.65  # gentle ease in/out
        z = (a.zoom[0] + (a.zoom[1] - a.zoom[0]) * t) * ow / w
        out = np.array([[z, 0, ow / 2 - z * w / 2], [0, z, oh / 2 - z * h / 2], [0, 0, 1]])
        full = out @ fix @ m
        enc.stdin.write(cv2.warpPerspective(f, full, (ow, oh), flags=cv2.INTER_LANCZOS4,
                                            borderMode=cv2.BORDER_REPLICATE).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    main()
