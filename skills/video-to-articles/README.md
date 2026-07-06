# video-to-articles

A [Claude Code](https://claude.com/claude-code) skill that turns a recorded video into ready-to-post
social content, written in your own voice:

- an **X (Twitter) Article** pack (launch post + replies + the article),
- a **Medium** article (SEO title, real code blocks, captioned figures),
- a **LinkedIn** post (plus an Article reuse),

each with a fresh, on-brand **cover image**. Everything is optimized for how each platform actually
distributes content, and written to sound like a person, not an AI.

Works for **any** video: a build-along, a how-to, a product demo, an opinion essay, a talking-head,
a vlog. It reads the transcript (and screenshots, if the video has any), figures out the video's
shape, and writes accordingly. It produces written articles/posts only; a swipeable LinkedIn
carousel is a separate skill.

## What it produces

| Platform | Output | Notes |
|---|---|---|
| X / Twitter | `x-article.md` + `x-article.html` + cover | linkless launch post, any link in a reply; the html twin pastes with headings/bold already applied |
| Medium | `medium-article.md` + `medium-article.html` + cover | SEO title/subtitle, real fenced code blocks, inline links, tags; html twin pastes formatted (also into LinkedIn Articles) |
| LinkedIn | `linkedin-post.md` | native post (5x the reach of Articles), first-comment link, multi-image; plain text, so no twin needed |

Every deliverable keeps one paragraph per line, so copying never leaves stray mid-sentence line
breaks to repair. `scripts/verify_article.py` enforces this plus the other invariants.

`SKILL.md` closes with one illustrative example (a dev build-along) showing the *shape* only.
`examples/` starts empty on purpose; the skill offers to save your real runs there over time (see
`examples/README.md`).

## Requirements

- **Claude Code** (this is a Skill; it loads via the Skill tool).
- **The Playwright MCP browser**, used to render the cover images headlessly. One-line setup:
  `claude mcp add playwright -- npx @playwright/mcp@latest` (docs: https://github.com/microsoft/playwright-mcp).
  Optional: without it, the skill still writes everything and hands you a finished `cover.html` to
  screenshot yourself.
- **Python 3** for `scripts/verify_article.py` (stdlib only).
- **`curl`** for the cover-render server health-check (`scripts/render_cover.sh`, a non-fatal
  status probe on every X/Medium cover) and for `scripts/fetch_logo.sh` (diagram/brand-logo covers).

## Install

Clone the repo, then copy this folder into your Claude Code skills directory (the skill name comes
from the folder name):

```bash
git clone <repo-url>   # this repository
cp -r video-to-articles ~/.claude/skills/
```

## Usage

Point it at a video's transcript (and screenshots, if any) and say where it's going:

- "turn this video into a twitter article"
- "write a medium article / blog post from my video"
- "write a linkedin post from this recording"

The skill reads the transcript, confirms the true story with you (accuracy first), picks the arc
that fits the video's shape, writes in your voice, then renders and shows you the cover.

## Voice

**The skill has no house style.** It matches YOUR writing voice: it reads a voice profile from
`~/.claude/voice-profile.md` if one exists; if not, it asks you for 2-3 real posts, infers your
voice, and offers to save the profile so future runs are zero-setup. A voice profile is a short
markdown file describing how you write; see `assets/voice-profile-template.md` for the shape. Over
time the profile's `## Learned` section accumulates what you accepted, rejected, and what your
audience actually rewarded (via the post-launch retro in `references/retro.md`), so output quality
compounds run over run.

## Covers

Most covers are **text-only** (`assets/cover-text-template.html`, the default, works light or dark).
Use `cover-template.html` only when the video has a real A→B→C system to diagram; use
`cover-medium-template.html` for Medium's centered featured image. All templates retheme through CSS
variables (`--bg`, `--accent`, `--display`), so a non-dev topic is a couple of edits away from the
dev default. See `references/cover-render.md`.

## Repo structure

```
SKILL.md                         the skill: workflow + archetypes + rules (versioned)
README.md                        this file
CHANGELOG.md                     what changed between versions
references/
  x.md                           X pack: launch post, replies, article, checklist
  medium.md                      Medium-specific format
  linkedin.md                    LinkedIn post + article
  cover-render.md                render + imagery + font guidance
  retro.md                       post-launch retro: measure, log, compound
evals/
  evals.json                     3 archetype test prompts + assertions
  fixtures/                      per-eval input files (transcripts + placeholder screenshots)
scripts/
  verify_article.py              mechanical checks (em dashes, wraps, markers, limits)
  render_cover.sh                serve / collect / stop helpers for the headless render
  fetch_logo.sh                  brand-mark fetch waterfall for diagram covers
assets/
  cover-text-template.html       text-only cover (the default)
  cover-template.html            dark cover with optional A→B→C diagram
  cover-medium-template.html     centered 1600x840 Medium featured image
  departure.woff2                Departure Mono (bundled, MIT)
  DepartureMono-LICENSE.txt      font license
  voice-profile-template.md      voice profile shape
examples/                        your real runs land here (starts with only its README)
LICENSE                          MIT
.gitignore                       OS + render scratch
```

## Credits

Cover font: **Departure Mono** by Helena Zhang & Tobias Fried (MIT). https://departuremono.com

## License

MIT. See `LICENSE`. The bundled font keeps its own MIT license in `assets/DepartureMono-LICENSE.txt`.
