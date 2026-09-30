#!/usr/bin/env python3
"""Usage: CAM_SRC=video.mp4 python camera.py [shot ...]  (edit SHOTS first)
Virtual camera over the landscape screen recording -> vertical 1080x1920 clips.
Camera keyframes are (t_local, scale, cx, cy) in SOURCE pixels (1920x1080);
scale = output px per source px (0.5625 = fit width, 1.778 = true full screen).
Outside the source frame we show a dark blurred fill."""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

import os
SRC = os.environ.get("CAM_SRC") or sys.argv.pop(1)   # landscape screen recording
OUT = Path(os.environ.get("CAM_OUT", "cam")); OUT.mkdir(exist_ok=True)
W, H, FPS, SW, SH = 1080, 1920, 30, 1920, 1080

# EDIT ME per project: name -> (src_start, src_end, [(t_local, scale, cx, cy), ...])
# Find keyframes by extracting frames (ffmpeg -ss T -frames:v 1) and reading pixel coords.
# Always frame-check: text must not be clipped by the crop.
SHOTS = {
    # "intro": start 0.3s, end 3.5s of the source; camera starts wide, pushes into the centre
    "intro": (0.30, 3.50, [(0.0, 0.90, 960, 300), (1.6, 0.90, 960, 300), (3.2, 1.10, 960, 420)]),
}

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def cam_at(keys, t):
    if t <= keys[0][0]: return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            u = ease((t - a[0]) / (b[0] - a[0]))
            return tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3))
    return keys[-1][1:]

def render(name):
    s0, s1, keys = SHOTS[name]
    n = int(round((s1 - s0) * FPS))
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{s0}", "-t", f"{s1 - s0}", "-i", SRC,
                            "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    tmp = OUT / f"{name}_v.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", str(tmp)],
                           stdin=subprocess.PIPE)
    for i in range(n):
        buf = dec.stdout.read(SW * SH * 3)
        if len(buf) < SW * SH * 3: break
        src = Image.frombuffer("RGB", (SW, SH), buf)
        s, cx, cy = cam_at(keys, i / FPS)
        # blurred dark fill (cover)
        bgs = H / SH
        bg = src.resize((int(SW * bgs), H), Image.BILINEAR)
        bx = (bg.width - W) // 2
        bg = bg.crop((bx, 0, bx + W, H)).filter(ImageFilter.GaussianBlur(36))
        bg = Image.eval(bg, lambda v: int(v * 0.55))
        # sharp layer: scale source by s, place so (cx,cy) lands on frame centre
        fg = src.resize((max(1, int(SW * s)), max(1, int(SH * s))), Image.LANCZOS)
        ox, oy = int(W / 2 - cx * s), int(H / 2 - cy * s)
        # clamp so we never pan past the source edge horizontally when it overflows
        if fg.width >= W: ox = min(0, max(W - fg.width, ox))
        else: ox = (W - fg.width) // 2
        if fg.height >= H: oy = min(0, max(H - fg.height, oy))
        bg.paste(fg, (ox, oy))
        enc.stdin.write(bg.tobytes())
    enc.stdin.close(); enc.wait(); dec.wait()
    out = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ss", f"{s0}", "-t", f"{s1 - s0}",
                    "-i", SRC, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "256k", "-shortest", str(out)], check=True)
    tmp.unlink()
    print("  cam", name, out)

if __name__ == "__main__":
    for nm in (sys.argv[1:] or SHOTS):
        render(nm)
