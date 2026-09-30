#!/usr/bin/env python3
"""Cut-point tools driven by a 10ms RMS envelope.

  snap    <src> <t> [--radius 0.12]   nearest point inside real silence around t
  dropout <src> [--start S --end E]   find mic dropouts (digital silence inside speech)
  levels  <src> <start> <end>         integrated loudness of a span (for per-seg gain)

Why: cutting inside a word or on a low-energy consonant makes short sentences sound
clipped. Word timestamps are approximate (+-50ms); the waveform is the truth.
"""
import argparse, subprocess, sys
import numpy as np

SR = 16000

def load(src, start=None, end=None):
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None: cmd += ["-ss", f"{start}"]
    if end is not None and start is not None: cmd += ["-t", f"{end - start}"]
    cmd += ["-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def envelope(x, win=0.010):
    n = int(SR * win); m = len(x) // n
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(axis=1) + 1e-12)

def db(v): return 20 * np.log10(v + 1e-9)

def snap(src, t, radius=0.12):
    a = max(0.0, t - radius)
    x = load(src, a, t + radius); env = db(envelope(x))
    if len(env) == 0: return t
    floor = np.percentile(env, 10)
    # prefer a run of >=3 quiet frames (30ms); pick the quietest run centre nearest t
    best, bi = None, None
    for i in range(1, len(env) - 1):
        run = env[max(0, i - 1): i + 2].mean()
        score = run + 0.15 * abs(a + i * 0.01 - t) * 100   # small pull toward t
        if best is None or score < best: best, bi = score, i
    return round(a + bi * 0.01 + 0.005, 3)

def dropouts(src, start=None, end=None, thresh_db=-75, min_ms=40):
    x = load(src, start, end); env = db(envelope(x))
    off = start or 0.0
    speech = db(np.convolve(envelope(x), np.ones(30) / 30, "same")) > -45   # ~300ms smoothed
    out, i = [], 0
    while i < len(env):
        if env[i] < thresh_db and speech[i]:
            j = i
            while j < len(env) and env[j] < thresh_db: j += 1
            if (j - i) * 10 >= min_ms: out.append((round(off + i * 0.01, 2), round(off + j * 0.01, 2)))
            i = j
        else: i += 1
    return out

def levels(src, start, end):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{start}", "-t", f"{end - start}", "-i", src,
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    import json
    return json.loads(r[r.rfind("{"): r.rfind("}") + 1])["input_i"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("snap"); a.add_argument("src"); a.add_argument("t", type=float); a.add_argument("--radius", type=float, default=0.12)
    b = sp.add_parser("dropout"); b.add_argument("src"); b.add_argument("--start", type=float); b.add_argument("--end", type=float)
    c = sp.add_parser("levels"); c.add_argument("src"); c.add_argument("start", type=float); c.add_argument("end", type=float)
    r = ap.parse_args()
    if r.cmd == "snap": print(snap(r.src, r.t, r.radius))
    elif r.cmd == "dropout":
        d = dropouts(r.src, r.start, r.end)
        print("no dropouts" if not d else "DROPOUTS (avoid cutting keywords here):\n" + "\n".join(f"  {s}-{e}s" for s, e in d))
    else: print(levels(r.src, r.start, r.end), "LUFS")
