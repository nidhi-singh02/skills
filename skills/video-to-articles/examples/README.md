# Examples: your real runs land here

This folder starts empty on purpose. After a good run, the skill offers to save a sanitized copy of
the deliverable pack here, so over time it fills with *your* reference material in *your* voice.

Why keep them: past packs are the fastest way to check section order, launch-post shape, marker
placement, and the html twin against something that actually shipped. Study the *structure* of a
past run; the content, hooks, and voice always come from the new video's transcript and your own
voice profile.

## Adding a run

Copy the deliverable pack here named `<platform>-<slug>.md` (+ `.html` if the platform ships a
twin). Scan it for anything private first: emails, keys, phone numbers, unpublished links. Then
sanity-check it:

```bash
python3 ../scripts/verify_article.py <platform>-<slug>.md --platform x|medium|linkedin
```

(`image markers: MISSING` is expected on copies; the `[📷 …]` markers point at the original
project's `blog/assets/`, which stays with the video project.)
