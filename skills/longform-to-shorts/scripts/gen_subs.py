#!/usr/bin/env python3
"""
Map word-level Whisper timings onto each Short's EDITED timeline and emit SRTs.

Usage: edit CLIPS below (source seconds, in output order, one (start,end) per kept
segment; gaps between segments = removed clauses), point WORDS at your words.json,
then: python3 gen_subs.py   ->   writes shorts/<name>.srt

ALWAYS hand-review the output SRTs afterward. Whisper drops words, mis-hears names
(Meetily/Mintly, shadcn/"Chad Cien", slop/"slob"), and sometimes duplicates words.
The auto output is a timing scaffold, not postable copy.
"""
import json, re

WORDS = '_ref/words.json'
OUTDIR = 'shorts'

# name -> [(src_start, src_end), ...]  segments in output order (audio timeline)
CLIPS = {
    # 'agent-reach': [(44.5, 91.5)],
    # 'taste':       [(566.7, 589.5), (592.05, 604.1)],   # gap = removed clause
}

# systematic Whisper fixes (extend per project)
FIX = [
    ('Mintly', 'Meetily'), ('Mintley', 'Meetily'),
    ('Chad Cien', 'shadcn'), ('Chad Cian', 'shadcn'), ('Chad CN', 'shadcn'),
    ('Cloud Video', 'Claude Video'), ('cloud video', 'claude-video'),
    ('slob', 'slop'),
]

def fix(t):
    for a, b in FIX:
        t = t.replace(a, b)
    return re.sub(r'\s+', ' ', t).strip()

def out_time(src, segs):
    off = 0.0
    for (s, e) in segs:
        if s <= src < e:
            return off + (src - s)
        off += (e - s)
    return None  # word is in a removed gap -> dropped

def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')

def main():
    words = json.load(open(WORDS))['words']
    for name, segs in CLIPS.items():
        ws = []
        for w in words:
            st = w['start']; en = w.get('end', st + 0.3)
            ot = out_time(st, segs)
            if ot is None:
                continue
            ws.append([ot, ot + (en - st), w['word'].strip()])
        ws.sort()
        # phrase chunk: break on trailing punctuation, or >=6 words, or >=2.3s
        cues, cur = [], []
        for ot, oe, word in ws:
            cur.append([ot, oe, word])
            span = cur[-1][1] - cur[0][0]
            if (word.endswith(('.', '?', '!', ',', ';', ':')) and len(cur) >= 2) or len(cur) >= 6 or span >= 2.3:
                cues.append(cur); cur = []
        if cur:
            cues.append(cur)
        merged = []
        for c in cues:  # fold a lone trailing word into the previous cue
            if len(c) == 1 and merged:
                merged[-1].extend(c)
            else:
                merged.append(c)
        cues = merged
        out = []
        for i, c in enumerate(cues):
            st = c[0][0]; en = c[-1][1] + 0.12
            if i + 1 < len(cues):
                en = min(en, cues[i + 1][0][0] - 0.02)
            if en <= st:
                en = st + 0.4
            out.append(f"{i+1}\n{fmt(st)} --> {fmt(en)}\n{fix(' '.join(x[2] for x in c))}\n")
        open(f'{OUTDIR}/{name}.srt', 'w').write('\n'.join(out))
        print(f"{name}: {len(cues)} cues  (HAND-REVIEW THIS SRT)")

if __name__ == '__main__':
    main()
