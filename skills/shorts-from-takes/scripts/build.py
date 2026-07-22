#!/usr/bin/env python3
"""shorts-from-takes renderer — config-driven vertical Short builder.

Reads a spec.json describing the chosen segments and house-style settings, then:
  per-segment extract (fit each clip to vertical: cover-crop or blurred fill) with
  optional speed-up, optional relight, gentle denoise + 30ms audio fades
  -> lossless concat into blocks
  -> xfade chain between blocks (orientation flips / take changes)
  -> title card overlay (first N s)
  -> Hormozi-style ASS captions applied LAST
  -> loudness normalize to -14 LUFS.

This is the RENDER engine only. Picking takes, trim points, and grade amounts is a
judgment job done in the conversation (see SKILL.md) — this script just executes the spec.

Usage:
    python build.py spec.json
    python build.py spec.json --preview     # faster, lower CRF
    python build.py spec.json --check       # verify a rendered output vs the spec

Loudnorm uses video-use's helper if present (auto-resolved; inherits upstream fixes),
otherwise a built-in 2-pass loudnorm — so this runs standalone with no external repo.
"""
from __future__ import annotations
import argparse, functools, json, os, re, subprocess, sys
from pathlib import Path

# ---- house-style defaults (overridable per-key in spec.json) ----------------
DEFAULTS = {
    "version": "v1",
    "speed": 1.0,                 # 1.0 keeps native pacing; e.g. 1.2 punches up talking-head takes (pitch preserved)
    "xfade": 0.2,                 # crossfade seconds at block joins
    "xfade_type": "fade",         # ffmpeg xfade transition for every block join (fade, slideup, wipeleft, ...)
    "xfade_types": [],            # optional per-join override, in block-join order; falls back to xfade_type
    "fps": 30,
    "width": 1080, "height": 1920,
    "title_seconds": 3.0,         # title card shown 0..N, fades in/out
    "subs_start": 0.0,            # earliest caption time (set 3.0 to free the open)
    "title": "",
    "fonts_dir": None,            # default: skill assets/fonts
    "transcripts_dir": "transcripts",
    # relight recipe, applied ONLY to segments with "grade": true (or a per-segment
    # custom filter string). Default = warm + lift shadows + tame highlights (suits skin).
    "grade_filter": ("colortemperature=temperature=5200:pl=1,"
                     "curves=master='0/0.05 0.25/0.30 0.75/0.71 1/0.93',"
                     "eq=saturation=1.03"),
    "blur_sigma": 18,             # gaussian blur strength for landscape blur-fill backdrop
    "denoise": "highpass=f=70,afftdn=nr=8:nf=-50",   # gentle; "" to disable
    "loudnorm": True,
    "name_fix": {},               # caption text corrections, e.g. {"CLAWED":"CLAUDE"}
    "captions": {
        "font": "Anton",          # family name libass resolves from fonts_dir
        "fontfile": "Anton-Regular.ttf",
        "fontsize": 116, "marginv": 650,
        "primary": "&H0000F0FF",      # fill (sung) = yellow  AABBGGRR
        "secondary": "&H00FFFFFF",    # pre-fill (unsung) = white
        "outline_colour": "&H00101010",
        "outline": 8, "shadow": 4,
        "pop": True,              # quick scale pop-in per cue
        "max_words": 2,
        "highlight": "",          # ASS colour (&HAABBGGRR) for highlight_words; "" disables
    },
    "highlight_words": [],        # words to tint captions.highlight (matched uppercase,
                                  # after punctuation strip — same normalization as cues)
    "top_titles": [],             # beat labels: [{"start","end","text","colour"?,"fontsize"?}]
                                  # (output seconds), rendered top-center via the ASS Top style
    "top_title_marginv": 210,     # Top style margin FROM THE TOP — below platform UI chrome
    "inserts": [],                # image B-roll overlays: [{"file","start","end","x","y"}]
                                  # (output seconds), alpha-faded, drawn under the captions
    # video-use helpers dir (OPTIONAL — only its 2-pass loudnorm is borrowed). Leave
    # null to auto-resolve from $VIDEO_USE_HELPERS / common paths, else the built-in
    # 2-pass loudnorm runs so this works with no external repo. See resolve_helpers().
    "video_use_helpers": None,
}
PUNCT = set(".,!?;:")


class RenderConfigError(RuntimeError):
    pass


def sh(cmd, cwd=None):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.PIPE, cwd=cwd)


def atempo_chain(spd: float) -> str:
    """ffmpeg's atempo accepts 0.5..2.0 per instance. Chain factors (whose product == spd)
    so a `speed` override outside that window still works instead of hard-failing at extract."""
    factors, s = [], float(spd)
    while s > 2.0:
        factors.append(2.0); s /= 2.0
    while s < 0.5:
        factors.append(0.5); s /= 0.5
    factors.append(s)
    return ",".join(f"atempo={f:g}" for f in factors)


def dur(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "default=nk=1:nw=1", str(p)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def probe_wh(p):
    """Display width,height of a clip's video stream — rotation-aware, so portrait
    phone footage (often stored landscape + a 90° flag) classifies correctly. Only
    called to auto-detect orientation when a segment omits "kind"."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height:side_data=rotation", "-of", "json", str(p)],
        capture_output=True, text=True, check=True)
    st = json.loads(out.stdout)["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    rot = 0
    for sd in st.get("side_data_list", []):
        try:
            rot = int(sd.get("rotation", 0))
        except (TypeError, ValueError):
            pass
    if abs(rot) % 180 == 90:
        w, h = h, w
    return w, h


# ---- loudnorm ---------------------------------------------------------------
# -14 LUFS / -1 dBTP is the de-facto target for social video (what YT/IG/TikTok
# normalize toward), so mixing to it means platforms re-touch your audio the least.
LUFS_I, LUFS_TP, LUFS_LRA = -14.0, -1.0, 11.0


def measure_loudness(p: Path):
    """Analysis-pass loudnorm; returns ffmpeg's measurement dict (input_i, input_tp,
    input_lra, input_thresh, target_offset) or None if it can't be parsed. Used both to
    drive the 2-pass correction and to verify an output in --check."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(p),
         "-af", f"loudnorm=I={LUFS_I}:TP={LUFS_TP}:LRA={LUFS_LRA}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    try:
        return json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    except Exception:
        return None


def resolve_helpers(explicit):
    """Locate video-use's helpers dir — OPTIONAL, only its 2-pass loudnorm is used.

    We resolve rather than hardcode a path so the skill is portable: video-use is a
    separate, optional install (https://github.com/browser-use/video-use). Order:
    explicit spec value -> $VIDEO_USE_HELPERS -> a couple of common checkout spots.
    Returns a path string if found, else None (caller uses the built-in fallback)."""
    cand = explicit or os.environ.get("VIDEO_USE_HELPERS")
    if cand and Path(cand).is_dir():
        return cand
    for p in (Path(__file__).resolve().parents[2] / "video-use/helpers",  # sibling in a skills/ checkout
              Path.home() / ".claude/skills/video-use/helpers",            # standard skill install
              Path.home() / "video-use/helpers"):                          # clone in home dir
        if p.is_dir():
            return str(p)
    return None


def _local_loudnorm(inp: Path, outp: Path, preview=False):
    """Built-in 2-pass loudnorm so the skill needs no external repo.

    Two-pass (measure, then correct against that measurement) is what lands the mix
    ON -14 LUFS instead of merely near it; single-pass drifts on quiet or peaky
    speech. Preview skips the measure pass for speed. Video is stream-copied — only
    audio is touched. Falls back to one-pass if the measurement can't be parsed."""
    common = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000",
              "-movflags", "+faststart", str(outp)]
    base = f"loudnorm=I={LUFS_I}:TP={LUFS_TP}:LRA={LUFS_LRA}"
    if not preview:
        d = measure_loudness(inp)
        if d:
            base += (f":measured_I={d['input_i']}:measured_TP={d['input_tp']}"
                     f":measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}"
                     f":offset={d['target_offset']}:linear=true")
        # measurement unreadable -> base stays one-pass, the safe degrade
    sh(["ffmpeg", "-y", "-i", str(inp), "-c:v", "copy", "-af", base] + common)
    return True


def get_loudnorm(helpers_dir):
    """Prefer video-use's loudnorm if its helpers are present (inherits upstream
    fixes); otherwise the built-in 2-pass above. Same API either way:
    (input_path, output_path, preview=False) -> bool."""
    hd = resolve_helpers(helpers_dir)
    if hd:
        try:
            sys.path.insert(0, hd)
            from render import apply_loudnorm_two_pass  # type: ignore
            return apply_loudnorm_two_pass
        except Exception:
            pass
    return _local_loudnorm


# ---- HDR -> SDR tone mapping (HLG / PQ sources) -----------------------------
# iPhone selfie takes default to HLG HDR. If we only drop bit depth without
# tone-mapping, the 8-bit output still carries HLG/PQ transfer metadata and social
# re-encodes read it as HDR -> oversaturated / blown out. Detect via color_transfer
# and prepend a zscale+tonemap chain so the output is clean Rec.709 SDR.
HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}  # PQ (HDR10) and HLG
ZSCALE_TONEMAP_CHAIN = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                        "tonemap=tonemap=hable:desat=0,"
                        "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


@functools.lru_cache(maxsize=None)
def ffmpeg_has_filter(name: str) -> bool:
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                             capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return any(len(parts := line.split()) >= 2 and parts[1] == name
               for line in out.stdout.splitlines())


def tonemap_chain() -> str:
    if ffmpeg_has_filter("zscale"):
        return ZSCALE_TONEMAP_CHAIN
    raise RenderConfigError(
        "HDR source detected, but this ffmpeg build does not include the zscale "
        "filter required for HDR->SDR tone mapping. Install an ffmpeg build with "
        "libzimg/zscale support, or convert the source to SDR before rendering.")


def is_hdr_source(video) -> bool:
    """True if the source uses a PQ or HLG transfer function (needs tone-mapping)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=color_transfer",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
            capture_output=True, text=True, check=True)
        return out.stdout.strip() in HDR_TRANSFERS
    except subprocess.CalledProcessError:
        return False


# ---- per-segment extract ----------------------------------------------------
def extract(seg, i, cfg, clips, preview):
    odur = float(seg["end"]) - float(seg["start"])
    spd = cfg["speed"]
    sdur = odur / spd
    fd = min(0.03, max(0.0, sdur / 2.0))   # 30ms edge fades, shrunk so sub-60ms clips
    fo = max(0.0, sdur - fd)               # don't get overlapping in/out fades
    crf = "20" if preview else "16"
    preset = "medium" if preview else "fast"
    out = clips / f"seg_{i}.mp4"
    W, H, fps = cfg["width"], cfg["height"], cfg["fps"]

    # per-segment gain (dB): level a take shot without the mic in hand (typically
    # 15-20 LU under the mic'd takes) up to its neighbours. Pure volume, BEFORE the
    # denoise so afftdn's noise floor sees the same levels on every segment; global
    # loudnorm can't fix relative imbalance between segments, only overall level.
    gv = float(seg.get("gain", 0))
    gainf = f"volume={gv:g}dB," if gv else ""
    den = (cfg["denoise"] + ",") if cfg["denoise"] else ""
    aud = (f"{gainf}{den}{atempo_chain(spd)},"
           f"afade=t=in:st=0:d={fd:.3f},afade=t=out:st={fo:.3f}:d={fd:.3f}")
    # -r sets the frame RATE, but the MP4 timebase (tbn) still inherits from the source:
    # a 29.97fps source leaves tbn=30000/1001 even at -r 30. concat_copy uses -c copy so it
    # can't renormalize, and the block xfade then rejects mismatched timebases (error 234).
    # -fps_mode cfr forces constant frame rate; -video_track_timescale pins a fixed tbn so
    # every seg — whatever the source — shares one timebase and blocks concat + xfade cleanly.
    tail = ["-c:v", "libx264", "-preset", preset, "-crf", crf,
            "-pix_fmt", "yuv420p", "-r", str(fps), "-fps_mode", "cfr",
            "-video_track_timescale", str(fps * 1000),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(out)]
    # -ss and -t BEFORE -i bound the SOURCE range so setpts can compress to sdur.
    head = ["ffmpeg", "-y", "-ss", f"{float(seg['start']):.3f}",
            "-t", f"{odur:.3f}", "-i", seg["src"]]

    # optional per-segment source crop [x, y, w, h] — zoom/reframe the SHARP clip
    # (push into the legible region of a screen recording, recompose a subject…).
    # Even w/h only. On blur-fill it crops the foreground only; the blurred backdrop
    # stays the full frame (else a wide/thin crop makes a giant ugly blur).
    cr = seg.get("crop")
    cropf = f"crop={int(cr[2])}:{int(cr[3])}:{int(cr[0])}:{int(cr[1])}," if cr else ""
    # optional separate crop for the blurred backdrop [x, y, w, h]. Use when the
    # full frame contains something you don't want bleeding through the blur
    # (e.g. a burned-in caption in the source). Defaults to the full frame.
    bgc = seg.get("bg_crop")
    bgcropf = f"crop={int(bgc[2])}:{int(bgc[3])}:{int(bgc[0])}:{int(bgc[1])}," if bgc else ""

    # Framing is orientation-based, not content-based, so this works for ANY clips.
    # "kind" is optional — omit it and orientation is auto-detected from the source.
    # Accepted: "portrait"/"vertical" (or legacy "face"); "landscape"/"wide" (or legacy
    # "laptop"/"screen"). "fit" picks how a clip fills the 1080x1920 frame:
    #   "cover" — scale to fill, center-crop (no bars; robust for any aspect ratio)
    #   "blur"  — sharp clip centered over its own blurred fill (keeps every pixel)
    # Default: landscape -> blur (so wide content isn't cropped), else cover.
    ORIENT = {"portrait": "portrait", "vertical": "portrait", "face": "portrait",
              "landscape": "landscape", "wide": "landscape", "laptop": "landscape",
              "screen": "landscape"}
    orient = ORIENT.get((seg.get("kind") or "").lower())
    if orient is None:
        w, h = probe_wh(seg["src"])
        orient = "portrait" if h >= w else "landscape"

    # grade: opt-in per segment. true -> house relight recipe; a string -> custom filter.
    g = seg.get("grade", False)
    gf = cfg["grade_filter"] if g is True else (g if isinstance(g, str) and g.strip() else "")
    grade = ("," + gf) if gf else ""

    # HDR (HLG/PQ, e.g. iPhone) -> tone-map to Rec.709 SDR first, else colours blow out.
    tm = (tonemap_chain() + ",") if is_hdr_source(seg["src"]) else ""

    fit = (seg.get("fit") or "").lower() or ("blur" if orient == "landscape" else "cover")
    if fit == "blur":
        sigma = cfg.get("blur_sigma", cfg.get("laptop_blur_sigma", 18))
        fc = (f"[0:v]{tm}split=2[bg][fg];"
              f"[bg]{bgcropf}scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},gblur=sigma={sigma}[bg2];"
              f"[fg]{cropf}scale={W}:-2[fg2];"
              f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2,setsar=1{grade},"
              f"setpts=PTS/{spd},fps={fps}[v];[0:a]{aud}[a]")
        cmd = head + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]"] + tail
    else:  # cover — scale to fill then center-crop; works for any source aspect ratio
        # optional animated zoom: seg["zoom"] = [z_start, z_end], interpolated linearly
        # over the segment (a push-in, a pull-back, or a "punch" that drifts). Two rules
        # learned the hard way:
        #  - `fps=` MUST run before zoompan: on VFR / odd-timebase sources (phone footage)
        #    zoompan otherwise multiplies the frame count ~15x and the clip runs long.
        #  - sample from a 4/3-oversized intermediate so any zoom <= 1.33 only ever
        #    downscales (no upscale artifacts). Not offered on the blur fit: zooming the
        #    sharp foreground against a static blur backdrop reads as a glitch.
        zm = seg.get("zoom")
        if zm:
            z0, z1 = float(zm[0]), float(zm[1])
            nfr = max(1, int(round(odur * fps)))
            iw2, ih2 = int(W * 4 / 3) // 2 * 2, int(H * 4 / 3) // 2 * 2
            vf = (f"{tm}fps={fps},{cropf}"
                  f"scale={iw2}:{ih2}:force_original_aspect_ratio=increase,"
                  f"crop={iw2}:{ih2},"
                  f"zoompan=z='{z0}+({z1}-{z0})*in/{nfr}'"
                  f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                  f":d=1:s={W}x{H}:fps={fps},"
                  f"setsar=1{grade},setpts=PTS/{spd},fps={fps}")
        else:
            vf = (f"{tm}{cropf}scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H},setsar=1{grade},setpts=PTS/{spd},fps={fps}")
        cmd = head + ["-vf", vf, "-af", aud] + tail
    kn = f"/{seg['kind']}" if seg.get("kind") else " auto"
    print(f"  seg{i} ({orient}{kn} {fit}, {seg.get('beat','')}) {odur:.2f}s -> {sdur:.2f}s")
    sh(cmd)
    return out


def concat_copy(parts, out: Path, edit: Path):
    lst = edit / f"_cc_{out.stem}.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", "-movflags", "+faststart", str(out)])
    lst.unlink(missing_ok=True)


# ---- captions (ASS, Hormozi word-fill) --------------------------------------
def _ass_ts(s):
    s = max(0.0, s); cs = int(round(s * 100)); h, r = divmod(cs, 360000)
    m, r = divmod(r, 6000); sec, c = divmod(r, 100)
    return f"{h:d}:{m:02d}:{sec:02d}.{c:02d}"


def _caption_measurer(cfg, fonts_dir):
    """Return (measure_fn, safe_px, fit_fs) for keeping cues inside the frame, or (None, 0, None).

    libass normalizes `Fontsize` by the font's (ascent+descent) cell, not the em square,
    so a font with tall vertical metrics renders visibly smaller than PIL reports at the
    same number. Scale PIL widths by fontsize/(ascent+descent) to line up with libass
    (empirically within ~2%). `safe_px` is PlayResX minus the style's L/R margins.

    `fit_fs(t)` is the largest `\\fs` that keeps `t` inside `safe_px`. Only the glyph
    advances scale with `\\fs`; the per-char spacing and the outline (`\\bord`) are fixed
    (ScaledBorderAndShadow scales border by the coordinate scale, which is 1.0 here since
    PlayRes == output), so shrink on the scalable part alone or the fixed outline pushes a
    boundary cue back over the edge."""
    c = cfg["captions"]
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(str(fonts_dir / c["fontfile"]), c["fontsize"])
        asc, desc = f.getmetrics()
        k = c["fontsize"] / max(1, asc + desc)
        spacing = 2  # matches the style's Spacing field below
        safe_px = cfg["width"] - 2 * 70  # MarginL/MarginR are 70 in the style
        fixed = lambda t: spacing * len(t) + 2 * c["outline"]  # unaffected by \fs
        measure = lambda t: f.getlength(t) * k + fixed(t)

        def fit_fs(t):
            glyph = f.getlength(t) * k
            if glyph <= 0:
                return c["fontsize"]
            return max(1, int(c["fontsize"] * (safe_px - fixed(t)) / glyph))

        return measure, safe_px, fit_fs
    except Exception:
        return None, 0, None


def build_ass(segs, offsets, cfg, edit, out: Path, fonts_dir: Path = None):
    c = cfg["captions"]
    pop = (r"{\fad(50,0)\fscx84\fscy84\t(0,110,\fscx100\fscy100)}"
           if c.get("pop") else "")
    # Keep cues inside the frame. WrapStyle 2 disables libass auto-wrap, so a cue wider
    # than the usable width silently runs off both edges (clipped). Measure each cue: a
    # too-wide multi-word cue gets an \N break near its middle; a single word that still
    # overflows gets an \fs shrink. Only active when the font is measurable (fonts_dir set).
    measure, safe_px, fit_fs = _caption_measurer(cfg, fonts_dir) if fonts_dir else (None, 0, None)
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {cfg['width']}\nPlayResY: {cfg['height']}\n"
        "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Pop,{c['font']},{c['fontsize']},{c['primary']},{c['secondary']},"
        f"{c['outline_colour']},&H66000000,0,0,0,0,100,100,2,0,1,"
        f"{c['outline']},{c['shadow']},2,70,70,{c['marginv']},1\n"
        # Top: beat labels / section titles. Alignment 8 = top-center, so MarginV is
        # measured FROM THE TOP — keep it below the platforms' UI chrome (status bar,
        # account row) but high enough to clear the subject's face.
        f"Style: Top,{c['font']},72,&H00FFFFFF,&H00FFFFFF,"
        f"{c['outline_colour']},&H66000000,0,0,0,0,100,100,2,0,1,"
        f"6,3,8,70,70,{cfg.get('top_title_marginv', 210)},1\n\n"
        "[Events]\n"
        # MarginV REQUIRED in this Format line — omitting it leaks a comma into Text.
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n")
    subs_start = cfg["subs_start"]; spd = cfg["speed"]
    name_fix = {k.upper(): v for k, v in cfg["name_fix"].items()}
    tdir = edit / cfg["transcripts_dir"]
    dlg = []
    timeline = []
    for seg in segs:
        i = seg["_i"]
        off = offsets[i]
        seg_end = off + (float(seg["end"]) - float(seg["start"])) / spd
        timeline.append((off, i, seg_end))
    timeline.sort()
    cue_end_limits = {}
    for pos, (off, i, seg_end) in enumerate(timeline):
        later_offsets = [later_off for later_off, _, _ in timeline[pos + 1:]
                         if later_off > off + 1e-6]
        cue_end_limits[i] = min(seg_end, later_offsets[0]) if later_offsets else seg_end

    for seg in segs:
        i = seg["_i"]
        tpath = Path(seg.get("transcript")) if seg.get("transcript") else \
            tdir / f"{Path(seg['src']).stem}.json"
        if not tpath.is_absolute():
            tpath = edit / tpath
        if not tpath.exists():
            print(f"  ! no transcript for seg{i} ({tpath.name}) — skipping its captions")
            continue
        t = json.loads(tpath.read_text(encoding="utf-8"))
        s0, e0, off = float(seg["start"]), float(seg["end"]), offsets[i]
        # Clamp cues before the next timeline entry. Block crossfades start the incoming
        # segment early, so the outgoing caption must end before that overlap begins.
        cue_end_limit = cue_end_limits[i]
        words = [w for w in t.get("words", [])
                 if w.get("type") == "word" and w.get("start") is not None
                 and w.get("end") is not None and w["end"] > s0 and w["start"] < e0
                 and (w.get("text") or "").strip()]

        def ot(src):
            return (min(max(src, s0), e0) - s0) / spd + off

        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= c["max_words"] or w["text"].strip()[-1] in PUNCT:
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        for k, ch in enumerate(chunks):
            ls = ot(ch[0]["start"])
            if ot(ch[-1]["end"]) <= subs_start:
                continue
            ls = max(ls, subs_start)
            txts = [name_fix.get(t, t) for t in
                    (re.sub(r"\s+", " ", w["text"]).strip().rstrip(",.;:!?").upper()
                     for w in ch)]
            # keep the rendered cue inside safe_px: break wide multi-word cues, shrink a
            # lone word that still overflows (see WrapStyle note above).
            brk, shrink = None, ""
            if measure:
                if len(txts) > 1 and measure(" ".join(txts)) > safe_px:
                    brk = len(txts) // 2
                lines = ([" ".join(txts[:brk]), " ".join(txts[brk:])] if brk
                         else [" ".join(txts)])
                widest_line = max(lines, key=measure)
                if measure(widest_line) > safe_px:
                    shrink = f"{{\\fs{fit_fs(widest_line)}}}"
            hl = {x.upper() for x in cfg.get("highlight_words", [])}
            hlc = c.get("highlight")
            parts, cursor = ([shrink] if shrink else []), ls
            for wi, w in enumerate(ch):
                ws, we = ot(w["start"]), ot(w["end"])
                gap = ws - cursor
                if gap > 0.02:
                    parts.append(f"{{\\k{int(round(gap*100))}}}")
                d = max(0.06, we - max(ws, cursor))
                sep = r"\N" if brk is not None and wi == brk - 1 else " "
                # highlight_words: retint this word's karaoke fill via \1c (the \kf sweep
                # fills toward PrimaryColour, so overriding \1c changes the sung colour);
                # restore the style's primary right after so following words are untouched.
                tint = f"\\1c{hlc.replace('&H00', '&H')}" if hlc and txts[wi] in hl else ""
                untint = f"{{\\1c{c['primary'].replace('&H00', '&H')}}}" if tint else ""
                parts.append(f"{{\\kf{int(round(d*100))}{tint}}}{txts[wi]}{untint}{sep}")
                cursor = we
            # a cue may not outlive the NEXT cue's start: the +0.12 hang otherwise
            # overlaps it and libass draws both at the same spot (glyph collision —
            # obvious with max_words=1, where every cue lands dead-center).
            nxt = ot(chunks[k + 1][0]["start"]) - 0.01 if k + 1 < len(chunks) else 1e9
            le = min(cursor + 0.12, cue_end_limit - 0.02, nxt)
            if le <= ls:
                continue
            # per-segment MarginV override (Dialogue field; 0 = inherit the style's
            # marginv). Lets one shot lift its captions to clear on-screen content, e.g.
            # a terminal status bar or a lower-third, without moving every other cue.
            mv = int(seg.get("marginv", 0))
            dlg.append((ls, le, f"Dialogue: 0,{_ass_ts(ls)},{_ass_ts(le)},"
                                f"Pop,,0,0,{mv},,{pop}{''.join(parts).strip()}"))
    # top_titles: hand-timed beat labels (OUTPUT seconds — after speed-up and xfade
    # overlap; read the final timeline off the measured seg durations, not the spec math,
    # since AAC frame rounding drifts the concat ~+0.04s per segment).
    for tt in cfg.get("top_titles", []):
        col = tt.get("colour")
        ov = (r"{\fad(200,200)" +
              (f"\\1c{col.replace('&H00', '&H')}" if col else "") +
              (f"\\fs{tt['fontsize']}" if tt.get("fontsize") else "") + "}")
        dlg.append((float(tt["start"]), float(tt["end"]),
                    f"Dialogue: 1,{_ass_ts(float(tt['start']))},{_ass_ts(float(tt['end']))},"
                    f"Top,,0,0,0,,{ov}{tt['text'].upper()}"))
    dlg.sort()
    out.write_text(header + "\n".join(d[2] for d in dlg) + "\n", encoding="utf-8")
    print(f"  master.ass: {len(dlg)} cues")


def make_title(cfg, fonts_dir, out: Path):
    from PIL import Image, ImageDraw, ImageFont
    W = cfg["width"]; H = 460
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    fpath = str(fonts_dir / cfg["captions"]["fontfile"])
    try:
        font = ImageFont.truetype(fpath, 84)
    except Exception:
        # The bundled font should always load; if a custom fonts_dir is missing it,
        # degrade cross-platform (never a hardcoded OS font path — that breaks off macOS).
        try:
            font = ImageFont.truetype(str(fonts_dir / "Montserrat-Black.ttf"), 84)
        except Exception:
            font = ImageFont.load_default()
    title = cfg["title"].upper()
    words = title.split(); lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) > W - 140 and cur:
            lines.append(cur); cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    asc, desc = font.getmetrics(); lh = asc + desc + 10
    tw = max(d.textlength(ln, font=font) for ln in lines)
    bx, by = (W - tw - 84) / 2, (H - lh * len(lines) - 52) / 2
    d.rounded_rectangle([bx, by, bx + tw + 84, by + lh * len(lines) + 52],
                        radius=28, fill=(0, 0, 0, 150))
    y = by + 26
    for ln in lines:
        x = (W - d.textlength(ln, font=font)) / 2
        d.text((x + 2, y + 3), ln, font=font, fill=(0, 0, 0, 170))
        d.text((x, y), ln, font=font, fill=(255, 255, 255, 255))
        y += lh
    img.save(out)
    print(f"  title.png ({len(lines)} line(s))")


# ---- self-eval gate ---------------------------------------------------------
def run_checks(cfg, segs, blocks, edit, preview):
    """Machine-verifiable gate over an already-rendered output. Duration and loudness are
    hard PASS/FAIL — they catch silent breakage a log won't show (a skipped loudnorm, a
    `-ss/-t` speed regression). Caption count is INFO, not a gate: no-speech montages
    legitimately carry none. Returns True iff the hard checks pass; CLI exits non-zero."""
    XF = cfg["xfade"]; spd = cfg["speed"]; tag = f"_{cfg['version']}"
    out = edit / (f"preview{tag}.mp4" if preview else f"final{tag}.mp4")
    ass = edit / "master.ass"
    passed = True

    def check(name, cond, detail=""):
        nonlocal passed
        passed = passed and cond
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print(f"checking {out.name}")
    if not out.exists():
        print(f"  [FAIL] output missing — {out} (render before --check)")
        return False

    got = dur(out)
    exp = sum((float(s['end']) - float(s['start'])) / spd for s in segs) - (len(blocks) - 1) * XF
    check("duration matches spec", abs(got - exp) <= 0.3,
          f"got {got:.2f}s vs expected {exp:.2f}s (speed {spd}x, {len(blocks) - 1} xfade(s))")

    if cfg["loudnorm"]:
        d = measure_loudness(out)
        li = float(d["input_i"]) if d else None
        tp = float(d["input_tp"]) if d else None
        check("integrated loudness ~ -14 LUFS", li is not None and -15.0 <= li <= -13.0,
              f"measured {li} LUFS")
        check("true-peak <= -1 dBTP (small slack)", tp is not None and tp <= -0.5,
              f"measured {tp} dBTP")

    ndlg = sum(1 for ln in ass.read_text(encoding="utf-8").splitlines()
               if ln.startswith("Dialogue:")) if ass.exists() else 0
    print(f"  [INFO] captions: {ndlg} cue(s)" +
          ("" if ndlg else " — none (fine for a no-speech montage; verify if you expected some)"))

    # canvas spine: a wrong-resolution/fps render passes duration+loudness but is unpostable.
    wh = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True).stdout.strip().split(",")
    ow, oh = (int(wh[0]), int(wh[1])) if len(wh) >= 2 else (0, 0)
    num, den = (wh[2].split("/") + ["1"])[:2] if len(wh) >= 3 and "/" in wh[2] else ("0", "1")
    ofps = round(float(num) / float(den))  # r_frame_rate is "30/1"
    check("canvas is spec WxH", (ow, oh) == (cfg["width"], cfg["height"]),
          f"got {ow}x{oh} vs {cfg['width']}x{cfg['height']}")
    check("fps matches spec", ofps == cfg["fps"], f"got {ofps} vs {cfg['fps']}")

    print("  " + ("ALL CHECKS PASSED" if passed else "CHECKS FAILED"))
    return passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="verify an already-rendered output against the spec "
                         "(duration, -14 LUFS loudness; caption count reported) and exit")
    args = ap.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    cfg = {**DEFAULTS, **spec}
    cfg["captions"] = {**DEFAULTS["captions"], **spec.get("captions", {})}
    edit = Path(cfg.get("output_dir") or args.spec.parent).resolve()
    skill_root = Path(__file__).resolve().parent.parent
    fonts_dir = Path(cfg["fonts_dir"]).resolve() if cfg["fonts_dir"] \
        else skill_root / "assets" / "fonts"

    segs = spec["segments"]
    for i, s in enumerate(segs):
        s["_i"] = i
    blocks = spec.get("blocks") or [[i] for i in range(len(segs))]
    XF = cfg["xfade"]; preview = args.preview

    if args.check:
        sys.exit(0 if run_checks(cfg, segs, blocks, edit, preview) else 1)

    clips = edit / "clips"; clips.mkdir(parents=True, exist_ok=True)
    print("1) extract segments")
    paths = [extract(s, i, cfg, clips, preview) for i, s in enumerate(segs)]
    m = [dur(p) for p in paths]

    print("2) blocks + xfade timing")
    bfiles = []
    for j, idxs in enumerate(blocks):
        if len(idxs) == 1:
            bfiles.append(paths[idxs[0]])
        else:
            bf = edit / f"block{j}.mp4"; concat_copy([paths[i] for i in idxs], bf, edit)
            bfiles.append(bf)
    db = [dur(f) for f in bfiles]; n = len(db)
    block_off = [0.0] * n; xf_off = [0.0] * n; acc = db[0]
    for j in range(1, n):
        xf_off[j] = acc - XF; block_off[j] = acc - XF; acc += db[j] - XF
    offsets = {}
    for j, idxs in enumerate(blocks):
        cur = block_off[j]
        for i in idxs:
            offsets[i] = cur; cur += m[i]
    print(f"   total ~{acc:.2f}s, {n} block(s), {n-1} xfade(s)")

    print("3) captions + title")
    build_ass(segs, offsets, cfg, edit, edit / "master.ass", fonts_dir=fonts_dir)
    has_title = bool(cfg["title"].strip())  # title is optional; skip the whole title path if empty
    if has_title:
        make_title(cfg, fonts_dir, edit / "title.png")

    print("4) composite (xfade chain -> title -> captions LAST)")
    ts = cfg["title_seconds"]
    # Normalize every block's frame rate + timebase before the xfade chain. concat -c copy can
    # leave a multi-clip block reporting avg_frame_rate 30000/1001 (inferred from a 29.97 source's
    # timestamps) while a single-seg block stays 30/1 — and xfade rejects mismatched input frame
    # rates ("do not match", error 234 / -22). fps + settb re-stamp both sides so any block mix joins.
    for j in range(n):
        vp.append(f"[{j}:v]fps={cfg['fps']},settb=AVTB[b{j}]")
    cur = "[b0]"
    xft = cfg.get("xfade_types") or []   # per-join transition; else the single xfade_type
    for j in range(1, n):
        nl = f"[xv{j}]"
        tr = xft[j - 1] if j - 1 < len(xft) else cfg["xfade_type"]
        vp.append(f"{cur}[b{j}]xfade=transition={tr}:duration={XF}:"
                  f"offset={xf_off[j]:.3f}{nl}"); cur = nl
    if has_title:
        ti = n  # title.png is appended as input index n, after the n block inputs
        vp.append(f"[{ti}:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,"
                  f"fade=t=out:st={ts-0.3:.2f}:d=0.3:alpha=1[ttl]")
        vp.append(f"{cur}[ttl]overlay=(W-w)/2:110:enable='between(t,0,{ts})'[v1]")
        cur = "[v1]"
    # image inserts — B-roll glimpses (a screenshot, a chart, a doc snippet) floated
    # over the video: [{"file","start","end","x","y"}] in OUTPUT seconds. 0.15s alpha
    # fades in/out; applied before the ass filter so captions always draw on top.
    ins_base = n + (1 if has_title else 0)
    for m_i, ins in enumerate(cfg.get("inserts", [])):
        st, en = float(ins["start"]), float(ins["end"])
        vp.append(f"[{ins_base + m_i}:v]format=rgba,"
                  f"fade=t=in:st={st:.2f}:d=0.15:alpha=1,"
                  f"fade=t=out:st={en - 0.15:.2f}:d=0.15:alpha=1[ins{m_i}]")
        vp.append(f"{cur}[ins{m_i}]overlay={ins['x']}:{ins['y']}:"
                  f"enable='between(t,{st:.2f},{en:.2f})'[vi{m_i}]")
        cur = f"[vi{m_i}]"
    vp.append(f"{cur}ass=master.ass:fontsdir=" + str(fonts_dir) + "[outv]")
    ap_, acur = [], "[0:a]"
    for j in range(1, n):
        nl = f"[xa{j}]"; ap_.append(f"{acur}[{j}:a]acrossfade=d={XF}{nl}"); acur = nl
    # With a single block the acrossfade loop never runs, so audio never enters the
    # filtergraph. Map the input stream directly (0:a, no brackets) — a bracketed
    # "[0:a]" would be read as a filtergraph label that doesn't exist and ffmpeg aborts.
    amap = acur if n > 1 else "0:a"
    fc = ";".join(vp + ap_)

    crf = "20" if preview else "18"
    tag = f"_{cfg['version']}"
    prenorm = edit / (f"preview{tag}.prenorm.mp4" if preview else f"final{tag}.prenorm.mp4")
    cmd = ["ffmpeg", "-y"]
    for bf in bfiles:
        cmd += ["-i", str(bf)]
    if has_title:
        cmd += ["-loop", "1", "-t", f"{ts}", "-i", str(edit / "title.png")]
    for ins in cfg.get("inserts", []):
        cmd += ["-loop", "1", "-t", f"{float(ins['end']) + 0.5:.2f}", "-i", str(ins["file"])]
    cmd += ["-filter_complex", fc, "-map", "[outv]", "-map", amap,
            "-c:v", "libx264", "-preset", "fast", "-crf", crf, "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(prenorm)]
    subprocess.run(cmd, check=True, cwd=str(edit))

    out = edit / (f"preview{tag}.mp4" if preview else f"final{tag}.mp4")
    if cfg["loudnorm"]:
        print("5) loudnorm -> -14 LUFS")
        get_loudnorm(cfg["video_use_helpers"])(prenorm, out, preview=preview)
        prenorm.unlink(missing_ok=True)
    else:
        prenorm.rename(out)
    print(f"DONE: {out} ({dur(out):.2f}s)")


if __name__ == "__main__":
    try:
        main()
    except RenderConfigError as e:
        sys.exit(f"ERROR: {e}")
