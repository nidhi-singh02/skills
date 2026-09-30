#!/usr/bin/env python3
"""Fetch an OFFICIAL brand logo (SVG) and rasterise to transparent PNG.
Usage: uv run --with resvg-py python logo.py <svg_url_or_file> out.png [--size 512]
Find official SVGs on Wikimedia Commons (Special:FilePath/<name>.svg) or the brand's press kit.
resvg-py ships pure wheels (cairosvg needs a system libcairo). Never redraw a logo by hand."""
import argparse, urllib.request, resvg_py, io
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--size", type=int, default=512); a = ap.parse_args()
svg = (urllib.request.urlopen(urllib.request.Request(a.src, headers={"User-Agent": "Mozilla/5.0"})).read().decode()
       if a.src.startswith("http") else open(a.src).read())
png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=a.size))
Image.open(io.BytesIO(png)).convert("RGBA").save(a.out); print("saved", a.out)
