#!/usr/bin/env python3
"""Pull frames at every cut, first/last 2s, and mid-caption for visual QA.
Usage: frame_check.py final.mp4 timeline.json out_dir   (timeline: {"offs": [...], "total": s})
Writes one contact sheet (sheet.png). Look for: caption over face, title/UI overlap,
clipped logos, frozen frames, wrong caption words."""
import json, subprocess, sys, pathlib
from PIL import Image, ImageDraw
v, tl, out = sys.argv[1], json.load(open(sys.argv[2])), pathlib.Path(sys.argv[3]); out.mkdir(exist_ok=True, parents=True)
ts = sorted({0.2, 1.0, tl["total"] - 0.5, tl["total"] - 1.5, *[o + d for o in tl["offs"][1:] for d in (-0.2, 0.1, 0.5)]})
ts = [t for t in ts if 0 <= t < tl["total"] - 0.05]
ims = []
for t in ts:
    p = out / f"f_{t:05.2f}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", v, "-frames:v", "1", "-vf", "scale=270:-2", str(p)], check=True)
    im = Image.open(p).convert("RGB"); ImageDraw.Draw(im).text((6, 6), f"{t:.2f}s", fill=(255, 80, 80)); ims.append(im)
cols = 8; rows = -(-len(ims) // cols); w, h = ims[0].size
sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out / "sheet.png"); print(out / "sheet.png", len(ims), "frames")
