# longform-to-shorts

Turn ONE finished long-form video (talking-head + screen-share — a "N tools" walkthrough, tutorial, review, demo) into several **standalone** vertical Shorts/Reels (1080×1920), one per topic, plus per-clip YouTube + Instagram metadata. All `ffmpeg` under the hood, no cloud editor.

Ask your agent something like *"cut shorts from this video"*, *"turn my long-form into reels, one clip per tool"*, or *"trim the short-form out of my video"* and it triggers from its description.

## What it does
1. Transcribe (clean transcript for segmenting + word-level timings for exact cuts).
2. Segment into standalone clips; trim sequencing/dangling words; clean starts and ends.
3. Detect face vs screen; switch to the screen crop only when the screen content actually appears.
4. Reframe to 9:16: face crop-to-fill, screen zoom + slow scroll, split-screen face bubble, transition-freeze.
5. Burn a hook + subtitles (hand-reviewed — raw transcription is a timing scaffold, not postable copy).
6. Polish: whoosh at transitions, optional pitch-preserved speed-up, fades.
7. Verify every clip (frame + re-transcribe) before calling it done.
8. Write per-clip metadata (multiple tension titles + complementary descriptions + captions).

## Prerequisites
- **ffmpeg / ffprobe** on your PATH.
- A transcription skill that returns **word-level timings** — pairs with [`watch` / claude-video](https://github.com/bradautomates/claude-video) + a **Groq** (free tier, preferred) or OpenAI Whisper key in `~/.config/watch/.env`. Line-level transcripts are too coarse to cut cleanly.
- A short **whoosh** `.mp3` for transitions (path configurable).
- A bold display font for the hook (default `Impact`; macOS path in the recipes — swap for your OS).

## Configurable defaults (opinionated — change to taste)
Subtitle color/size/position (`force_style`), speed-up factor (default `atempo=1.1`, pitch preserved; set 1.0 to disable), clip length (~30–45s), hook font, whoosh path. All in `references/ffmpeg-recipes.md`.

## Layout
```
SKILL.md                     # the workflow + judgment calls
references/ffmpeg-recipes.md # every ffmpeg command + the gotchas (read before building)
scripts/gen_subs.py          # word-timings -> per-clip SRT (edit CLIPS dict; always hand-review output)
```

## Example output
A Short cut from a long-form YouTube video with this skill — click to watch:

[<img src="https://i.ytimg.com/vi/BjtdvN_DdSM/oar2.jpg" alt="Your AI Agent Is Lying To You" width="270">](https://www.youtube.com/shorts/BjtdvN_DdSM)

## Not for
Raw multi-take footage (use **shorts-from-takes**), a single freeform edit, or captioning an already-finished short. This is specifically **finished long-form → many standalone verticals**.
</content>
