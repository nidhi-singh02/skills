# claude-skills

A small collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
for turning raw footage into finished, ready-to-post content. Built for
[Claude Code](https://claude.com/claude-code), usable by any agent that supports skills.

## Skills

| Skill | What it does |
|-------|--------------|
| **[shorts-from-takes](skills/shorts-from-takes/)** | Combine any clips — takes, shots, or existing reels — into one finished vertical Short (1080×1920): trimmed, ordered, fit to vertical, with optional captions, title card, speed-up, and relight, plus ready-to-post YouTube Shorts / Instagram Reels / X metadata. |
| **[video-to-articles](skills/video-to-articles/)** | Turn a recorded video (or its transcript) into a ready-to-post X Article pack, Medium article, or LinkedIn post — written in *your* voice (no house style), with a paste-ready HTML twin, a fresh cover image, a mechanical verifier, and a learning loop that compounds run over run. |
| **[longform-to-shorts](skills/longform-to-shorts/)** | Turn one finished long-form video (talking-head + screen-share) into several standalone vertical Shorts/Reels (1080×1920), one per topic — face zoom, screen zoom + slow-scroll, split-screen bubble, burned subtitles, hook, whoosh, pitch-preserved speed-up — plus per-clip YouTube + Instagram metadata. |

## Install a skill

Skills are just folders. Copy the one you want into your agent's skills directory:

```bash
git clone https://github.com/<your-username>/claude-skills
cp -r claude-skills/skills/shorts-from-takes ~/.claude/skills/
```

Then in Claude Code, just ask for the thing the skill does (e.g. *"cut a Short from these
clips"*) — it triggers automatically from its description. Each skill's own README covers
its prerequisites and usage.

## License

- **Code & docs:** MIT — see [LICENSE](LICENSE).
- **Bundled fonts** (`skills/*/assets/fonts/`): SIL Open Font License 1.1 — see each
  skill's `assets/font-licenses/`.
