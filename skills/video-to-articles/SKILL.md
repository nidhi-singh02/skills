---
name: video-to-articles
version: 1.1.0
description: >-
  Convert a recorded video (talking-head, build-along, tutorial, demo, essay, vlog) into a
  ready-to-post article or post for X (Twitter), Medium, or LinkedIn: a copy-paste pack (markdown +
  paste-ready HTML twin) plus a fresh cover image, in the creator's own voice. Use whenever the user
  wants a video, its transcript, or its screenshots turned into an X, Medium, or LinkedIn article,
  blog, or post (e.g. "make an X article from this video", "write a medium post from my recording"),
  or wants an existing long-form blog adapted for those platforms. Prefer this over generic writing
  when the source is a video or transcript and the destination is X, Medium, or LinkedIn. Do NOT use
  for: YouTube titles/descriptions/thumbnails, cutting shorts/reels, transcribing a video,
  scheduling/posting, or a swipeable LinkedIn carousel (separate skill).
---

# Video → article (X / Medium / LinkedIn)

Turn a video into a publish-ready article or post: **one deliverable pack** (md + paste-ready html)
plus **one cover image**, in the creator's voice, optimized for how each platform distributes
content. Works for **any** video: build-along, how-to, product demo, opinion essay, talking-head,
vlog. Derive every specific from the transcript in front of you. The rules below map to how the
platform algorithms behave and how a real person's voice reads; understand the *why* and adapt,
don't apply them as rote checkboxes.

## Requirements & graceful degradation
Rendering the cover uses the **Playwright MCP browser**. If it isn't available, don't fail: deliver
the finished `cover.html` plus one line of render instructions ("open in a browser at 1600×900 and
screenshot"), and continue with the articles. The written deliverables never depend on rendering.

## Workflow

### Step 0 — Gather inputs (read, don't guess)
- **Transcript**: read it in full. Source of truth for content AND the creator's actual phrasings.
  No transcript yet (just a video file)? Stop and ask for one, or point the user at a transcription
  tool/skill; never write from a summary or your memory of the video.
- **Voice profile**: read `~/.claude/voice-profile.md` if it exists and match it. If it doesn't,
  ask for 2-3 real posts, infer the voice, and **offer to write the profile file for them** (shape:
  `assets/voice-profile-template.md`) so every future run is zero-setup. If the profile has a
  `## Learned` section, treat it as binding: it records what this creator actually accepted and
  rejected on past runs.
- **Screenshots / frames (may not exist)**: if present, note what each shows; they become inline
  figures. Essays/talking-heads often have none, and that's fine (see "No assets" below).
- **Repo / link (may not exist)**: ask. If there isn't one, don't invent it.

### Step 1 — Confirm the real story (accuracy first)
Confirm the factual spine with the user, especially money, claims, outcomes. The most common
failure is a punchier-but-false framing (e.g. "cut my monthly bill" when they were on free credits).
A true hook beats a false one and protects the creator's credibility.

### Step 2 — Find the video's shape, then pick the arc
Identify the archetype; structure around ITS centerpiece ("give the centerpiece the most room" is
universal; which beat it is depends on the shape):
- **build / debug**: centerpiece = the wall + the exact fix.
  hook → what/why → setup → **wall + fix** → proof → honest caveat → close.
- **how-to / process**: centerpiece = the method + the non-obvious step.
  hook → the problem → the steps → **the part people get wrong** → result → close.
- **opinion / essay** (often no screenshots/repo): centerpiece = the argument + strongest evidence.
  hook (the claim) → why it matters → **the case** → honest counter-argument → what to do → close.
- **product / demo**: centerpiece = the watch-it-work moment + who it's for.
  hook → the problem → what it is → **the demo/proof** → limits → where to get it.
Pick the closest or blend. The example at the bottom is build/debug: one of four, not the template.

### Step 3 — Story spine, then the title/hook taste gate
Deliverables live in a `blog/` folder under the working directory (usually the video's project);
create it if missing, and ask where to put it if the working directory is unclear.
Write `blog/story-spine.md` first: ~15 lines holding the confirmed facts and true numbers, the
archetype + centerpiece, and the three attention slots (cover payoff / title story / first-line
angle). Every platform piece derives from the spine, so multi-platform runs never drift factually
and nothing gets re-derived. It's working scratch, not a publishable deliverable.

Then the **taste gate**: never ship your first title. Present **3-4 title + hook-line candidates**,
each a different hook type (number/result, time-saved, contrarian, transformation, curiosity gap),
one line on why it works, and mark a recommendation. Let the creator pick (use a question tool when
interactive). Record the winner in the spine. Titles are taste; options with tradeoffs beat a
single guess.

### Step 4 — Write for the platform (read the matching reference)
- **X (Twitter)** → `references/x.md` (launch post + replies + article + checklist)
- **Medium** → `references/medium.md` (SEO title/subtitle, real code blocks, tags)
- **LinkedIn** → `references/linkedin.md` (native post ≫ Article; plain text)
Each reference carries its platform facts with an as-of date. **Freshness rule:** if a facts block
is older than ~6 months, spot-check the key numbers with a web search before leaning on them.

### Step 5 — Cover, then verify (see sections below).

## Voice rules
The voice comes from the creator's profile (or the posts you inferred it from), **never from this
skill**. Casing, energy, sentence shape, signature words, emoji palette, closers: all follow the
profile, whatever it says. No profile and no posts? Write clean, plain sentence case and tell the
creator the piece sharpens once they add one. Rules that hold in ANY voice:
- **hook-first opener, never a greeting.** "hi guys" burns the scroll-stop; the first line is the
  pitch. Vocatives can appear later, just not as the first words.
- **No em dashes** (— or --): they read as an AI tell. Periods, commas, colons. Hard zero by
  default; only relax it if the creator's own profile uses them.
- **Keep the true rough edges.** Real numbers, losses next to wins, the creator's actual phrasings
  from the transcript. Sanded-smooth is how AI sounds; hard-won specifics are the hook.
- **No AI slop**: no "dive in / without further ado", no "it's not just X, it's Y", no rule-of-three
  filler, no hype words, no 🚨, no "thread 🧵". Before finishing, re-read the body hunting exactly
  these tells plus uniform sentence rhythm and stacked adjectives; the format drifts toward them.
  (The `avoid-ai-writing` / `humanizer` skills automate this pass if installed; neither is required.)

## Red flags — if you think this, stop
| thought | reality |
|---|---|
| "this number makes the hook punchier" | invented number = credibility debt. Step 1 exists for this |
| "every video needs a struggle section" | that's 1 of 4 archetypes; essays/demos have other centers |
| "i'll open with a quick greeting" | greetings kill the scroll-stop on every platform |
| "cover and title should say the same thing" | duplicated slots waste attention; split the labor |
| "no screenshots, i'll describe some" | never fake assets; use the no-assets path |
| "the reader can fix the formatting" | they can't easily; copy-paste fidelity is part of the job |

## Copy-paste fidelity (the deliverable must paste clean)
- **One paragraph = one line.** Never hard-wrap prose inside a paragraph in any copyable block;
  wrapped lines paste as literal newlines the user has to hand-repair. Wrapping is fine in
  scaffolding/comments only. Blank line between paragraphs.
- **Ship a paste-ready `.html` twin** next to the X and Medium markdown (e.g. `x-article.html`):
  same text, real `<h2>/<strong>/<a>/<ul>/<pre>` formatting, a small Copy button per section
  (select + `document.execCommand('copy')` copies rich text), and styled `📷 placeholder` blocks
  where images go (they paste as visible blocks the user replaces with uploads). Pasting rich text
  into X/Medium/LinkedIn Article editors carries headings and bold, so the user never re-applies
  formatting by hand. LinkedIn feed posts are plain text: no html twin needed, the unwrapped md is
  enough.
- The md is the source of truth; keep the html's text identical to it.

## No assets? (no screenshots / no repo)
- **No screenshots** (essays, talking-heads): don't fake them. Pull-quote callouts, one simple
  generated diagram, or clean text-only. Emit `[📷]` markers only for images that exist.
- **No repo/link:** drop the link reply/comment/inline mention entirely.

## The cover
Start from the topic and the creator's brand, not a fixed look. Editorial restraint always
(whitespace, one idea, refined type, restrained palette, no clipart/neon/stock/3D). **Most covers
should be text-only** (`assets/cover-text-template.html`, works light or dark; for photo-led
covers, uncomment its built-in hero-photo layer). Use
`assets/cover-template.html` only for a real A→B→C system diagram; `assets/cover-medium-template.html`
for Medium's centered 1600×840. All templates retheme via CSS vars (`--bg`, `--accent`,
`--display`; the two diagram templates also expose `--glow*` and default dark/pixel because they
were built for a dev video). The text template defaults editorial/light. Pick per topic:

| video type | palette | type | imagery |
|---|---|---|---|
| dev / technical | dark, one accent | mono/pixel or geometric sans | logos or a config snippet |
| product / SaaS | light or brand colour | geometric sans | a product/UI frame |
| cooking / lifestyle | light, warm | editorial serif | one hero photo |
| opinion / essay | high-contrast minimal | bold serif or grotesk | none (type-only) |
| how-to / process | clean, calm | friendly sans | one hero frame or a simple step diagram |

Render per `references/cover-render.md` (localhost serve + Playwright at 1600×900; helper:
`scripts/render_cover.sh`), save to `blog/assets/x_cover.png`, then **look at it**: legible at
~540px, survives a 1.91:1 centre-crop. Show the user before finalizing.

## Finish
- Run `scripts/verify_article.py <file> --platform x|medium|linkedin`: checks em dashes, hard-wrapped
  paragraphs in the `----`/`====` payload zones (a file with none fails; layout in `references/x.md`),
  launch-post length/linklessness (X), greeting openers, that every `[📷]`/`[FIGURE:]` marker
  resolves, that the html twin exists and matches the md (x/medium; pass `--no-twin` for an
  intentionally md-only run), Medium code fences balance, and the LinkedIn payload is plain text.
  Fix everything it flags; paste its output as evidence, don't claim from memory.
- Keep the folder lean (deliverables + only the assets they reference; confirm before removing
  files you didn't create). Cover verified by eye. Anti-AI-slop pass done.
- **Bank the edits (with consent):** if the creator changed or rejected anything in your draft,
  append one dated line per lesson to `## Learned` in `~/.claude/voice-profile.md` (create the
  section if missing; skip duplicates). Next run reads it in Step 0, so every edit trains the skill.
- Offer three follow-ups: save a one-shot prompt for the next video; (if the run went well) add a
  sanitized copy of the outputs to the repo's `examples/`; and a **post-launch retro** 24-48h after
  posting (see `references/retro.md`): collect the real numbers, log what the audience actually
  rewarded to `## Learned`, so hook and archetype choices compound run over run.

## One example (build/debug archetype, for shape only)
Imagine a build video about self-hosting an analytics dashboard. Its pack's launch post leads with
a time-saved hook ("Every guide for this skips the part that breaks. I burned 3 hours so you can do
it in 10 minutes."), a story-first title, and a dark cover over a simple 3-node diagram. That's the
build/debug shape: cost hook, wall-plus-fix centerpiece, system diagram. An essay, a cooking video,
or a product demo would use a different arc, hook, and cover; the casing and tics would be whatever
that creator's profile says. Derive everything from your own transcript; do not copy this shape.
