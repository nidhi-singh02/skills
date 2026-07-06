# Changelog

## 1.2.0 — 2026-07-06
- Verifier hardened: em-dash check now strips code/URLs/HTML-comments and catches `word--word`
  (plus `--allow-em-dash` for creators whose voice profile permits them); launch-post length counts
  CJK/emoji as X does and detects scheme-less links; LinkedIn plain-text check flags md links and
  italics with a balanced-`**` guard; X twin-parity is scoped to THE ARTICLE body (launch post +
  replies are pasted separately and intentionally not in the twin); CJK/Thai wrap heuristic; robust
  read errors.
- Content: added an interview/conversation/vlog archetype and multi-topic "split into separate runs"
  guidance; non-English transcript handling; an explicit destination-platform step; a Medium
  subtitle-vs-SEO-title nuance; a LinkedIn-post-only cover skip; per-platform cover filenames.
- Cover pipeline: `render_cover.sh`/`fetch_logo.sh` bind to loopback, add curl timeouts and
  protocol-relative logo handling; `cover-render.md` documents the serve/collect/stop helper and a
  fresh-copy `sips` flow.
- Docs: description hardened (summarize/notes exclusion, "blog or post"); a `## Files` manifest; the
  em-dash rule reframed so the profile exception is primary; an execCommand fallback note.

## 1.1.0 — 2026-07-05
- Copy-paste fidelity: one paragraph per line everywhere; paste-ready `.html` twins for X and
  Medium with per-section Copy buttons (headings/bold/links paste formatted; 📷 placeholder blocks).
- Story spine (`blog/story-spine.md`) so multi-platform runs share one factual source of truth.
- Title/hook taste gate: 3-4 candidates with tradeoffs before drafting, creator picks.
- Learning loop: draft-edit banking + post-launch retro (`references/retro.md`) into the voice
  profile's `## Learned` section.
- `scripts/`: `verify_article.py` (mechanical checks incl. html-twin parity), `render_cover.sh`,
  `fetch_logo.sh` (root-path waterfall + homepage-scrape fallback).
- Router structure: X mechanics moved to `references/x.md`; platform facts stamped with as-of dates
  and a freshness re-check rule; graceful degradation when the Playwright browser is absent.
- Voice-neutral: the skill carries no house style; voice comes only from the creator's profile.
- Red-flags table, no-assets paths (no screenshots / no repo), "do NOT use for" triggers, evals.

## 1.0.0 — 2026-07-03
- Initial public shape: video → X Article pack, Medium article, LinkedIn post; archetype arcs;
  cover templates (text-only, diagram, Medium) rethemable via CSS vars; bundled Departure Mono
  (MIT) with license; voice-profile template; MIT license.
