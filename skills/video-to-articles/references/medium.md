# Producing a Medium version

Same story and voice as the X Article, but Medium is **search-driven and evergreen**, not
feed-driven. That flips several format decisions. Deliver `blog/medium-article.md` plus the
paste-ready twin `blog/medium-article.html` (see "Copy-paste fidelity" in SKILL.md; the same html
also pastes into a LinkedIn Article editor).

Platform facts here are as of 2026-07; if that's more than ~6 months ago, spot-check with a web
search before leaning on specifics.

## What changes vs the X Article

- **Title + subtitle are SEO, not a curiosity hook.** Medium is indexed by Google/AI-search. Title
  ~50-60 chars with the primary keyword up front, in sentence/title case (readable in search
  results). Then a subtitle field that carries the story/hook (this is where the creator's own
  voice can live). Example: title `Self-Hosting Your Analytics Dashboard for $0` + subtitle
  `My free credits were about to run out, so I moved everything local`.
- **Real code blocks come back.** Medium has native, syntax-highlighted, copyable code blocks. Put
  the actual commands and config in fenced ```blocks```. Do NOT screenshot code, Medium code
  screenshots have no alt text and are inaccessible. The full config can also be a GitHub Gist embed.
- **Links are welcome inline** (no reach penalty, unlike X). Link the tools, the benchmarks, and
  the repo directly in the prose.
- **Drop all X scaffolding.** No launch post, no reply A/B, no "link only in a reply," no paste
  warning about markdown. Screenshots, if the video has any, become **figures with captions**; a
  video with none (e.g. an essay) runs text-only or uses one generated diagram.
- **Structure for scanning + AI-search.** One H1, clean H2/H3, and a tight TL;DR-style summary in
  the opening. Slightly more depth than the tight X cut, Medium rewards read-time.
- **Medium mechanics:** up to **5 tags**; a soft close (clap / comment / follow); if the piece is
  ALSO on X or a blog, add a **canonical URL** note pointing to the original so SEO doesn't split
  (skip if Medium is the original home); optional submission to a dev publication for reach.

## Deliverable shape (`blog/medium-article.md` + `.html`)

A short "how to get this into Medium" note (lead with the html twin's Copy button: pasting rich text
carries headings/bold/links/lists; note that a flattened code block is fixed by retyping ``` on it),
then the `TITLE` / `SUBTITLE` / `FEATURED IMAGE` / `TAGS` fields, then the body with real fenced
code blocks, `[FIGURE: path | caption]` markers, and inline links. One paragraph per line in the md.
Keep the voice, keep zero em dashes, keep the accuracy. Use the same pack scaffolding as the X pack
(ALL-CAPS labels with `====` banner lines; copyable payload between `----` and `====` lines, per
the layout block in `x.md`): `verify_article.py` only checks payload inside those zones and fails a
file with none.

## Featured image

Medium crops preview cards near 1.91:1 and the wide web hero even wider, keeping a centered safe
zone. Render a **1600x840** cover (that ratio needs almost no crop for cards/Twitter shares) with
the headline and hero element **centered**, and keep it **under 500KB**. Use
`assets/cover-medium-template.html` (the centered variant of the cover template) and the same
render/verify flow in `cover-render.md`.
