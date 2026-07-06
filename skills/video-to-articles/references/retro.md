# Post-launch retro (24-48h after posting)

The skill's biggest long-term edge is the loop: launch → measure → adjust. A retro takes five
minutes and turns each post into training data for the next one. Offer it at the end of every run;
run it when the creator comes back with numbers (or ask them to paste an analytics screenshot).

## What to collect (per platform, whatever they have)
- **X**: impressions, likes, replies, bookmarks (the strongest quality signal), profile visits,
  article read time if shown. Which reply got the most engagement.
- **Medium**: views, reads, read ratio, claps, highlights (what people highlighted = the line that
  landed), follower delta.
- **LinkedIn**: impressions, reactions, comments, saves, "see more" expand rate if shown.
- Everywhere: which line people quoted or screenshotted, and one subjective note from the creator
  ("felt spammy", "repo forks doubled").

## How to log it
Append ONE dated line per finding to `## Learned` in `~/.claude/voice-profile.md` (same section the
draft-edit banking uses; create if missing). Findings, not raw stats. Format:

    2026-07-05 · x · build/debug · time-saved hook · bookmarks 4x likes: config posts get saved, keep the in-body save cue
    2026-07-12 · linkedin · essay · contrarian hook · flat reach, comments deep: essays need a sharper first 2 lines here

## How to apply it (next run, Step 0/3)
- Hook choice: if a hook type repeatedly wins for this creator, make it the recommended option in
  the taste gate (still show alternatives).
- Archetype: note which shapes their audience rewards; steer borderline videos toward them.
- Platform: if one platform consistently outperforms, say so when the creator asks "where should
  this go?".
- Never over-fit to one launch: two or more consistent signals before changing a default.

## Verdict discipline
A retro line must name a decision it changes ("keep the save cue", "drop hashtags entirely"). A
number with no decision attached is trivia; don't log it.
