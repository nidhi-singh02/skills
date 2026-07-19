---
name: longform-to-shorts
description: >
  Cut standalone vertical Shorts/Reels (1080x1920) out of ONE finished long-form talking-head + screen-share
  video (a "N tools" walkthrough, tutorial, review, demo), one Short per topic/tool, then write per-Short
  YouTube + Instagram metadata. Use this whenever the user hands over a finished long-form video and wants
  short-form clips from it, even if they don't say the word "shorts": "cut shorts/reels from this video",
  "trim the short-form videos out of my long-form", "make reels from my youtube video", "turn each tool in my
  video into its own clip", "clip this up for tiktok/reels". Uses ffmpeg + a transcription skill for word
  timings. Do NOT use for raw multi-take footage (use shorts-from-takes) or a single freeform edit; this is
  specifically finished-long-form -> many standalone verticals.
allowed-tools: Bash, Read, Write, Edit
---

# longform-to-shorts

Turn one finished long-form video into several **standalone** vertical Shorts, then write their metadata. Each Short must stand fully alone (no "first/next", no cross-reference), open on a clean full sentence, end clean, and look native to Reels: face zoomed, screen zoomed + scrolling, burned subtitles, a hook, a whoosh, a small speed-up.

This was distilled from a long real edit. The exact ffmpeg commands, the two-phase build, and the gotchas that each cost hours live in **`references/ffmpeg-recipes.md`** — read it before building any clip. The phases below are the plan and the judgment calls.

## Setup
Source = one finished `.mp4` (talking-head + screen-share, ~1080p). Needs `ffmpeg`/`ffprobe` and a transcription skill that can return **word-level timings** (this pairs with the `watch`/claude-video skill + a Groq/OpenAI Whisper key in `~/.config/watch/.env`; line-level transcripts are too coarse to cut cleanly). Provide a short **whoosh** sound effect for transitions. Work in a `shorts/` folder next to the video; keep `_ref/` for frames + `words.json`.

## The pipeline

**1. Transcribe twice.** Full clean transcript for reading/segmenting; word-level JSON for exact cut points. Commands in the reference.

**2. Segment + trim (editorial).** One Short per topic; target ~30–45s (pre-speedup; see Configuration). Every Short is standalone — cut all sequencing ("first/next", "moving on", "second one") and cross-references. Never open on a dangling connective ("but/so/and/that/okay"); start on a clean full sentence (an earlier sentence start often reads best). End on a complete sentence without clipping the last word. Mid-cuts to drop a redundant clause are fine — pick boundaries with a real gap, else remove the whole clause rather than leave a leftover fragment.

**3. Face vs screen.** Sample frames (~every 8s) to map talking-head vs screen-share spans. **The critical rule:** switch to the screen crop only when the screen content *actually appears*, not when the speaker starts mentioning it — otherwise you crop an empty room for a few seconds while they lean to bring the window up. Confirm the real appearance time with 2s-interval frames at the boundary.

**4. Reframe to fill 1080x1920.** Face → center-crop on the face. Screen → zoom + **slow vertical scroll** (a static screen under voiceover looks dead). Screen-only (no face) → split-screen: screen scroll + a full-face PIP bubble. Transition dead-zone → freeze the first clean target frame over the audio. Filters in the reference.

**5. Captions.** Top hook (short, viewer-workflow tension). Burned subtitles: generate an SRT with `scripts/gen_subs.py` (maps word timings onto the edited timeline incl. gaps), then **HAND-REVIEW and correct every SRT** — raw Whisper drops words, mis-hears names, and duplicates; it is not postable. Chunk into natural phrases. Burn recipe in the reference.

**6. Polish.** Whoosh SFX at each face→screen transition; a small **speed-up with pitch preserved** (as a final pass so subtitles stay synced); fade in/out.

**7. Verify before saying done (non-negotiable).** Re-transcribe each Short: clean opening, clean end, no sequencing words, mid-cuts read naturally. Sample frames: face in-frame everywhere (no empty chair), subtitles positioned + readable, screen scrolls, no leftover tag. Confirm the sped audio is intelligible.

**8. Per-Short metadata.** For each Short: **3–4 tension/curiosity title options** (Title Case, no emoji, no overclaim — don't credit a tool with a capability it doesn't have), a YouTube description that *complements* the clip (never restates the spoken lines) + link + hashtags + `#Shorts`, and a platform caption in the creator's voice. Write to `shorts/METADATA.md`.

## Configuration (opinionated defaults, change to taste)
Baked into the recipes as defaults; edit for your style:
- **Subtitles**: color/size/position via `force_style` (default white, bottom). See the reference.
- **Speed-up**: default `atempo=1.1` (pitch preserved). Set to 1.0 to disable.
- **Clip length**: ~30–45s target.
- **Hook font**: default Impact; change the hardcoded `fontfile=` (macOS path by default — swap for your OS).
- **Whoosh SFX**: set the path in the phase-2 command.

## Files
- `references/ffmpeg-recipes.md` — every ffmpeg command + the gotchas. Read before building.
- `scripts/gen_subs.py` — word-timings → per-Short SRT (edit the CLIPS dict; always hand-review output).
</content>
