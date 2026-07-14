# Editorial workflow — story, continuity, coverage

Use this before writing `spec.json` whenever the source contains speech, multiple takes, or a
story assembled from separate moments. Rendering cannot repair a confusing paper edit.

## 1. Set the editorial brief

Write four lines before selecting footage:

- **Audience:** who should understand or care.
- **Promise:** the one useful idea, feeling, or transformation the video delivers.
- **Focus:** the two or three themes that earn the most time.
- **Deprioritize:** interesting material that distracts from the promise.

Do not infer the focus from the longest answer or the cleanest take. Select for the brief, then
choose the strongest performance that communicates it.

## 2. Audit all footage

Analyze every supplied clip before making edit decisions. Build a source map with:

| Source range | Speaker/subject | Exact line/action | Meaning | Performance | Visual/audio notes |
|---|---|---|---|---|---|
| clip + timecode | stable role label | verbatim or concise action | what it adds | strong/usable/weak | eyeline, framing, noise, movement |

Mark false starts, repeated ideas, incomplete sentences, camera adjustments, off-screen prompts,
and clean reaction or b-roll moments. A technically clean line is not automatically useful; a
line is strong when its meaning and delivery both support the story.

## 3. Write the paper edit

Create `paper_edit.md` before `spec.json`. List the exact viewer-facing order:

| # | Beat | Speaker/subject | Exact line or action | Source range | Purpose | Dependency/bridge |
|---|---|---|---|---|---|---|
| 1 | Hook | role | verbatim line/action | clip + in/out | earns attention | understandable cold |
| 2 | Context | role | verbatim line/action | clip + in/out | frames the problem | defines terms used later |

Use stable speaker labels across all clips. Keep wording verbatim unless the item is explicitly a
generated title, caption, or end card. The paper edit is the contract: select and approve the
lines first, then make visual choices around them.

## 4. Run the continuity gate

Read only the proposed lines, without looking at the footage. The sequence is not ready until:

1. The hook is understandable without hidden setup.
2. Every pronoun and reference has an obvious antecedent.
3. Terms are introduced before examples, consequences, or solutions depend on them.
4. Questions are followed by answers that address the same question.
5. Each beat adds new information instead of restating the previous beat.
6. Removing any line does not break the logic of the next line; if it does, restore context or add
   an honest bridge.
7. The ending resolves the promise rather than merely stopping on the last usable sentence.

Prefer a longer coherent answer over a shorter sequence of disconnected fragments. Tight pacing
means removing dead time, not removing the words required to understand the idea.

## Interview-specific rules

- Preserve enough of each question to establish what the answer is solving. Do not reduce the
  interviewer to decontextualized reaction shots.
- Keep both participants present in the story. Use the interviewer for framing, clarification,
  challenge, or synthesis; use the guest for substance. Balance follows function, not a fixed
  screen-time ratio.
- Keep question and answer adjacent unless an intentional visual cutaway preserves the same audio
  thought. A new topic requires a new setup.
- Favor complete clauses and natural breaths. Remove filler and repetition, but do not splice
  unrelated sentence halves into a claim the speaker did not make.
- Use listener reactions, two-shots, or relevant b-roll to cover trims only when eyelines, emotion,
  and timing match. Coverage should clarify the exchange, not disguise a broken one.

## Pacing and transitions

- Earn the first three seconds with the strongest complete idea or action, not an unexplained
  fragment selected only because it is dramatic.
- Vary pace by purpose: compress setup and repetition; hold on proof, emotion, demonstrations, or
  a decisive answer long enough to register.
- Prefer hard cuts for continuous thought and matched action. Use dissolves or wipes only when they
  communicate a real change in time, place, speaker, medium, or section.
- Assign each join a reason before choosing a transition. If no reason exists, use the least visible
  edit.
- Check visual continuity across every cut: eyeline, movement direction, hand position, framing,
  exposure, white balance, and background geometry.

## Endings and brand assets

Use the strongest source conclusion when one exists. If the footage lacks a clean ending, create a
brief end card that summarizes the established takeaway or gives an appropriate CTA. Never present
generated copy as a spoken quote or introduce a new unsupported claim.

When brand assets are supplied:

- Use the official logo/wordmark from the highest-quality source; do not redraw it with a font.
- Derive colours from the supplied identity assets and keep contrast accessible in vertical safe
  areas.
- Match the ending to the edit's visual language rather than dropping in an unrelated template.
- Add restrained continuous motion to static cards when it improves polish and prevents the video
  from appearing frozen. Otherwise allow-list an intentional hold in `quality_checks`.
- Let dialogue resolve before the card. Carry music or room tone naturally; the renderer adds a
  silent audio stream when a graphic clip has none.

## Lock before rendering

Present the paper edit when the user asks to approve lines, structure, or speaker balance. After it
is approved, change timing, coverage, captions, grade, and sound freely, but do not silently change
the approved meaning or line order. If a render reveals an editorial problem, update the paper edit
first and explain the changed dependency.
