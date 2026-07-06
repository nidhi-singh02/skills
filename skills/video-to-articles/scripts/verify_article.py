#!/usr/bin/env python3
"""Mechanical checks for video-to-articles deliverables.

Usage: verify_article.py <file.md> [--platform x|medium|linkedin]

Checks (all platforms):
  * zero em dashes (— , spaced " -- ", word--word, or one-sided word-- / --word) in prose;
    leaves --flags, <!-- -->, fenced code blocks, URLs, and `inline code` spans alone
  * no hard-wrapped paragraphs inside copyable payload (one paragraph = one line); this now
    also covers space-less CJK/Thai prose and treats non-Latin sentence enders (danda ।॥,
    Urdu ۔, Arabic ؟, ...) as terminal, though it stays a heuristic (eyeball non-Latin runs)
  * no greeting openers ("hi guys", "hey there", "good morning", "what's up", ...); a narrow
    heuristic, not a guarantee — read a flagged line before trusting it
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
# Known ALL-CAPS pack labels only (optionally numbered): treated as scaffolding.
# Kept narrow so a wrapped sentence starting with a tech acronym (API, SEO, RAG,
# SaaS, CEO ...) is NOT mistaken for a section header and skipped by the wrap check.
PACK_LABEL_RE = re.compile(
    r"^(?:#{1,6}\s*)?\d*[.)]?\s*"
    r"(LAUNCH POST|REPLY(?:\s+[A-Z])?|BODY|TITLE|SUBTITLE|TAGS|FEATURED IMAGE|"
    r"POSTING CHECKLIST|THE ARTICLE|COVER)\b")
GREET_RE = re.compile(
    r"^(?:hi|hey|hello|yo)\s+(?:guys|everyone|all|folks|friends|there|team|gang|peeps|y'?all|"
    r"chat|fam)\b"
    r"|^(?:good\s+(?:morning|afternoon|evening))\b"
    r"|^what'?s\s+up\b",
    re.I | re.M)
MARKER_RE = re.compile(r"\[" + CAMERA + r"(.*?)\]", re.S)
# "--" used as clause punctuation: word--word (no spaces) or fully-spaced word -- word.
# Excludes --flags: a space *before* --word (e.g. "run --build") is a flag, not a dash,
# so only the space-less word--word or the symmetric spaced form " -- " count. <!-- --> is
# stripped in _prose_only before this runs.
DASH_SUB_RE = re.compile(r"\w--\w")
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


_CJK_RE = re.compile(
    r"[ᄀ-ᇿ⺀-〾ぁ-㏿㐀-䶿一-鿿"
    r"ꀀ-꓏가-힣豈-﫿＀-｠฀-๿]")


def _has_cjk(s: str) -> bool:
    """True if the line carries CJK / Japanese / Korean / Thai (space-less) script."""
    return bool(_CJK_RE.search(s))


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
    if PACK_LABEL_RE.match(line):                       # known ALL-CAPS pack labels ("BODY (…)")
        return True
    if re.fullmatch(r"[^a-z]*[A-Z][^a-z]*", line):      # a WHOLE all-caps line (no lowercase)
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
            fence = False   # a ---- boundary resets fence state so an unbalanced
            continue        # fence in scaffolding can't leak into the payload zone
        if re.match(r"^={20,}\s*$", s):
            inside = False
            fence = False
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
    ap.add_argument("--allow-em-dash", action="store_true",
                    help="don't fail on em dashes (creator's voice profile permits them)")
    args = ap.parse_args()

    try:
        text = args.file.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as e:
        print("verify_article.py · %s" % args.file.name)
        print("  FAIL  cannot read %s: %s" % (args.file, e))
        print("result: FAIL")
        return 1
    lines = text.splitlines()
    guessed = ("x" if "x-article" in args.file.name
               else "medium" if "medium" in args.file.name
               else "linkedin" if "linkedin" in args.file.name else None)
    plat = args.platform or guessed or "x"
    if args.platform is None and guessed is None:
        print("note: could not infer platform from filename; defaulting to 'x'. "
              "Pass --platform to be explicit.")
    fails, ok = [], []

    # 1. em dashes: the literal — and the "--" substitute used as punctuation
    #    (spaced " -- ", or word--word). Shell flags like --build and <!-- --> are left
    #    alone, and so are fenced code blocks, URLs, and `inline code` spans — a literal
    #    — or word--word inside code or a link slug is legitimate, not a prose em dash.
    def _prose_only(line: str) -> str:
        line = re.sub(r"<!--.*?-->", " ", line, flags=re.S)  # strip HTML comments
        line = re.sub(r"`[^`]*`", " ", line)              # strip `inline code`
        line = re.sub(r"https?://\S+", " ", line)         # strip URLs (slugs may have --)
        return line
    em_lines = []
    _fence = False
    for i, l in enumerate(lines, 1):
        if re.match(r"^-{20,}\s*$", l) or re.match(r"^={20,}\s*$", l):
            _fence = False   # a ----/==== boundary resets fence state so an unbalanced
            continue          # fence in scaffolding can't suppress detection in the payload
        if l.strip().startswith("```"):
            _fence = not _fence
            continue
        if _fence:
            continue
        p = _prose_only(l)
        if EM in p or " -- " in p or DASH_SUB_RE.search(p):
            em_lines.append(i)
    if em_lines and args.allow_em_dash:
        ok.append("em dashes: FOUND at lines " + str(em_lines[:10]) + " (allowed by --allow-em-dash)")
    else:
        (fails if em_lines else ok).append(
            "em dashes: " + ("FOUND at lines " + str(em_lines[:10]) if em_lines else "0"))

    # 2. hard-wrapped paragraphs in payload
    wraps = []
    zone = list(payload_zones(lines))
    if not zone:
        fails.append("payload zones: NONE found — copyable payload must sit between a ----"
                     " separator line (20+ dashes) and a ==== header line (20+ equals); see the"
                     " pack layout in references/x.md (wrap/plain-text checks cannot run)")
    # A LAUNCH POST / REPLY is a deliberate 2-3 line hook stack, not a wrapped paragraph
    # (see references/x.md). Collect the line numbers under such a label so the wrap check
    # skips them — their stacked lines need not end in terminal punctuation.
    _STACK_LABEL_RE = re.compile(
        r"^(?:#{1,6}\s*)?\d*[.)]?\s*(?:LAUNCH POST|REPLY(?:\s+[A-Z])?)\b")
    _SECTION_LABEL_RE = re.compile(r"^(?:#{1,6}\s*)?\d+[.)]\s*[A-Z]")
    stack_lines = set()
    in_stack = False
    for n, l in enumerate(lines, 1):
        if _STACK_LABEL_RE.match(l):
            in_stack = True
        elif _SECTION_LABEL_RE.match(l) or re.match(r"^={20,}\s*$", l):
            in_stack = False
        if in_stack:
            stack_lines.add(n)
    for (n1, a), (n2, b) in zip(zone, zone[1:]):
        if n1 in stack_lines or n2 in stack_lines:
            continue
        if n2 != n1 + 1 or not a.strip() or not b.strip():
            continue
        if is_scaffold(a) or is_scaffold(b):
            continue
        # A space-less line is normally a non-prose token (a path, a slug) — skip it. But
        # CJK/Thai/Japanese prose has no spaces, so a genuinely wrapped ideographic paragraph
        # would slip through vacuously. When either line carries ideographic codepoints, keep
        # checking it; the terminal-punctuation guard below still lets legitimate sentence
        # ends pass, so false-positives stay low.
        if not (_has_cjk(a) or _has_cjk(b)):
            if " " not in a.strip() or " " not in b.strip():
                continue
        if a.rstrip().endswith((".", "!", "?", ":", ")", '"', "”",
                                "。", "！", "？", "、", "」", "）", "…",
                                "।", "॥", "۔", "؟", "։", "።")):
            continue
        wraps.append(n1)
    (fails if wraps else ok).append(
        "wrapped paragraphs: " + ("suspected at lines " + str(wraps[:10]) if wraps else "none"))

    # 3. greeting opener
    greet = GREET_RE.search(text)
    (fails if greet else ok).append(
        "greeting opener: " + ("FOUND (" + greet.group(0) + ")" if greet else "none"))

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
            # Keep only real payload lines: drop blank lines, pure separators
            # (----/====), and whole-line parenthetical scaffolding notes. Do NOT
            # drop lines that merely start with "-" or "(" — a dash-led stat line
            # or a parenthetical opener is real launch-post content.
            def _is_scaffold_note(t: str) -> bool:
                return (re.fullmatch(r"-{20,}", t) is not None
                        or re.fullmatch(r"={4,}", t) is not None
                        or re.fullmatch(r"\(.*\)", t) is not None)
            keep = [l for l in m.group(1).splitlines()
                    if l.strip() and not _is_scaffold_note(l.strip())]
            # Count the post as the user would paste it: lines joined by single
            # newlines (a "2-3 line stack" is not double-spaced).
            post = "\n".join(keep)
            n = len(post)
            # X weights most CJK ideographs and emoji as 2 units toward the 280 limit,
            # not 1 codepoint. Weight them so a near-limit non-Latin post doesn't PASS
            # here yet get rejected by X. (Approximation: CJK/full-width ranges + any
            # non-BMP codepoint, which covers emoji.)
            def _weight(ch: str) -> int:
                o = ord(ch)
                if o > 0xFFFF:
                    return 2                       # emoji and other astral chars
                if (0x1100 <= o <= 0x11FF or 0x2E80 <= o <= 0x303E
                        or 0x3041 <= o <= 0x33FF or 0x3400 <= o <= 0x4DBF
                        or 0x4E00 <= o <= 0x9FFF or 0xA000 <= o <= 0xA4CF
                        or 0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF
                        or 0xFE30 <= o <= 0xFE4F or 0xFF00 <= o <= 0xFF60
                        or 0xFFE0 <= o <= 0xFFE6):
                    return 2                       # CJK / full-width ideographs
                return 1
            weighted = sum(_weight(c) for c in post)
            # X auto-linkifies bare domains too, so catch scheme-less links (example.com/x,
            # www.example.io) not just http(s). Tolerate sentence enders like "e.g." / "etc."
            # by requiring a known TLD followed by a slash or a word boundary.
            has_link = bool(
                re.search(r"https?://|www\.", post, re.I)
                or re.search(r"\b[\w-]+\.(?:com|io|dev|ai|net|org|co|app|sh|xyz|me|gg)"
                             r"(?:/|\b)", post, re.I))
            bad = weighted > 280 or n == 0 or has_link
            note = "" if weighted == n else " (%d codepoints)" % n
            (fails if bad else ok).append(
                "launch post: %d weighted chars%s, link=%s (X limit 280 counts CJK/emoji as 2, "
                "nonzero, linkless)" % (weighted, note, "YES" if has_link else "no"))
        else:
            fails.append("launch post: section not found (expected a '1) LAUNCH POST' label; "
                         "see the pack layout in references/x.md)")
    elif plat == "medium":
        fences = sum(1 for l in lines if l.strip().startswith("```"))
        (fails if fences % 2 else ok).append(
            "code fences: %d markers (%s)" % (fences, "UNBALANCED" if fences % 2 else "balanced"))
    elif plat == "linkedin":
        # LinkedIn's feed is the paste target (no html twin), so any surviving markdown
        # syntax pastes literally. Flag headings, bold, markdown links [text](url), and
        # _italic_ runs. Require ** to be a balanced pair before flagging so exponent
        # notation like 2**8 is not a false positive.
        _MDLINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")
        _ITALIC_RE = re.compile(r"(?<!\w)_[^_]+_(?!\w)")

        def _has_md(l: str) -> bool:
            if l.startswith("## "):
                return True
            if l.count("**") >= 2:
                return True
            if _MDLINK_RE.search(l):
                return True
            return bool(_ITALIC_RE.search(l))
        fmt = [i for i, l in payload_zones(lines) if _has_md(l)]
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
            # On X, the .html twin carries only "4) THE ARTICLE" body — the launch post and
            # replies are pasted into X's native composer separately and are correctly NOT in
            # the twin (see references/x.md). Scope parity to the article section so those
            # payload zones aren't flagged as drift. Medium's twin is the whole body, so no
            # anchor there.
            body_start = 0
            if plat == "x":
                for n, l in enumerate(lines, 1):
                    if re.match(r"^[ \t]*(?:#{1,6}\s*)?4[.)]\s*THE ARTICLE\b", l):
                        body_start = n
                        break
            drift = [n for n, l in payload_zones(lines)
                     if n > body_start and not is_scaffold(l)
                     and len(_norm(l)) > 60 and _norm(l) not in hay]
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
