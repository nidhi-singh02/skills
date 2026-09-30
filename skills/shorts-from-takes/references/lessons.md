# Lessons: things that cost a re-render

Apply these up front. Helper scripts live in `scripts/`.

## Cuts and audio
1. **Snap every cut into real silence** (`snap_cuts.py snap <src> <t>`, 10ms RMS). Word timestamps are ±50ms; a cut on a soft consonant makes short sentences sound clipped.
2. **Use ~8ms audio fades**, not 30ms. Long fades eat consonants at cut edges.
3. **Check for mic dropouts before picking takes** (`snap_cuts.py dropout <src>`). A word can be silent even though the lips move (hand over the mic). If a CTA keyword is missing from every take, splice it from another take and back it with an on-screen card.
4. **A take that starts as the mic reconnects** has a clipped first word; don't start a segment there.
5. **Level per segment** (`snap_cuts.py levels`, then the segment `gain`). Global loudnorm can't fix imbalance between segments. Finish with 2-pass loudnorm.
6. **If you add SFX, trim to under a second.** A long "whoosh" sample can be continuous noise that makes the voice seem to drop several dB.
7. **Speed per segment:** talking heads can take ~1.2x (atempo keeps pitch); screen recordings stay at native speed.

## Verification
8. **Re-transcribe at 1x** (`verify_1x.py`). Speech-to-text often misreads sped-up audio, so a "wrong" word at 1.2x may be fine, and a right-looking one can hide a clipped word.
9. **Frame check** (`frame_check.py final.mp4 timeline.json out/`): frames at every cut and the first/last 2s. Look for captions over the face, title/UI overlap, clipped logos, frozen frames.

## Visuals
10. **Virtual camera** (`camera.py`) for landscape screen recordings: keyframed pan/zoom over a blurred fill keeps UI readable in 9:16. Check each keyframe so text isn't cropped.
11. **Transition at every cut**, especially between screen footage and a talking head (xfade 0.25-0.5s).
12. **Avoid a frozen or silent face at the end.** End on a logo or end screen under the CTA.
13. **Captions** (`overlay_kit.py`): keep them off the face and in the lower third. Clamp each cue's end to the next cue's start minus ~0.04s, or two cues draw at once.
14. **Titles over UI need a dark gradient scrim.** Pick title colours from the video's palette.
15. **CTA card:** slide the card in, slam the keyword in on the *spoken* word, then show the follow prompt.
16. **Missing glyphs** (arrows etc.) in a font: draw the shape by hand.
17. Frame extraction at the exact end timestamp fails; use end - 0.5s. Dump frames as PNG (mjpeg rejects non-full-range video).

## Workflow
18. **Get the script approved before rendering.** Restructure for retention: hook first, payoff, CTA last.
19. **Check the seams for repeated words** across joined segments.
20. **Offer visual options** (caption styles, covers) as a sheet and let the creator choose.
