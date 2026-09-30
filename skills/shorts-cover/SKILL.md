---
name: shorts-cover
description: >-
  Make vertical (1080x1920) cover/thumbnail options for a YouTube Short or Instagram Reel:
  find the best smiling face frame, then compose sticker-style headline covers with a brand
  logo and a product screenshot card, with a 4:5 Instagram-grid safety check. Use after a
  Short is rendered (e.g. with shorts-from-takes), or when asked for a "thumbnail", "cover",
  "cover image", or "show me smile frames".
license: MIT
compatibility: Requires ffmpeg and Python 3 with pillow and numpy; logo.py also needs resvg-py (uv run --with resvg-py).
---

# Shorts cover

Face + tilted sticker headline (optional logo inline) + a screenshot card of the product, in 1080x1920. Offer 4-6 variants and let the creator pick. Fonts are borrowed from the sibling `shorts-from-takes` skill.

## Recipe
1. **Smile finder.** `python scripts/smile_sheet.py out/smiles clip1.MOV clip2.MOV --step 0.5 --max 24` writes a numbered `smiles_sheet.png` (blurry frames dropped, rotation applied). Show it and ask which number.
2. **Logo (optional).** `uv run --with resvg-py python scripts/logo.py <official.svg url or file> logo.png`. Use the brand's official SVG (press kit or Wikimedia Commons) and check its usage guidelines; never redraw a logo.
3. **Screenshot source.** Grab the most legible frame of the product video (`ffmpeg -ss T -frames:v 1`). Confirm the text you want on the card is really on that frame; UI text can be on screen for only a fraction of a second.
4. **Compose.** `from cover_kit import standard_cover, sticker, place, framed, face_crop, vgrad`, e.g. `standard_cover(face, screen, (x0, y0, x1, y1), "HEADLINE", "SUBLINE", logo=None)`. Vary text pairs, layout, face zoom and sticker colours to get options.
5. **Safe check.** `safe_preview(cover)` shows the centre 4:5 crop the Instagram grid uses. Keep the headline inside it (the top ~15% is cropped).
6. Show all options in one preview sheet, then export the chosen PNG at full resolution.

## Rules
- Sticker boxes have equal padding on all four sides, measured from the glyph ink box (`sticker()` does this).
- Short headlines (three words or fewer per line), all caps, slight tilt.
- Take colours from the video's palette; keep text off the eyes and mouth.
- Use a real smile frame with open eyes, chosen by the creator.
- A glyph missing from the font (arrows etc.): draw it with shapes.
