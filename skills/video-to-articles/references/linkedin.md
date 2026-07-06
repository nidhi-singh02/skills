# Producing a LinkedIn version

Platform facts here are as of 2026-07; if that's more than ~6 months ago, spot-check with a web
search before leaning on the specific multipliers. LinkedIn is a professional feed. Two facts
drive everything:
1. **A native post gets ~5x the reach of a LinkedIn "Article."** So the POST is the main event.
   The Article is a secondary, evergreen / Google + AI-citation play (reuse the Medium piece).
2. **Dwell time is the #1 signal (+40%)**, and **saves + quality comments** are the strongest
   levers. The first ~60 minutes (a 2-5% test audience) decide reach.

Deliver `blog/linkedin-post.md` containing the post, its first comment, and the article-reuse note.
Feed posts are plain text, so no html twin is needed: the unwrapped md (one paragraph per line)
pastes clean as-is. Use the same `----`/`====` payload scaffolding as the other packs (see the
layout block in `x.md`); `verify_article.py`'s plain-text and wrap checks run only on those payload
lines and fail a file with none.

## The native post

- **Hook in the first ~2 lines** (that's all that shows before "…see more"). Use a number,
  confession, or contradiction. Lead with the stakes or the result.
- **~150-250 words**, conversational and first-person, in the creator's voice. One feed-specific
  caveat: if their profile is unconventional for LinkedIn (e.g. all-lowercase), flag that it can
  read oddly in this feed and confirm before writing. No em dashes.
- **No code blocks render** in posts, so describe the fix and point to the repo, don't dump config.
- **Keep it link-free.** External links cost ~60% reach, and as of 2026 the "link in first comment"
  workaround is also dinged. Still, the least-bad option is the **repo link in your own first
  comment**. Never put it in the post body.
- **0-3 hashtags** (0 often wins now; the algorithm reads the full copy, not tags).
- **Attach images if the video has them.** Multi-image posts out-engage text-only, so reuse 3-4
  screenshots/frames when they exist. If the video has none (e.g. a talking-head essay), a strong
  text-only post is fine. Make it **save-worthy** (a concrete number/takeaway is what gets saved).
  (A swipeable carousel does even better, but that is a separate skill, not this one.)
- **CTA = a real question** to pull comments. Reply to every early comment fast (real replies).
- Post Tue-Thu mornings in the audience timezone.

## The LinkedIn Article (evergreen / authority)

Reuse the Medium piece: paste from `blog/medium-article.html` via its Copy button (headings, bold,
links, and lists carry into LinkedIn's Article editor). Articles get little feed reach but get
indexed by Google and cited by AI assistants, and they live on the profile. Caveats vs Medium:
LinkedIn's Article editor has no real code block (keep the short fix as plain text or point to the
repo), and links inside Articles are fine. Use the Medium cover as the banner, and drive traffic to
the Article from the post.
