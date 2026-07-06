---
name: shorts-from-takes
description: >-
  Assemble several raw clips — multiple takes, separate shots, or existing reels — into ONE
  finished, on-brand vertical Short (1080x1920), PLUS ready-to-post YouTube / Instagram /
  TikTok / X metadata. Use this whenever someone hands over a batch of clips and wants them
  stitched into a single short-form video: it selects and orders the best material, fits each
  clip to vertical, burns word-by-word captions, adds a title card, and normalizes audio.
  Works for ANY content — talking-head, screen recordings, b-roll, montage. Trigger on "make a
  short/reel from these clips", "combine/stitch these videos into one short", "cut a vertical
  video from my takes", "edit these into a Short/Reel/TikTok", or any folder of clips to post
  as a Short. Opinionated layer ON TOP OF `video-use` — use video-use for a freeform
  single-video edit; cede to `video-to-articles` for a written post/article and
  `linkedin-carousel` for a slide/PDF carousel.
---

# Shorts From Takes

Combine several raw clips — alternate takes, separate shots, or existing reels — into one
finished vertical Short in a consistent house style, then generate platform-tuned posting
metadata. This skill is a **thin preset over `video-use`**: `video-use` is the engine
(transcription, timeline inspection, loudnorm, ffmpeg know-how); this skill carries the
*recipe* — how to select and order the clips, the look, the caption style, the render script,
and the metadata playbook.

## When this applies
Someone hands you multiple clips — any mix of vertical talking-head, wide screen recordings or
b-roll, phone footage, or already-cut reels — and wants them trimmed and combined into one
posted short-form video (YouTube Shorts / Reels / TikTok / X). The clips might be several takes
of the same lines, or distinct shots to assemble — both work. For a general/freeform edit of a
single video, use `video-use` directly.

## Prerequisites
- **`ffmpeg` + `ffprobe`** on PATH, and **Python 3** with **`pillow`**. Zero-setup run:
  `uv run --with pillow python scripts/build.py <spec.json>` (no venv to manage). Or
  `pip install -r requirements.txt` in any env.
- **Transcription** (word-level timestamps) — captions need one transcript JSON per clip:
  - *Recommended:* the `video-use` skill (engine) — clone
    `https://github.com/browser-use/video-use`, put an `ELEVENLABS_API_KEY` (the free
    tier includes credits) in its `.env`, then run its `transcribe_batch.py` +
    `pack_transcripts.py`. `build.py` auto-detects it; or point via the `VIDEO_USE_HELPERS`
    env var / `video_use_helpers` in the spec.
  - *Bring your own:* any tool that emits word timestamps (WhisperX, faster-whisper,
    Deepgram…) works — just match `references/transcript-schema.md`. No video-use needed.
- **Loudnorm** borrows video-use's helper if present, else a built-in 2-pass runs — so
  rendering never requires video-use; only transcription does (or a BYO transcript).
- Fonts are bundled in `assets/fonts/` (Anton + Montserrat). Nothing to download.

## The house style (defaults — deviate when the material calls for it)
- **Format:** vertical 1080x1920, 30fps, downscaled from source at near-lossless CRF.
- **Structure:** open on the strongest hook, end on the payoff/CTA, keep only what earns its
  place. A talking-head + demo piece might run HOOK → SETUP → SHOW → PROOF → PAYOFF → CTA; a
  montage might just be your best shots in rhythm. The `beat` labels are yours — the arc is
  whatever the material wants.
- **Fit to vertical:** portrait clips fill the frame (center-crop); wide clips default to a
  blurred fill so nothing is lost, or `fit: cover` to crop them full-frame. Orientation is
  auto-detected per clip (or set `kind` explicitly).
- **Speed:** native (1.0). Bump to ~1.2x (pitch preserved) to tighten talking-head takes.
- **Look:** native colour by default. Opt a clip into a warm relight with `grade: true` (lift
  shadows, tame highlights) — good for faces/skin; leave screen/UI and already-graded footage native.
- **Transitions:** hard cuts within a run of same-orientation clips; a quick 0.2s crossfade at
  orientation flips and between two different takes/shots you want to dissolve.
- **Captions (optional):** Hormozi style — Anton, ALL CAPS, thick stroke, word-by-word yellow
  fill, quick pop-in; in the cross-platform safe zone. Clips with no speech (or no transcript)
  simply carry none — montages work fine.
- **Title card:** top, first ~3s, fading out.
- **Audio:** gentle denoise + high-pass, normalized to −14 LUFS (turn denoise off for music-led clips).
- **Output:** versioned files (`final_v1.mp4`, `final_v2.mp4`, …) so iterations compare.

These are starting points, not laws. The *creative* picks — which clip, exact trim points,
how warm, font size — are judgment calls made by looking at the footage.

## Workflow

### 1. Inventory + transcribe (engine = video-use)
- `ffprobe` each clip (orientation, fps, duration). You can set `kind` per clip, or let the
  renderer auto-detect portrait vs landscape.
- If the clips have speech you want captioned, transcribe them (video-use's helpers, or any
  word-timestamp tool → `references/transcript-schema.md`):
  `uv run python <video-use>/helpers/transcribe_batch.py "<folder>" --edit-dir "<folder>/edit"`
  then `pack_transcripts.py --edit-dir "<folder>/edit"`. Cache — never re-transcribe. Skip this
  entirely for no-speech montages.
- Read `takes_packed.md`. Note false starts, look-aways, mis-speaks, and the best of each beat.

### 2. Select + order the clips + confirm the plan (judgment — do NOT skip)
- Choose the best clip/take per beat and order them so they flow. Drill into specific moments
  with `video-use`'s `timeline_view.py` (filmstrip+waveform) to find clean cut points and to
  spot look-aways/awkward pauses to trim.
- For spoken clips, snap cuts to word boundaries and pad edges — the exact rule (and why
  cutting inside a word fails) is `references/render-notes.md` hard rule 8.
- Confirm the plain-English plan (clip order, trims, title, any name corrections) with the
  user before rendering.

### 3. Write the spec + render
- Copy `scripts/spec.example.json`, fill `segments` (`src`/`start`/`end`, optional
  `kind`/`grade`/`fit`/`beat`), `blocks` (group consecutive same-orientation clips; a crossfade
  fires between blocks), `title`, `name_fix`, `version`.
- Preview: `python scripts/build.py <spec.json> --preview`
- Final:   `python scripts/build.py <spec.json>`
- See `references/render-notes.md` for the spec schema, the production-correctness rules,
  and the gotchas that cause silent failures (read it before changing the render).

### 4. Self-eval before showing the user
Render failures here are *silent* — a mis-ordered filter, a hidden caption, or a skipped
loudnorm looks fine in the ffmpeg log and only shows on an actual frame or waveform. So grade
the rendered file, not the plan, before the user ever sees it.
- Run the automated gate first: `python scripts/build.py <spec.json> --check` asserts output
  duration and −14 LUFS loudness against the spec (and reports the caption-cue count).
- Then eyeball what a script can't, per the Self-eval recipe in `references/render-notes.md`
  (frames at each cut, title, first/last 2s; captions readable + in safe zone; grade
  consistent; names corrected). Fix → re-render → re-check, cap 3 passes. Bump `version` each
  iteration so the user can compare.

### 5. Posting metadata (optional — when asked, or offer it)
Write platform-tuned metadata to `<edit>/social_metadata.md` per
`references/social-metadata.md` — YouTube Shorts, Instagram Reels, X native video, and TikTok
(the "when asked" fourth platform), each to that platform's CURRENT algorithm. Research current
trends first (web search); the reference encodes the durable rules but trends move.

## Files
- `scripts/build.py` — the render engine (reads a spec.json; `--preview` and `--check` modes).
  Self-contained: borrows video-use's loudnorm if present, else uses a built-in 2-pass.
- `scripts/spec.example.json` — worked example: several clips assembled into one Short (copy + edit paths).
- `references/render-notes.md` — spec schema + hard rules + gotchas. Read before editing render.
- `references/social-metadata.md` — the 4-platform metadata playbook + paste-ready templates.
- `references/transcript-schema.md` — the transcript JSON captions read (bring your own).
- `requirements.txt` — Python deps (`pillow`); ffmpeg/ffprobe are system tools.
- `assets/fonts/` — Anton (caption/title), Montserrat (fallback); SIL OFL, licenses in `assets/font-licenses/`.

## Staying current with video-use
This skill deliberately does NOT copy video-use's engine — it calls it, so upstream fixes
flow through. Periodically `git -C <video-use> pull` to stay on the latest. If you extend
the render in ways video-use lacks (mixed-orientation canvas, xfade chain, ASS karaoke),
consider upstreaming them as a PR so the engine carries them and this skill shrinks.
