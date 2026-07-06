# Producing the X (Twitter) Article pack

Deliver two files: `blog/x-article.md` (source of truth) and `blog/x-article.html` (the paste-ready
twin, see "Copy-paste fidelity" in SKILL.md). The pack has five sections, in this order.

## Pack file layout (verify_article.py parses this)
Each section is a numbered ALL-CAPS label under/over a banner line of 20+ `=`; every **copyable
payload** sits between a `----` separator line (20+ dashes) and the next `====` line, with
scaffolding notes outside those zones. The verifier keys on this: it finds the launch post by its
`1) LAUNCH POST` label, and the wrap / plain-text / twin-parity checks run only on payload lines
(a file with zero `----`/`====` zones fails). Skeleton:

    ====================================================
      1) LAUNCH POST   (scaffolding note, not copied)
    ====================================================
    (another scaffolding note)
    ----------------------------------------------------
    the copyable payload, one paragraph per line
    ====================================================
      2) REPLY A
    ...

Medium and LinkedIn packs use the same scaffolding (see `medium.md` / `linkedin.md`).

## Platform facts (as of 2026-07, re-verify if older than ~6 months)
- External links in a post cost roughly 30-90% reach; a published X Article attaches to a post as a
  native card with no link penalty.
- **X Articles require X Premium+** (publishing long-form Articles is a paid feature). Confirm the
  creator has it in Step 0/1. If they don't, fall back: post the article body as a long-form post
  (or a short thread) instead of an Article; the launch-post-then-link-in-reply structure below is
  unchanged, but the launch post links to the long-form post rather than attaching an Article card.
- Replies are worth ~27-150x a like; author replies that get replies are the strongest signal.
  Bookmarks are heavily weighted, so save-worthy content wins.
- Long-form dwell time boosts distribution; hashtags are near-useless (0-1 max).
- Good windows: Tue-Thu, mid-morning in the audience's timezone.

The structure below (linkless launch post, link in a reply, question reply) holds even if the exact
multipliers move; the as-of date above governs when to re-verify the numbers.

## 1. LAUNCH POST
The tweet that carries the Article. Linkless (the Article card attaches natively). Hook-first, the
creator's 2-3 line stack, ≤280 chars, zero hashtags by default. Pick the hook type that fits the
video's archetype (see SKILL.md): number/result, time-saved, contrarian claim, transformation, or
curiosity gap. Use the creator's true numbers; never invent one.

## 2. REPLY A
A reply-driving question, no link (a link would suppress the reply you want people answering).

## 3. REPLY B
A separate reply containing the repo/link, if one exists. No link exists? Skip Reply B entirely.

## 4. THE ARTICLE
A story-first `TITLE` in the creator's casing, a `[📷 COVER]` note, then the body following the archetype's arc,
its centerpiece given the most room. X's Article editor has no code block: show a key snippet as
in-body plain text plus a screenshot. `[📷 path | alt: …]` markers only where a real image exists
(no em dash inside markers either; the verifier flags them anywhere in the file).
Add one in-body save cue at the single most valuable moment ("bookmark this part…").

### Title, cover, and first line are three complementary slots
Never duplicate text across them; that wastes a prime attention slot and closes the curiosity gap.
Cover = the bold visual payoff. Title = the story / why-you. Launch first line = a third angle.

## 5. POSTING CHECKLIST
Order of operations (reverse of the file): publish the Article first via the .html twin's copy
button (headings/bold paste formatted; replace 📷 placeholder blocks with real uploads) → copy the
Article URL → launch post (do NOT paste the URL; let X attach the card; if images exist, attach a
2-4 image set for feed dwell) → Reply A → Reply B (if any) → win the first hour (seed a value reply,
answer early comments fast) → Day-2 quote-tweet with the single most surprising line or number from the article.
