#!/usr/bin/env python3
"""Cover building blocks (1080x1920). Import; see SKILL.md for the standard recipe.

Key rule: sticker boxes have EQUAL padding on all four sides, measured from the
glyph INK bbox (textbbox), never from font metrics.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
# Fonts are shared with the sibling shorts-from-takes skill (SIL OFL, licences in its assets/font-licenses).
FONTS = Path(__file__).resolve().parent.parent.parent / "shorts-from-takes" / "assets" / "fonts"
W, H = 1080, 1920
ANTON, POP = str(FONTS / "Anton-Regular.ttf"), str(FONTS / "Montserrat-Black.ttf")
CORAL, SAND, NAVY, VIOLET, PEACH = (255, 107, 87), (242, 217, 176), (22, 32, 74), (169, 139, 255), (255, 177, 153)
INK, DEEP = (12, 10, 30), (10, 14, 40)

def font(p, s): return ImageFont.truetype(p, s)

def face_crop(path, zoom=1.75, cy_frac=0.33):
    """Portrait frame -> 9:16 crop centred on the face region."""
    im = Image.open(path).convert("RGB"); cw = int(im.width / zoom); ch = int(cw * 16 / 9)
    cx, cy = im.width // 2, int(im.height * cy_frac); y0 = max(0, min(im.height - ch, cy - ch // 2))
    return im.crop((cx - cw // 2, y0, cx + cw // 2, y0 + ch)).resize((W, H), Image.LANCZOS).convert("RGBA")

def vgrad(img, y0, y1, col, a0, a1):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(y0, y1): d.line((0, y, img.width, y), fill=col + (int(a0 + (a1 - a0) * (y - y0) / max(1, y1 - y0)),))
    return Image.alpha_composite(img.convert("RGBA"), ov)

def framed(im, src, box, size, pos, outline, radius=30):
    """Rounded, shadowed, outlined screenshot card (src crop `box` -> `size` at `pos`)."""
    card = Image.open(src).convert("RGB").crop(box).resize(size, Image.LANCZOS)
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    sh = Image.new("RGBA", (size[0] + 80, size[1] + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 50, size[0] + 40, size[1] + 50), radius=radius, fill=(0, 0, 0, 160))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (pos[0] - 40, pos[1] - 40)); im.paste(card, pos, m)
    ImageDraw.Draw(im).rounded_rectangle((pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]), radius=radius, outline=outline, width=5)

def sticker(text, f, bg, fg, logo=None, logo_sz=0, pad=46):
    """Rounded label, EQUAL padding all sides (ink bbox). logo = RGBA image placed inline left of text."""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10))); x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    tw, th = x1 - x0, y1 - y0; gap = int(pad * 0.6) if logo is not None else 0
    w = tw + 2 * pad + (logo_sz + gap if logo is not None else 0); h = max(th, logo_sz) + 2 * pad
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(st); d.rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=bg)
    x = pad
    if logo is not None:
        st.alpha_composite(logo.resize((logo_sz, logo_sz), Image.LANCZOS), (x, (h - logo_sz) // 2)); x += logo_sz + gap
    d.text((x - x0, (h - th) // 2 - y0), text, font=f, fill=fg); return st

def place(im, st, cx, y, angle):
    r = st.rotate(angle, resample=Image.BICUBIC, expand=True); im.alpha_composite(r, (int(cx - r.width / 2), int(y))); return r

def standard_cover(face, screen, screen_box, top_text, sub_text, logo=None, out="cover.png"):
    """Default cover: face + tilted sand sticker (logo inline) + coral sticker + screenshot card."""
    im = vgrad(face_crop(face), 0, 560, DEEP, 235, 0); im = vgrad(im, 1250, H, DEEP, 0, 240)
    framed(im, screen, screen_box, (880, 389), ((W - 880) // 2, 1330), VIOLET)
    place(im, sticker(top_text, font(ANTON, 190), SAND, INK, logo=logo, logo_sz=150 if logo is not None else 0), W / 2, 210, -4)
    place(im, sticker(sub_text, font(ANTON, 130), CORAL, INK), W / 2 + 10, 490, 3)
    im.convert("RGB").save(out); return out

def safe_preview(cover, out="cover_safe.png"):
    """Show the centre 4:5 Instagram-grid crop + the 3:4/1:1 crops so text isn't cut off."""
    im = Image.open(cover).convert("RGB"); w, h = im.size; ch = int(w * 5 / 4); y0 = (h - ch) // 2
    crop = im.crop((0, y0, w, y0 + ch)); sheet = Image.new("RGB", (w + ch * w // ch, h), (20, 20, 20))
    sheet.paste(im, (0, 0)); sheet.paste(crop, (w, y0)); d = ImageDraw.Draw(sheet)
    d.rectangle((0, y0, w, y0 + ch), outline=(255, 80, 80), width=6); sheet.save(out); return out
