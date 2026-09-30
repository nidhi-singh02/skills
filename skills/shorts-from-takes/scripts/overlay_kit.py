#!/usr/bin/env python3
"""Reusable PIL overlay drawers . Import, don't run.

    from overlay_kit import Kit
    kit = Kit(font_path="Poppins-ExtraBold.ttf", big_font="Anton-Regular.ttf", preset="D")
    img = Image.new("RGBA", (1080, 1920), (0,0,0,0))
    kit.caption(img, cue, t)      # cue = [{"t": "word", "a": start_s, "b": end_s}, ...] (<=3 words)
    kit.title(img, t, lines, fade_out_at)
    kit.cta(img, t, cta_t, keyword_t, keyword="GUIDE")
Render one RGBA PNG per frame, then overlay via ffmpeg (see references/lessons.md).
Keep captions off the speaker's face: cap_y defaults to the lower third (1330).
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# caption presets: (text colour, active-word colour, pill background RGBA). Add your own.
PRESETS = {
    "D": ((255, 177, 153), (255, 107, 87), (22, 32, 74, 214)),    # peach / coral on navy
    "A": ((214, 200, 255), (169, 139, 255), (14, 12, 34, 220)),   # lavender / violet on ink
    "B": ((242, 217, 176), (255, 107, 87), (12, 10, 30, 214)),    # sand / coral on ink
    "C": ((160, 235, 220), (255, 177, 153), (16, 40, 52, 214)),   # mint / peach on teal
}
SAND, VIOLET, CORAL, NAVY, PEACH = (242, 217, 176), (169, 139, 255), (255, 107, 87), (22, 32, 74), (255, 177, 153)

def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

class Kit:
    def __init__(self, font_path, big_font, preset="D", W=1080, H=1920, cap_y=1330):
        self.W, self.H, self.cap_y = W, H, cap_y
        self.txt, self.act, self.pill = PRESETS[preset]
        self.fcap = ImageFont.truetype(font_path, 80); self.ftitle = ImageFont.truetype(font_path, 70)
        self.fsm = ImageFont.truetype(font_path, 56); self.fbig = ImageFont.truetype(big_font, 190)

    def cues(self, words, cta_index=None, max_words=3, gap=0.35, break_after=()):
        """Group word dicts into <=3-word cues; break on gaps/punctuation words; stop before CTA."""
        out, cur = [], []
        for w in words[:cta_index]:
            if cur and (len(cur) >= max_words or w["a"] - cur[-1]["b"] > gap): out.append(cur); cur = []
            cur.append(w)
            if w["t"] in break_after: out.append(cur); cur = []
        if cur: out.append(cur)
        return out

    def visible(self, cues, t):
        """Cue to draw at time t. End clamped to next cue start - 0.04 (prevents double-draw)."""
        for c in cues:
            end = c[-1]["b"] + 0.15
            nxt = [x[0]["a"] for x in cues if x[0]["a"] > c[0]["a"]]
            if nxt: end = min(end, nxt[0] - 0.04)
            if c[0]["a"] - 0.02 <= t < end: return c
        return None

    def caption(self, img, cue, t):
        d = ImageDraw.Draw(img); words = [w["t"] for w in cue]; sp = 22
        ws = [d.textlength(x, font=self.fcap) for x in words]; tw = sum(ws) + sp * (len(words) - 1)
        k = 0.86 + 0.14 * ease((t - cue[0]["a"]) / 0.12)
        layer = Image.new("RGBA", (int(tw) + 90, 150), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle((0, 0, layer.width - 1, 149), radius=36, fill=self.pill)
        x = 45
        for w, wl, word in zip(cue, ws, words):
            ld.text((x, 20), word, font=self.fcap, fill=(self.act if w["a"] - 0.03 <= t else self.txt) + (255,)); x += wl + sp
        if k < 1: layer = layer.resize((int(layer.width * k), int(layer.height * k)), Image.LANCZOS)
        img.alpha_composite(layer, ((self.W - layer.width) // 2, self.cap_y - layer.height // 2))

    def title(self, img, t, lines, fade_out_at, y=300, hi_color=VIOLET):
        """lines = [[(text, color), ...], ...]. Dark scrim behind so it never fights the UI.
        Pick colours that match the video's palette."""
        a = min(ease((t - 0.15) / 0.35), 1 - ease((t - fade_out_at) / 0.3))
        if a <= 0: return
        scrim = Image.new("RGBA", (self.W, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(scrim)
        for yy in range(520):
            sd.line((0, yy, self.W, yy), fill=(8, 6, 20, int(190 * a * min(1, (520 - yy) / 200) * min(1, (yy + 80) / 200))))
        img.alpha_composite(scrim, (0, y - 120))
        layer = Image.new("RGBA", (self.W, 60 + 92 * len(lines)), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); yy = 30
        for ln in lines:
            tw = sum(d.textlength(s, font=self.ftitle) for s, _ in ln); x = (self.W - tw) / 2
            for s, c in ln:
                d.text((x, yy), s, font=self.ftitle, fill=c + (255,), stroke_width=3, stroke_fill=(12, 10, 30, 255)); x += d.textlength(s, font=self.ftitle)
            yy += 92
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(layer, (0, y + int(30 * (1 - ease((t - 0.15) / 0.35)))))

    def cta(self, img, t, cta_t, keyword_t, keyword="GUIDE", lead="comment", tail="+ follow for more", y0=1120):
        """Card slides up at cta_t, keyword slams in on the SPOKEN word (keyword_t), follow pill after."""
        p = (t - cta_t) / 0.35
        if p < 0: return
        e = ease(p); cw, ch = 860, 520
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=48, fill=NAVY + (232,), outline=VIOLET + (255,), width=5)
        d.text(((cw - d.textlength(lead, font=self.fsm)) / 2, 40), lead, font=self.fsm, fill=PEACH + (255,))
        if t >= keyword_t - 0.05:
            k = 1.25 - 0.25 * ease((t - keyword_t) / 0.15)
            lay = Image.new("RGBA", (cw, 240), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); s = f"“{keyword}”"
            ld.text(((cw - ld.textlength(s, font=self.fbig)) / 2, 0), s, font=self.fbig, fill=CORAL + (255,))
            lay = lay.resize((int(cw * k), int(240 * k)), Image.LANCZOS)
            card.alpha_composite(lay, ((cw - lay.width) // 2, 118 - (lay.height - 240) // 2))
        ft = keyword_t + 0.45
        if t >= ft:
            fa = ease((t - ft) / 0.25); pill = Image.new("RGBA", (cw, 110), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
            tw = pd.textlength(tail, font=self.fsm)
            pd.rounded_rectangle(((cw - tw) / 2 - 36, 8, (cw + tw) / 2 + 36, 102), radius=46, fill=VIOLET + (255,))
            pd.text(((cw - tw) / 2, 18), tail, font=self.fsm, fill=(18, 14, 40, 255))
            pill.putalpha(pill.getchannel("A").point(lambda v: int(v * fa))); card.alpha_composite(pill, (0, 380 + int(20 * (1 - fa))))
        card.putalpha(card.getchannel("A").point(lambda v: int(v * e)))
        img.alpha_composite(card, ((self.W - cw) // 2, y0 + int(160 * (1 - e))))
