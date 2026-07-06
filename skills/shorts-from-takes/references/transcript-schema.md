# Transcript schema — what the caption engine reads

`build.py` burns word-by-word captions from a **transcript JSON per source clip**. It was
built around [ElevenLabs Scribe](https://elevenlabs.io/) output (what the `video-use` engine
produces), but the format is trivial — **any word-timestamped transcriber works** if you
match the shape below. That's the whole point of this doc: you don't need `video-use` or an
ElevenLabs key to use this skill, only *some* source of word timestamps.

## Where the files go

For each segment, `build.py` looks for a transcript at:

```
<output_dir>/<transcripts_dir>/<source-filename-stem>.json
```

e.g. a segment whose `src` is `.../selfie_takeA.mov`, with the default
`transcripts_dir: "transcripts"`, is captioned from `<edit>/transcripts/selfie_takeA.json`.
You can also set an explicit `"transcript": "path.json"` on an individual segment to override.
If a transcript is missing, that segment simply renders **without** captions (a warning
prints) — the video still builds.

## The shape

Top-level object with a `words` array. Each entry the engine uses has four fields:

```json
{
  "words": [
    { "type": "word",    "text": "To",  "start": 6.299, "end": 6.420 },
    { "type": "spacing", "text": " ",   "start": 6.420, "end": 6.519 },
    { "type": "word",    "text": "use", "start": 6.519, "end": 6.719 }
  ]
}
```

Rules the engine relies on:

- **`type`** — only entries with `type == "word"` become captions. Anything else
  (`"spacing"`, punctuation-only tokens, etc.) is ignored, so it's safe to include them.
- **`start` / `end`** — floats in **seconds, measured in the ORIGINAL source clip**
  (before any speed-up). `build.py` does all the speed and crossfade offset math itself —
  never pre-adjust timings. Entries missing `start` or `end` are skipped.
- **`text`** — the word. It's upper-cased for the Hormozi look and trailing punctuation is
  stripped automatically, so raw casing/punctuation is fine.
- Extra fields (`speaker_id`, `logprob`, `language_code`, a top-level `text`, …) are
  ignored. Only the four above matter.

## Producing it without video-use / ElevenLabs

Any of these emit word-level timestamps you can reshape into the above:

- **WhisperX** — `result["segments"][*]["words"]` gives `{"word","start","end"}`. Map
  `word -> text`, add `"type": "word"`.
- **faster-whisper** — `model.transcribe(..., word_timestamps=True)`; each `word` has
  `.start`, `.end`, `.word`.
- **OpenAI Whisper** (`--word_timestamps True`), **Deepgram**, **AssemblyAI** — all expose
  per-word start/end; rename fields to `text/start/end` and tag `type: "word"`.

Minimal Python to convert a WhisperX result:

```python
import json
out = {"words": [
    {"type": "word", "text": w["word"], "start": w["start"], "end": w["end"]}
    for seg in result["segments"] for w in seg.get("words", [])
    if w.get("start") is not None and w.get("end") is not None
]}
json.dump(out, open("transcripts/selfie_takeA.json", "w"))
```

That's it — drop the JSON where the naming rule expects it and captions render.
