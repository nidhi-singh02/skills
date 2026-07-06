#!/usr/bin/env python3
"""Mechanical checks for video-to-articles deliverables.

Usage: verify_article.py <file.md> [--platform x|medium|linkedin]

Checks (all platforms):
  * zero em dashes (and no " -- " substitutes)
  * no hard-wrapped paragraphs inside copyable payload (one paragraph = one line)
  * no greeting openers ("hi guys", "hey everyone", ...)
  * every [📷 ...] or [FIGURE: ...] image marker resolves to a real file
Platform extras:
  x        launch post <= 280 chars and linkless
  medium   code fences balanced
  linkedin no markdown formatting tokens in the plain-text payload
  x/medium the paste-ready .html twin exists and its text matches the md payload
           (md is the source of truth; pass --no-twin for an intentionally md-only run)

Payload-zone heuristic: copyable payload starts after a ---- separator line (20+ dashes)
and ends at a ==== header line (20+ equals) — the pack layout documented in references/x.md.
A file with ZERO payload-zone lines FAILS (the wrap/plain-text checks would otherwise pass
vacuously). Wrapping is allowed outside those zones (scaffolding), and for indented lines,
list items, commands, env vars, and fences inside them. Heuristics can false-positive; read
the offending lines before "fixing".
"""
import argparse
import html as html_lib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

EM = "—"
CAMERA = "\U0001F4F7"
SCAFFOLD_START = ("=", "-", "•", "#", ">", "[", "(", "|", "`", "⚠", CAMERA)
CMD_PREFIX = ("git ", "cd ", "cp ", "mv ", "docker ", "curl ", "ollama ", "pip ", "npm ",
              "python", "mkdir ", "img2pdf ", "pdfunite ", "for ", "sips ")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}=")
LIST_RE = re.compile(r"^(\d+[.)]\s|[-*+]\s)")
GREET_RE = re.compile(
    r"^(hi|hey+|hello|yo|hiya|howdy|sup|greetings|good\s+(?:morning|afternoon|evening)|"
    r"what'?s\s+up|welcome)\b", re.I)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")          # [text](url)
MD_HEAD_RE = re.compile(r"^\s*#{1,6}\s")                 # any # heading (incl single #)
MD_EMPH_RE = re.compile(r"(\*\*|__|(?<![\w*])\*[^*\s][^*]*\*(?![\w*])"
                        r"|(?<![\w_])_[^_\s][^_]*_(?![\w_]))")   # bold or *italic*/_italic_
MARKER_RE = re.compile(r"\[" + CAMERA + r"(.*?)\]", re.S)
FIGURE_RE = re.compile(r"\[FIGURE:(.*?)\]", re.S | re.I)
PATH_RE = re.compile(r"[\w./-]+\.(?:png|jpe?g|webp|gif)", re.I)


class _HTMLText(HTMLParser):
    """Visible text of the html twin; skips script/style and the Copy-button chrome."""
    SKIP = {"script", "style", "button"}

    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def _norm(s: str) -> str:
    """Normalize md/html text so identical prose compares equal across formats."""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)   # md link -> its text
    s = s.replace("**", "").replace("`", "")
    s = html_lib.unescape(s)
    s = re.sub(r"[‘’]", "'", s)            # curly -> straight quotes
    s = re.sub(r"[“”]", '"', s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([.,;:!?)\]])", r"\1", s)        # tag-boundary joins add spaces
    s = re.sub(r"([(\[])\s+", r"\1", s)              # around punctuation; strip them
    return s.strip().lower()


def is_scaffold(line: str) -> bool:
    if not line or line[0] in (" ", "\t"):
        return True
    if line.startswith(SCAFFOLD_START):
        return True
    if re.match(r"^[A-Z][A-Z0-9]{2,}(\s|:|$)", line):   # ALL-CAPS pack labels ("BODY (…)")
        return True
    if LIST_RE.match(line) or ENV_RE.match(line):
        return True
    return line.lower().startswith(CMD_PREFIX)


def payload_zones(lines):
    """Yield (lineno, line) for lines inside payload zones."""
    inside = False
    fence = False
    for i, line in enumerate(lines, 1):
        s = line.rstrip("\n")
        if re.match(r"^-{20,}\s*$", s):
            inside = True
            continue
        if re.match(r"^={20,}\s*$", s):
            inside = False
            continue
        if s.strip().startswith("```"):
            fence = not fence
            continue
        if inside and not fence:
            yield i, s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--platform", choices=["x", "medium", "linkedin"], default=None)
    ap.add_argument("--no-twin", action="store_true",
                    help="skip the html-twin parity check (intentionally md-only run)")
    args = ap.parse_args()

    if not args.file.exists():
        print("verify_article.py: file not found: %s" % args.file)
        return 1
    text = args.file.read_text(encoding="utf-8")
    lines = text.splitlines()
    plat = args.platform or ("x" if "x-article" in args.file.name
                             else "medium" if "medium" in args.file.name
                             else "linkedin" if "linkedin" in args.file.name else "x")
    fails, ok = [], []

    # 1. em dashes
    em_lines = [i for i, l in enumerate(lines, 1) if EM in l or " -- " in l]
    (fails if em_lines else ok).append(
        "em dashes: " + ("FOUND at lines " + str(em_lines[:10]) if em_lines else "0"))

    # 2. hard-wrapped paragraphs in payload
    wraps = []
    zone = list(payload_zones(lines))
    if not zone:
        fails.append("payload zones: NONE found — copyable payload must sit between a ----"
                     " separator line (20+ dashes) and a ==== header line (20+ equals); see the"
                     " pack layout in references/x.md (wrap/plain-text checks cannot run)")
    for (n1, a), (n2, b) in zip(zone, zone[1:]):
        if n2 != n1 + 1 or not a.strip() or not b.strip():
            continue
        if is_scaffold(a) or is_scaffold(b):
            continue
        if " " not in a.strip() or " " not in b.strip():
            continue
        if a.rstrip().endswith((".", "!", "?", ":", ")", '"', "”")):
            continue
        wraps.append(n1)
    (fails if wraps else ok).append(
        "wrapped paragraphs: " + ("suspected at lines " + str(wraps[:10]) if wraps else "none"))

    # 3. greeting opener — check the opener line of each payload zone, not the whole
    # file, so a greeting quoted in a scaffolding note doesn't false-fail.
    greet = None
    inside = fresh = False
    for l in lines:
        s = l.rstrip("\n")
        if re.match(r"^-{20,}\s*$", s):
            inside = True; fresh = True; continue
        if re.match(r"^={20,}\s*$", s):
            inside = False; continue
        if inside and fresh and s.strip() and not is_scaffold(s):
            fresh = False
            mm = GREET_RE.match(s.strip())
            if mm:
                greet = mm.group(0); break
    (fails if greet else ok).append(
        "greeting opener: " + ("FOUND (" + greet + ")" if greet else "none"))

    # 4. image markers resolve
    missing = []
    for m in list(MARKER_RE.finditer(text)) + list(FIGURE_RE.finditer(text)):
        pm = PATH_RE.search(m.group(1))
        if not pm:
            continue
        rel = pm.group(0)
        roots = [args.file.parent, args.file.parent.parent, Path.cwd()]
        if not any((r / rel).exists() for r in roots):
            missing.append(rel)
    (fails if missing else ok).append(
        "image markers: " + ("MISSING " + str(missing) if missing else "all resolve"))

    # platform extras
    if plat == "x":
        m = re.search(r"^[ \t]*(?:#{1,6}\s*)?1[.)]\s*LAUNCH POST[^\n]*\n(?:=+\n)?"
                      r"(.*?)(?=^={4,}\s*$|^[ \t]*(?:#{1,6}\s*)?2[.)]\s|\Z)", text, re.S | re.M)
        if m:
            body = "\n".join(l for l in m.group(1).splitlines()
                             if l.strip() and not l.strip().startswith(("(", "=", "-")))
            post = "\n\n".join(p for p in body.split("\n") if p.strip())
            n = len(post)
            has_link = "http" in post.lower()
            bad = n > 280 or n == 0 or has_link
            (fails if bad else ok).append(
                "launch post: %d chars, link=%s (limit 280, nonzero, linkless)"
                % (n, "YES" if has_link else "no"))
        else:
            fails.append("launch post: section not found (expected a '1) LAUNCH POST' label; "
                         "see the pack layout in references/x.md)")
    elif plat == "medium":
        fences = sum(1 for l in lines if l.strip().startswith("```"))
        (fails if fences % 2 else ok).append(
            "code fences: %d markers (%s)" % (fences, "UNBALANCED" if fences % 2 else "balanced"))
    elif plat == "linkedin":
        fmt = [i for i, l in payload_zones(lines)
               if MD_HEAD_RE.match(l) or MD_EMPH_RE.search(l) or MD_LINK_RE.search(l)]
        (fails if fmt else ok).append(
            "plain-text payload: " + ("markdown tokens at " + str(fmt[:10]) if fmt else "clean"))

    # 5. html twin parity (x/medium ship a paste-ready .html whose text mirrors the md)
    if plat in ("x", "medium") and not args.no_twin:
        twin = args.file.with_suffix(".html")
        if not twin.exists():
            fails.append("html twin: %s not found (pass --no-twin if intentionally md-only)"
                         % twin.name)
        else:
            p = _HTMLText()
            p.feed(twin.read_text(encoding="utf-8"))
            hay = _norm(" ".join(p.parts))
            drift = [n for n, l in payload_zones(lines)
                     if not is_scaffold(l) and len(_norm(l)) > 25 and _norm(l) not in hay]
            (fails if drift else ok).append(
                "html twin parity: " + ("md paragraphs missing from html at lines "
                                        + str(drift[:10]) if drift else "in sync"))

    print("verify_article.py · %s · platform=%s" % (args.file.name, plat))
    for line in ok:
        print("  PASS  " + line)
    for line in fails:
        print("  FAIL  " + line)
    print("result: " + ("FAIL" if fails else "PASS"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
