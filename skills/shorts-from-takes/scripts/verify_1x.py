#!/usr/bin/env python3
"""Second-opinion transcript of a finished 1.2x short.

Whisper mishears sped-up speech (short words get swallowed), so: slow the audio back to 1x
(atempo=1/speed), transcribe locally, print. Compare against the intended script.
Usage: verify_1x.py final.mp4 [--speed 1.2] [--model small]"""
import argparse, subprocess, tempfile, pathlib
ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--speed", type=float, default=1.2)
ap.add_argument("--model", default="small"); a = ap.parse_args()
d = pathlib.Path(tempfile.mkdtemp()); wav = d / "slow.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-vn", "-af", f"atempo={1 / a.speed:.5f}",
                "-ar", "16000", "-ac", "1", str(wav)], check=True)
subprocess.run(["whisper", str(wav), "--model", a.model, "--language", "en", "--output_format", "txt",
                "--output_dir", str(d), "--fp16", "False"], check=True, capture_output=True)
print((d / "slow.txt").read_text().strip())
