"""Stabilize a handheld clip and give it a diffused, nostalgic, anamorphic-lens look.

Full 16:9 frame, no letterbox bands. Needs ffmpeg (with libvidstab), numpy and
opencv-python-headless.

    python3 make_anamorphic.py input.mp4 [output.mp4] [--preview SECONDS]
"""
import argparse
import os
import subprocess
import tempfile

import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30


def radial(power):
    """0 at the centre, 1 at the corners."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2)) / np.sqrt(2)
    return r ** power


class Look:
    def __init__(self):
        r = radial(1.0)
        self.falloff = (1 - 0.14 * r ** 2.5)[..., None]   # gentle lens light falloff
        self.edge_soft = np.clip((r - 0.3) / 0.7, 0, 1)[..., None] ** 1.3
        # Tone curve: airy and faded. Brightened mids, milky lifted blacks, creamy highlights.
        xs = np.linspace(0, 1, 256, dtype=np.float32) ** 0.88
        self.lut = np.stack([
            0.095 + xs * 0.880,                     # R: warm
            0.090 + xs * 0.860,                     # G
            0.085 + xs * 0.790,                     # B: faded, cream highlights
        ], -1).astype(np.float32)
        self.streak_tint = np.array([0.35, 0.6, 1.0], np.float32)
        self.rng = np.random.default_rng(7)

    def chroma_aberration(self, img):
        out = img.copy()
        for c, scale in ((0, 1.0018), (2, 0.9982)):
            m = cv2.getRotationMatrix2D((W / 2, H / 2), 0, scale)
            out[..., c] = cv2.warpAffine(img[..., c], m, (W, H), flags=cv2.INTER_LINEAR,
                                         borderMode=cv2.BORDER_REFLECT)
        return out

    def __call__(self, frame):
        img = frame.astype(np.float32) / 255.0

        # Nostalgic grade: muted saturation, then faded print-style curve.
        lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        img = lum[..., None] + 0.72 * (img - lum[..., None])
        idx = np.clip(img * 255, 0, 255).astype(np.uint8)
        img = np.stack([self.lut[idx[..., c], c] for c in range(3)], -1)

        # Diffusion (Pro-Mist): soft bloom over everything plus a warm halation round highlights.
        small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bloom = cv2.resize(cv2.GaussianBlur(small, (0, 0), 9), (W, H))
        img = 1 - (1 - img) * (1 - 0.38 * bloom)
        lum_s = small @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        hi = np.clip((lum_s - 0.62) / 0.38, 0, 1) ** 2
        halo = cv2.resize(cv2.GaussianBlur(hi, (0, 0), 3.5), (W, H))[..., None]
        img = img + 0.28 * halo * np.array([1.0, 0.55, 0.3], np.float32)

        # Anamorphic: long horizontal blue streaks from the brightest highlights.
        hot = np.clip((lum_s - 0.66) / 0.30, 0, 1) ** 2
        streak = cv2.GaussianBlur(hot, (0, 0), sigmaX=90, sigmaY=0.7) * 9
        streak = cv2.resize(streak, (W, H))[..., None] * self.streak_tint
        img = 1 - (1 - np.clip(img, 0, 1)) * (1 - np.clip(streak, 0, 0.6))

        # Anamorphic lens character: colour fringing, horizontally smeared edges, soft falloff.
        img = self.chroma_aberration(img)
        soft = cv2.GaussianBlur(img, (0, 0), sigmaX=5, sigmaY=1.5)
        img = img + (soft - img) * self.edge_soft
        img = img * self.falloff

        # Film grain, clumped a little by generating it at 2/3 resolution.
        g = self.rng.standard_normal((H * 2 // 3, W * 2 // 3)).astype(np.float32)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        img = img + g * 0.024 * (0.6 + 0.4 * (1 - img))

        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", default="output/anamorphic_stabilized.mp4")
    ap.add_argument("--preview", type=float, nargs="*",
                    help="only write stills at these seconds to output/preview/")
    args = ap.parse_args()

    look = Look()
    with tempfile.TemporaryDirectory() as tmp:
        trf = os.path.join(tmp, "transforms.trf")
        # Pass 1: measure the camera shake.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.input, "-vf",
                        f"vidstabdetect=shakiness=8:accuracy=15:stepsize=4:result={trf}",
                        "-f", "null", "-"], check=True)
        # Pass 2: smooth the camera path (~1.5 s window) and zoom just enough to hide the edges.
        stab = ["ffmpeg", "-v", "error", "-i", args.input, "-vf",
                f"vidstabtransform=input={trf}:smoothing=45:optzoom=1:zoomspeed=0.2:"
                f"interpol=bicubic:crop=keep,scale={W}:{H}:flags=lanczos,fps={FPS}",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        src = subprocess.Popen(stab, stdout=subprocess.PIPE)

        if args.preview is not None:
            os.makedirs("output/preview", exist_ok=True)
            want = {round(s * FPS) for s in args.preview}
            enc = None
        else:
            enc = subprocess.Popen(
                ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", args.input,
                 "-map", "0:v", "-map", "1:a?",
                 "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                 "-c:a", "aac", "-b:a", "256k", "-shortest", args.output],
                stdin=subprocess.PIPE)

        n = 0
        while True:
            buf = src.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            if enc is None:
                if n in want:
                    out = look(frame)
                    cv2.imwrite(f"output/preview/anamorphic_{n / FPS:05.2f}s.jpg",
                                cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
            else:
                enc.stdin.write(look(frame).tobytes())
            n += 1
        src.wait()
        if enc is not None:
            enc.stdin.close()
            enc.wait()
            print(f"Wrote {args.output} ({n} frames)")


if __name__ == "__main__":
    main()
