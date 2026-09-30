#!/usr/bin/env python3
"""Sample frames from face clips, drop blurry ones, write a NUMBERED contact sheet to pick a smile from.
Usage: smile_sheet.py out_dir clip1.MOV [clip2 ...] [--step 0.5] [--start 0 --end 30] [--max 24]
Outputs: out_dir/s_XX.png (full-res frames) + out_dir/smiles_sheet.png. Then ask the user which # to use.
Sharpness = variance of a Laplacian (numpy). No face model needed: the user picks the smile."""
import argparse, subprocess, pathlib, numpy as np
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("clips", nargs="+")
ap.add_argument("--step", type=float, default=0.5); ap.add_argument("--start", type=float, default=0)
ap.add_argument("--end", type=float); ap.add_argument("--max", type=int, default=24); a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True); cand = []
def sharp(im):
    g = np.asarray(im.convert("L").resize((360, 640)), dtype=np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())
for c in a.clips:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", c], capture_output=True, text=True).stdout)
    t = a.start
    while t < (a.end or dur) - 0.1:
        p = out / f"_{pathlib.Path(c).stem}_{t:06.2f}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", c, "-frames:v", "1", str(p)], check=True)  # applies rotation
        cand.append((sharp(Image.open(p)), p, c, t)); t += a.step
cand.sort(key=lambda x: -x[0]); keep = sorted(cand[: a.max], key=lambda x: (x[2], x[3]))
tiles = []
for i, (s, p, c, t) in enumerate(keep, 1):
    dst = out / f"s_{i:02d}.png"; p.replace(dst)
    im = Image.open(dst).convert("RGB"); im.thumbnail((270, 480)); ImageDraw.Draw(im).text((8, 8), f"#{i}  {pathlib.Path(c).stem} @{t:.1f}s", fill=(255, 80, 80)); tiles.append(im)
for _, p, *_ in cand:
    if p.exists(): p.unlink()
cols = 6; rows = -(-len(tiles) // cols); w, h = tiles[0].size
sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
for i, im in enumerate(tiles): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out / "smiles_sheet.png"); print(out / "smiles_sheet.png", len(tiles), "candidates")
