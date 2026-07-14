# shorts-from-takes

Give it a batch of **raw clips** — multiple takes, separate shots, or existing reels — and it
combines them into one finished **vertical Short** (1080×1920), plus the copy to post it. It
trims, orders, stitches, and burns the look onto **any** footage — talking-head, screen
recordings, b-roll, product, travel, gameplay, vlog:

- **Selects + concatenates** your clips into a single short, in whatever arc the material wants
- **Fits every clip to vertical** — portrait fills the frame; wide clips blur-fill (keep all
  pixels) or `fit: cover` to crop full-frame; orientation auto-detected per clip
- **Hormozi-style captions** (optional) — word-by-word, ALL-CAPS, thick outline, yellow fill,
  pop-in; clips with no speech simply carry none
- **Title card**, optional **speed-up** (pitch preserved) and per-clip **warm relight**,
  gentle denoise, **−14 LUFS** audio
- **Ready-to-post metadata** tuned per platform (YouTube Shorts / Instagram Reels / X)

It's an opinionated **house-style layer on top of** the
[`video-use`](https://github.com/browser-use/video-use) engine — `video-use` does the
heavy lifting (transcription, timeline inspection, ffmpeg know-how); this carries the
*recipe*. The render script is self-contained, so you can also run it standalone.

> This skill is written to be **driven by an AI agent** (Claude Code): it hands the agent a
> recipe, and the agent does the judgment work — watching your clips, picking and ordering the
> best material, and finding clean cut points — with you. The renderer underneath is a plain
> Python script you can also drive by hand.

## See it in action

A finished Short built with this skill — raw takes in, posted vertical out:

▶ **[Watch the Short on YouTube](https://www.youtube.com/shorts/BmN-N9cK1PY)**

## How it works

```
raw clips ──▶ transcribe ──▶ select + order clips ──▶ write spec.json ──▶ build.py ──▶ final_v1.mp4
 (any)       (optional)      (judgment, with you)      (segments+blocks)   (ffmpeg)     + captions
```

`build.py` reads a `spec.json` (which clips, which time ranges, the title, any fixes) and
renders: per-segment fit-to-vertical + optional speed/grade → lossless concat into blocks →
crossfade at orientation flips → title overlay → captions applied last → loudness normalize.

## Prerequisites

- **`ffmpeg` + `ffprobe`** on your PATH — `brew install ffmpeg` (macOS) or
  [ffmpeg.org/download](https://ffmpeg.org/download.html). HDR phone footage needs an
  FFmpeg build with the `zscale` filter; SDR footage renders with a normal build.
- **Python 3 + `pillow`.** Easiest is [`uv`](https://docs.astral.sh/uv/) with no setup:
  `uv run --with pillow python scripts/build.py …`. Or `pip install -r requirements.txt`.
- **Word-level transcripts** — the captions need one transcript JSON per clip. Two paths:
  - **Recommended — `video-use`:** `git clone https://github.com/browser-use/video-use`,
    add an `ELEVENLABS_API_KEY` to its `.env` (ElevenLabs' **free tier includes credits** —
    no paid plan needed), then run its transcribe helpers (below). `build.py` auto-detects
    the clone; or set `VIDEO_USE_HELPERS` / `video_use_helpers` in the spec.
  - **Bring your own:** use WhisperX, faster-whisper, Deepgram — anything with word
    timestamps — and match [`references/transcript-schema.md`](references/transcript-schema.md).
    No `video-use` or ElevenLabs key required.

Rendering (grade, captions, loudnorm) needs **none** of the above beyond ffmpeg + pillow —
only transcription does.

## Quickstart

**1. Put your clips in a folder** — any mix of portrait and wide footage: takes, shots, or reels.

**2. Transcribe** (the `video-use` way; skip if bringing your own transcripts):

```bash
# from your video-use clone, with ELEVENLABS_API_KEY set in .env
uv run python helpers/transcribe_batch.py "/path/to/your-project" \
    --edit-dir "/path/to/your-project/edit"
uv run python helpers/pack_transcripts.py --edit-dir "/path/to/your-project/edit"
```

This writes a transcript JSON per clip into `…/edit/transcripts/` and a readable
`takes_packed.md` for spotting the best material. Skip this step entirely for no-speech montages.

**3. Write a spec.** Copy [`scripts/spec.example.json`](scripts/spec.example.json) and edit
it: point `src` at your clips, set each `start`/`end`; optionally `kind` (portrait/landscape —
omit to auto-detect), `grade: true` for a warm relight, or `fit: cover` to crop a wide clip
full-frame; group `blocks`; set the `title`. Full schema and the correctness rules are in
[`references/render-notes.md`](references/render-notes.md).

**4. Render:**

```bash
# fast preview
uv run --with pillow python scripts/build.py scripts/spec.json --preview
# final
uv run --with pillow python scripts/build.py scripts/spec.json
```

Output lands in `output_dir` as `final_v1.mp4` (bump `version` in the spec to compare
iterations side by side).

**5. Metadata** (optional): ask the agent for posting copy, or follow
[`references/social-metadata.md`](references/social-metadata.md) to write per-platform
titles/captions to `…/edit/social_metadata.md`.

## The house style is defaults, not laws

Everything in the look is a starting point you can override per-key in the spec —
`speed` (default 1.0), `xfade`, `grade_filter`, `blur_sigma`, `denoise`, `subs_start`, and the
whole `captions` block (font, size, position, colours, words-per-cue). Per segment: `kind`,
`grade`, `fit`, `crop`. Leave a key out and the [`build.py`](scripts/build.py) default applies.
The *creative* calls — which clip, exact trims, how warm the grade — are judgment made by
looking at the footage, not hard-coded.

## Fonts & license

- Bundled fonts — **[Anton](https://fonts.google.com/specimen/Anton)** (captions/title) and
  **[Montserrat](https://fonts.google.com/specimen/Montserrat)** (fallback) — are under the
  **SIL Open Font License 1.1** (licenses in `assets/font-licenses/`). Swap in any font via
  `captions.fontfile` + `fonts_dir`.
- Skill code & docs: **MIT** (see the repo root `LICENSE`).
- Engine credit: [browser-use/video-use](https://github.com/browser-use/video-use).
