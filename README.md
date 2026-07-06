# skills for content creators

A small collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
for turning raw footage into finished, ready-to-post content. These are usable by any agent that supports skills.

[Subscribe To My YouTube Channel](https://www.youtube.com/@NidhiSinghAttri?sub_confirmation=1)

## Skills

| Skill | What it does |
|-------|--------------|
| **[shorts-from-takes](skills/shorts-from-takes/)** | Combine any clips — takes, shots, or existing reels — into one finished vertical Short (1080×1920): trimmed, ordered, fit to vertical, with optional captions, title card, speed-up, and relight, plus ready-to-post YouTube Shorts / Instagram Reels / X metadata. |
| **[video-to-articles](skills/video-to-articles/)** | Turn a recorded video (or its transcript) into a ready-to-post X Article pack, Medium article, or LinkedIn post — written in *your* voice (no house style), with a paste-ready HTML twin, a fresh cover image, a mechanical verifier, and a learning loop that compounds run over run. |

## Quickstart (30-second setup)

1. Run the skills.sh installer: 
```bash
npx skills@latest add nidhi-singh02/skills
```

2. Pick the skills you want, and which coding agents you want to install them on.

Then in Claude Code/Codex/Cursor, just ask for the thing the skill does (e.g.
*"cut a Short from these clips"* or *"turn this video into a Medium article"*) —
it triggers automatically from its description. Each skill's own README covers
its prerequisites and usage.

