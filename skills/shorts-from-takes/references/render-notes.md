# Render notes — spec schema, hard rules, gotchas

Read this before editing `scripts/build.py` or hand-writing a spec. Most of these are
correctness rules where deviation fails *silently* (looks fine in the log, broken in the file).

## Spec schema

Required:
- `segments`: ordered array. Each needs `{ "src": abs path, "start": sec, "end": sec }`,
  plus optional `"kind"`, `"grade"`, `"fit"`, `"beat"`, `"crop"`, `"bg_crop"`, `"transcript"`.
  - `kind` (optional): `"portrait"`/`"vertical"` or `"landscape"`/`"wide"` (legacy `"face"`/
    `"laptop"` still accepted). OMIT to auto-detect orientation from the source (rotation-aware).
  - `fit` (landscape): `"blur"` (default — sharp clip over its own blurred fill, keeps every
    pixel) or `"cover"` (scale-to-fill + center-crop; no bars, edges lost). Portrait uses cover.
  - `grade` (optional): `true` applies the house relight; a filter string applies your own;
    default none (native colour). Opt in on faces/skin, not on screen/UI or graded footage.
- `blocks`: array of index arrays grouping consecutive segments, e.g. `[[0,1],[2,3],[4],[5]]`.
  Segments inside a block are hard-cut (lossless concat); a crossfade fires BETWEEN blocks.
  Group same-orientation / same-clip runs together; put each orientation flip (and each
  different take/shot you want to dissolve) on a block boundary.

Common overrides (else house-style defaults in `build.py`):
- `version` (output suffix), `title`, `subs_start` (0.0 = caption from first word;
  3.0 = leave the open to the title), `name_fix` (`{"CLAWED":"CLAUDE"}` — UPPERCASE keys),
  `speed` (default 1.0 = native pacing; 1.2 tightens talking-head), `grade_filter` (the relight
  recipe `grade: true` uses), `blur_sigma` (landscape blur strength), `denoise` ("" disables),
  `xfade`, `output_dir`, `transcripts_dir`, `captions` (font/fontsize/marginv/colours/pop/max_words/
  `highlight` — colour for `highlight_words`), `highlight_words` (words tinted in the karaoke fill),
  `top_titles` (beat labels rendered top-center: `[{"start","end","text","colour"?,"fontsize"?}]`
  in OUTPUT seconds) + `top_title_marginv`, `inserts` (image B-roll overlays
  `[{"file","start","end","x","y"}]`, alpha-faded, drawn under the captions),
  `video_use_helpers`.

Per-segment extras (inside a `segments[]` entry): `marginv`, `crop`, `bg_crop`, `grade`, `fit`,
plus:
- `gain` (dB) — pure volume applied before denoise. Levels a take recorded without the mic
  in hand (typically 15–20 LU under the mic'd takes — both hands on a prop, filming a
  screen) up to its neighbours. Global loudnorm can't fix relative imbalance between
  segments; measure each span (`ffmpeg -af loudnorm=print_format=json`) and set gain to
  the difference. Pure gain leaves voice character untouched.
- `zoom` `[z_start, z_end]` — animated zoom (cover fit only), interpolated linearly over
  the segment: values > 1 magnify, start > end zooms out, equal values hold a fixed punch.
  Sampled from a 4/3-oversized intermediate so zoom ≤ 1.33 never upscales.

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
   same duration.** Both shorten the total by `xfade` per join, so they stay locked only if
   equal. `build.py` owns the offset accumulator (`acc` in `main()`) — don't recompute it by
   hand; a manual offset desyncs audio from video after the first join.
7. **Caption times account for BOTH speed and xfade overlap.** `build.py` computes each cue's
   output time from the transcript; don't hand-edit timings — any manual offset drifts the
   moment `speed` or a block boundary changes.
8. **Never cut inside a word.** Snap to word boundaries from the transcript; pad
   30–200ms. Prefer silences ≥400ms as cut targets. (No transcript = no captions for that
   clip; the video still renders — fine for montages / no-speech footage.)
9. **A block-join crossfade blends AUDIO too — it can eat the last word.** `acrossfade`
   mixes the final `xfade` seconds (0.2s) of the outgoing segment into the incoming one; a
   word landing in that tail gets swallowed or doubled. If a segment ends on a word that
   carries the message (a name, the punchline, the CTA), either leave ≥250ms of clear
   silence after it, or make that join a hard cut (merge the blocks) instead of dissolving.
10. **`fps=` MUST precede `zoompan`.** On VFR / odd-timebase sources (phone footage)
   zoompan otherwise multiplies the output frame count ~15x — the segment silently runs
   many times its length and the final xfade offsets land hundreds of seconds out.
11. **Measured durations, not spec math, for anything hand-timed.** AAC frame rounding
   drifts each encoded segment ~+0.04s, so a 13-segment concat lands ~0.5s past the
   nominal `sum(dur/speed) - joins*xfade`. Caption cues are safe (computed from measured
   seg durations), but `top_titles`, `inserts`, and any SFX overlay you time by hand must
   be placed against `ffprobe` durations of the rendered `clips/seg_*.mp4` files. Same
   reason `--check`'s duration gate can show a ~0.5s gap on many-segment cuts — that
   drift is benign.

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

## Self-eval recipe (use video-use's timeline_view on the OUTPUT, not the sources)
Run `python scripts/build.py <spec.json> --check` first — it asserts output duration and
−14 LUFS loudness (±1 LU; true-peak ≤ −0.5 dBTP, small slack over the −1 target) and reports
the caption-cue count, so a silently skipped loudnorm or a `-ss/-t` duration regression fails
loudly. Then eyeball what a script can't: at each cut ±1.5s look for visual jump/flash and
audio-pop spikes in the waveform; sample the title, first/last 2s, mids; verify captions
visible + safe-zone + readable, grade consistent, captions start when intended, names
corrected. Cap 3 fix loops.

One verification trap worth naming: **whisper mishears sped-up speech.** On a 1.2–1.3x
output, a re-transcription can drop or garble short function words that are perfectly intact
(e.g. "let me walk you through it" coming back as "let me you through it"). Before treating
a missing word as a cut defect, extract that span, slow it back to 1.0x (`atempo`), and
re-transcribe — if it's clean at 1x, the audio is fine. The genuine defect this masks is
hard rule 9 (a crossfade actually eating the word), so check both.
