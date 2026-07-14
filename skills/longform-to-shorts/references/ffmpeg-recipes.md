# ffmpeg recipes + gotchas (longform-to-shorts)

Concrete commands for each phase. Read this when you're about to build a Short. Values (crop x-offsets, segment times, switch points) are footage-specific — sample frames to find them; the *structure* of each command is what's stable.

Paths to set for your machine:
- **Font**: `FONT=/System/Library/Fonts/Supplemental/Impact.ttf` (macOS). On Linux/Windows point at any bold display font (e.g. Impact/Anton/Arial Bold).
- **Whoosh SFX**: `WH=<path to a short whoosh .mp3>`.

## Table of contents
- [Gotchas that cost hours](#gotchas-that-cost-hours)
- [Word-level timings](#word-level-timings)
- [Reframe filters](#reframe-filters)
- [Caption overlays](#caption-overlays)
- [Two-phase build (the pattern)](#two-phase-build-the-pattern)

## Gotchas that cost hours
Read these first; each was a multi-attempt failure in the wild.
- **Captions via `textfile=<file>`, never `text='...'`.** Passing spoken text inline gets mangled by the shell/filtergraph. Write one tiny `.txt` per caption line and reference it.
- **Brace every shell variable used in a filtergraph: `${VAR}`.** Unbraced `$VAR:` in zsh triggers the `:e`/`:t` history-modifier and silently corrupts the value — a font path becomes its basename, `textfile=$F:expansion` becomes `txtxpansion`. This is the single biggest time-sink. When a filter mysteriously "can't find" a file whose name is half-garbled, this is why.
- **`expansion=none` on every `drawtext`** so `%`, `:` and friends in text are literal.
- **Hardcode the font path in `drawtext`** (or use `${FONT}` braced). Do not pass it through an unbraced `$var` (see the brace bug).
- **`force_style` value must be single-quoted inside the filtergraph** (`force_style='...'`) or its internal commas are parsed as filter separators.
- **After `concat`, apply crop/subtitles/fades to the concatenated video `[cv]`; keep audio as its own `concat` + `afade`.**
- **`subtitles` MarginV is scaled by libass PlayRes (~288), not pixels.** `MarginV=45` lands roughly in the bottom third of a 1920-tall frame, not 45px up. Tune by eyeballing a frame; Alignment=2 is bottom-center, 8 is top-center.
- **Whisper word `start` times run ~0.2-0.3s early.** To EXCLUDE a word from a cut, start ~0.3s after its reported start; to keep it, start slightly before.

## Word-level timings
Line-level transcripts are too coarse for clean cuts. Get word timings once:
```
ffmpeg -i <video> -vn -ac 1 -ar 16000 -b:a 64k _ref/full.mp3
KEY=$(grep GROQ_API_KEY ~/.config/watch/.env | cut -d= -f2)
curl -s https://api.groq.com/openai/v1/audio/transcriptions -H "Authorization: Bearer $KEY" \
  -F model=whisper-large-v3 -F file=@_ref/full.mp3 -F response_format=verbose_json \
  -F "timestamp_granularities[]=word" -o _ref/words.json
```
Query a window:
```
python3 -c "import json;w=json.load(open('_ref/words.json'))['words'];print(' '.join(f\"{x['word']}@{x['start']:.1f}\" for x in w if LO<=x['start']<=HI))"
```

## Reframe filters
All output 1080x1920. Sample frames first to find the face x-offset, the face->screen switch (= when the screen CONTENT appears, not when it's mentioned), and the PIP location.

**Face segment (crop-to-fill on face):**
```
[0:v]trim=A0:A1,setpts=PTS-STARTPTS,crop=608:1080:<FACEX>:0,scale=1080:1920[v1]
```

**Screen segment (MUST slow-scroll — a static screen reads dead):**
```
[0:v]trim=B0:B1,setpts=PTS-STARTPTS,crop=456:811:250:269*t/<SEGDUR>,scale=1080:1920[v2]
```
The pan reveals top->bottom of the (static) viewport = looks like scrolling. `269 = 1080-811` (max vertical travel).

**Split-screen (screen-only segment, no talking head): screen scroll + face bubble from the PIP.**
```
[0:v]trim=B0:B1,setpts=PTS-STARTPTS,split=2[a][b];
[a]crop=456:811:250:269*t/<SEGDUR>,scale=1080:1920[base];
[b]crop=300:300:<PIPX>:<PIPY>,scale=420:420[bub];
[base][bub]overlay=x=(W-w)/2:y=1400[c]
```
Optional border: `drawbox=x=330:y=1400:w=420:h=420:color=0xE8641E:t=5`. Frame the bubble FULL-FACE with headroom — cropping too low/tight cuts the forehead.

**Transition dead-zone (leaning out / window still loading): freeze the first clean target frame over the audio so a reveal line ("meet X") plays over a clean visual, not curtain.**
```
[0:v]trim=<CLEAN0>:B1,setpts=PTS-STARTPTS,crop=456:811:250:269*t/<DUR>,scale=1080:1920,tpad=start_duration=0.7:start_mode=clone,setpts=PTS-STARTPTS[v2]
```
Audio still `atrim`s from the earlier point so the words are intact; video length = freeze + clip must equal the audio length.

## Caption overlays
**Top hook** (dark bar + display font, white). `${FONT}` is your bold font path:
```
drawbox=x=0:y=205:w=1080:h=150:color=0x000000@0.5:t=fill,
drawtext=fontfile=${FONT}:textfile=hook.txt:expansion=none:fontsize=56:fontcolor=white:x=(w-tw)/2:y=248
```
**Burned subtitles** (after generating + hand-reviewing the SRT). Default white; change PrimaryColour for your style:
```
subtitles=<name>.srt:force_style='FontName=Arial,Fontsize=14,Bold=1,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=45'
```
Use `Alignment=8` (top) on split-screen Shorts so subtitles clear the bottom face bubble.

## Two-phase build (the pattern)
Build at 1x with all video + subtitles + hook + fades, THEN a final pass for SFX + speed (so subtitles stay synced).

**Phase 1 — face+screen Short (audio = concat of the same segments; handles mid-cut gaps uniformly):**
```
ffmpeg -y -i "$S" -filter_complex \
"[0:v]trim=A0:A1,setpts=PTS-STARTPTS,crop=608:1080:FACEX:0,scale=1080:1920[v1];\
 [0:v]trim=B0:B1,setpts=PTS-STARTPTS,crop=456:811:250:269*t/SEGDUR,scale=1080:1920[v2];\
 [v1][v2]concat=n=2:v=1:a=0[cv];\
 [0:a]atrim=A0:A1,asetpts=PTS-STARTPTS[aa];[0:a]atrim=B0:B1,asetpts=PTS-STARTPTS[ab];[aa][ab]concat=n=2:v=0:a=1[ca];\
 [cv]drawbox=...,drawtext=...:textfile=hook.txt...,subtitles=name.srt:force_style='...',fade=t=in:st=0:d=0.2,fade=t=out:st=FO:d=0.4[v];\
 [ca]afade=t=in:st=0:d=0.2,afade=t=out:st=FO:d=0.4[o]" \
-map "[v]" -map "[o]" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -r 30 _ref/p1_name.mp4
```

**Phase 2 — whoosh at the face->screen transition + speed (pitch preserved):**
```
ffmpeg -y -i _ref/p1_name.mp4 -i "$WH" -filter_complex \
"[1:a]volume=0.4,adelay=TRANS_MS|TRANS_MS[wh];[0:a][wh]amix=inputs=2:normalize=0[am];[am]atempo=1.1[oa];[0:v]setpts=PTS/1.1[ov]" \
-map "[ov]" -map "[oa]" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 160k -r 30 -movflags +faststart name.mp4
```
`atempo=1.1` preserves pitch (set to 1.0 to disable the speed-up). `FO = clip_dur - 0.4`.
</content>
