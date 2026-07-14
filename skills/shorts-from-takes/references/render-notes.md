# Render notes — spec schema, hard rules, gotchas

Read this before editing `scripts/build.py` or hand-writing a spec. Most of these are
correctness rules where deviation fails *silently* (looks fine in the log, broken in the file).

## Spec schema

Required:
- `segments`: ordered array. Each needs `{ "src": abs path, "start": sec, "end": sec }`,
  plus optional `"kind"`, `"grade"`, `"fit"`, `"beat"`, `"crop"`, `"bg_crop"`, `"transcript"`,
  `"speed"`, `"denoise"`, and `"audio_gain_db"`.
  - `kind` (optional): `"portrait"`/`"vertical"` or `"landscape"`/`"wide"` (legacy `"face"`/
    `"laptop"` still accepted). OMIT to auto-detect orientation from the source (rotation-aware).
  - `fit` (landscape): `"blur"` (default — sharp clip over its own blurred fill, keeps every
    pixel) or `"cover"` (scale-to-fill + center-crop; no bars, edges lost). Portrait uses cover.
  - `grade` (optional): `true` applies the house relight; a filter string applies your own;
    default none (native colour). Opt in on faces/skin, not on screen/UI or graded footage.
  - `speed` (optional): per-segment playback rate, pitch preserved. Overrides global `speed`.
    Use restrained differences to compress setup without rushing proof or emotion.
  - `denoise` (optional): per-segment audio filter override; `""` disables it for music or a
    source that is already processed.
  - `audio_gain_db` (optional): pre-normalization gain for matching uneven speakers/takes.
    Loudnorm controls final programme level; this controls balance *between* segments.
  - `speaker`, `beat`, and other paper-edit metadata are allowed and ignored by the renderer.
    Keep them in the spec when they make review and continuity auditing clearer.
- `blocks`: array of index arrays grouping consecutive segments, e.g. `[[0,1],[2,3],[4],[5]]`.
  Segments inside a block are hard-cut (lossless concat); a crossfade fires BETWEEN blocks.
  Group same-orientation / same-clip runs together; put each orientation flip (and each
  different take/shot you want to dissolve) on a block boundary.
- Every segment index must appear in `blocks` exactly once. The renderer now fails before ffmpeg
  on duplicates, omissions, invalid indices, empty blocks, non-positive trims, or invalid speeds.

Common overrides (else house-style defaults in `build.py`):
- `version` (output suffix), `title`, `subs_start` (0.0 = caption from first word;
  3.0 = leave the open to the title), `name_fix` (`{"CLAWED":"CLAUDE"}` — UPPERCASE keys),
  `speed` (default 1.0 = native pacing; 1.2 tightens talking-head), `grade_filter` (the relight
  recipe `grade: true` uses), `blur_sigma` (landscape blur strength), `denoise` ("" disables),
  `xfade`, `output_dir`, `transcripts_dir`, `captions` (font/fontsize/marginv/colours/pop/max_words),
  `video_use_helpers`.

### Per-join transitions

`xfade` + `xfade_type` remain the global defaults, and legacy `xfade_types` still works. Prefer
`transitions` when joins need different timing:

```json
"transitions": [
  { "type": "fade", "duration": 0.12 },
  { "type": "wipeleft", "duration": 0.20 }
]
```

Entries map to block joins in order. Missing entries fall back to legacy/global settings. The
same duration drives video `xfade`, audio `acrossfade`, total-duration math, segment offsets, and
caption timing. Keep a join shorter than both adjacent timeline sides.

### Automated signal checks

`--check` runs black/freeze detection after duration and loudness checks. Defaults are recursively
merged, so override only what changes:

```json
"quality_checks": {
  "black_frames": {
    "enabled": true,
    "min_duration": 0.30,
    "pixel_threshold": 0.02,
    "severity": "error",
    "allow_ranges": []
  },
  "freeze_frames": {
    "enabled": true,
    "min_duration": 1.50,
    "noise_db": -50,
    "severity": "warning",
    "allow_ranges": [[12.0, 14.0]]
  }
}
```

Use `severity: "error"` for live-action finals when any frozen hold is unintended. Keep the broad
default at `warning` because screen recordings and still-led montages can contain legitimate holds.
Do not ignore warnings: add restrained motion, shorten the hold, disable the relevant check, or
allow-list a reviewed range. Black frames fail by default because black tails commonly indicate a
bad timeline or transition.

## Hard rules (silent-failure territory)

1. **Captions applied LAST** in the filter chain, after the title overlay. Otherwise the
   title (or any overlay) can hide them. `build.py` does `...overlay...[v1];[v1]ass=...[outv]`.
2. **`-ss` and `-t` go BEFORE `-i`** in the per-segment extract. They bound the SOURCE
   range so `setpts=PTS/speed` can compress the clip to `dur/speed`. Put `-t` AFTER `-i`
   and it caps OUTPUT length instead → the speed-up silently does nothing (clip stays full
   length, content window shifts). This bit us once; the symptom is "total duration unchanged."
3. **ASS `[Events]` Format line MUST include `MarginV`** (10 fields:
   Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text). Omit it and the extra
   comma in each Dialogue line bleeds into the Text field → every caption renders with a
   leading comma. Pure-text inspection won't show it; you only see it on a rendered frame.
4. **Per-segment extract → lossless `-c copy` concat for blocks**, then ONE final encode
   for xfade+title+captions. Don't single-pass the whole thing from sources — you lose the
   clean block boundaries and re-encode more than once.
5. **≤30ms audio fades at every segment edge** (`afade` in/out, d=0.03, auto-shrunk toward
   half-length for sub-60ms clips so the in/out fades never overlap). Prevents pops at the
   hard cuts inside a block. Block joins use `acrossfade` (the xfade handles the seam).
6. **A/V sync at block joins: the video `xfade` and the audio `acrossfade` MUST share the
   same per-join duration.** Both shorten the total by that duration, so they stay locked only if
   equal. `build.py` owns the offset accumulator (`acc` in `main()`) — don't recompute it by
   hand; a manual offset desyncs audio from video after the first join.
7. **Caption times account for BOTH per-segment speed and transition overlap.** `build.py` computes each cue's
   output time from the transcript; don't hand-edit timings — any manual offset drifts the
   moment a segment speed or block boundary changes.
8. **Never cut inside a word.** Snap to word boundaries from the transcript; pad
   30–200ms. Prefer silences ≥400ms as cut targets. (No transcript = no captions for that
   clip; the video still renders — fine for montages / no-speech footage.)

## Orientation handling
- Orientation is auto-detected from the source (rotation-aware) unless `kind` is set. If
  auto-detect looks wrong on rotated phone footage, set `kind` explicitly.
- **Cover** (portrait default; landscape `fit:"cover"`): `scale=W:H:force_original_aspect_
  ratio=increase,crop=W:H` → fills the frame for ANY source aspect ratio, center-cropping the
  overflow. No bars.
- **Blur-fill** (landscape default): `split` → background scaled to COVER + cropped + `gblur`,
  foreground scaled to width, overlaid centered. Keeps every pixel (nothing cropped) — best for
  wide content whose edges matter (screen recordings, text). `crop` reframes the sharp
  foreground only; the blurred backdrop stays full-frame (use `bg_crop` to change that).

## Grade (opt-in per segment)
- Off by default — clips render at native colour. Set `"grade": true` on a segment for the
  house relight, or `"grade": "<ffmpeg filter>"` for a custom look. Applies to whichever clips
  you pick (portrait or landscape); leave screen/UI and already-graded footage ungraded.
- House `grade_filter`: `colortemperature=temperature=5200:pl=1` (warmer) +
  `curves=master='0/0.05 0.25/0.30 0.75/0.71 1/0.93'` (lift shadows so they aren't harsh,
  pull highlights so direct light isn't blown) + slight saturation. Tune `temperature`
  lower = warmer, and the curve endpoints for more/less shadow lift. Test the grade on a
  real face frame before committing — skin tone is unforgiving and the numbers lie until
  you see a face.

## Audio
- Source from good phones is often near-silent in gaps (−90 dBFS+). Keep denoise gentle —
  the `build.py` default is `highpass=f=70,afftdn=nr=8:nf=-50` (the `nf` sets the noise
  floor). Aggressive denoise/arnndn makes the voice watery for no gain; if you tighten it,
  listen to the speech before/after (a manual check — the script doesn't measure RMS).
- Then loudnorm to −14 LUFS / −1 dBTP, two-pass (measure, then correct): video-use's helper
  if present, else the built-in in `build.py`. Two-pass lands ON target and holds true-peak
  under −1 dBTP, which single-pass can miss on a late loud transient (some players clip).
- Use per-segment `audio_gain_db` to match noticeably uneven takes before loudnorm. Judge with
  speech, not silence; avoid aggressive boosts that raise room noise. Use per-segment `denoise: ""`
  for music or sources already mastered.
- Sources without an audio stream are accepted. The extractor synthesizes stereo silence for the
  trimmed output duration so silent b-roll, motion graphics, and generated end cards can participate
  in concat and acrossfade without breaking the audio graph.
- Every extracted segment is conformed to 48 kHz stereo before joining. This prevents mono/stereo
  source changes from altering channel layout or destabilizing audio transitions mid-video.

## Self-eval recipe (use video-use's timeline_view on the OUTPUT, not the sources)
Run `python scripts/build.py <spec.json> --check` first — it asserts output duration and
−14 LUFS loudness (±1 LU; true-peak ≤ −0.5 dBTP, small slack over the −1 target), scans for
black/frozen frames, and reports caption cues. Then inspect the rendered output, not just the
spec: at every cut ±1.5s check logic, visual continuity, and audio-pop spikes; sample the title,
first/last 2s, mids, and any end-card transition; verify captions are readable in the safe zone,
grade is consistent, both interview speakers are represented as intended, names are corrected,
and the ending resolves the paper-edit promise. Cap 3 fix loops.
