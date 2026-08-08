# skills for content creators

![GitHub stars](https://img.shields.io/github/stars/nidhi-singh02/skills?style=flat-square)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Agent Skills](https://img.shields.io/badge/agent-skills-8A2BE2?style=flat-square)

A collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turn raw footage into finished, ready-to-post content. Usable by any agent that supports skills — Claude Code, Codex, Cursor, and more.

Built by a solo creator who got tired of manually editing every Short, article, and caption. These are the exact workflows I use for my own channel.

## What you get

| Skill | What it does |
|-------|--------------|
| **[shorts-from-takes](skills/shorts-from-takes/)** | Combine any clips — takes, shots, or existing reels — into one finished vertical Short (1080×1920): trimmed, ordered, fit to vertical, with optional captions, title card, speed-up, and relight, plus ready-to-post YouTube Shorts / Instagram Reels / X metadata. |
| **[video-to-articles](skills/video-to-articles/)** | Turn a recorded video (or its transcript) into a ready-to-post X Article pack, Medium article, or LinkedIn post — written in *your* voice (no house style), with a paste-ready HTML twin, a fresh cover image, a mechanical verifier, and a learning loop that compounds run over run. |
| **[longform-to-shorts](skills/longform-to-shorts/)** | Turn one finished long-form video (talking-head + screen-share) into several standalone vertical Shorts/Reels (1080×1920), one per topic — face zoom, screen zoom + slow-scroll, split-screen bubble, burned subtitles, hook, whoosh, pitch-preserved speed-up — plus per-clip YouTube + Instagram metadata. |

## Quickstart (30-second setup)

```bash
npx skills@latest add nidhi-singh02/skills
```

Pick the skills you want and which coding agents to install them on. Then just ask for the thing the skill does:

```
"cut a Short from these clips"
"turn this video into a Medium article"
```

It triggers automatically from its description. Each skill's own README covers prerequisites and usage.

## Why agent skills

Skills are the missing glue between "I have a workflow" and "my agent does it for me." Instead of re-explaining your process every session, you install it once and the agent knows how to do it. This repo is a working example of that pattern, built and tested in real production use (every Short on my channel went through these).

## Video walkthrough

[![Watch the shorts-from-takes installation and usage walkthrough](https://img.youtube.com/vi/bTORVA83vSI/maxresdefault.jpg)](https://youtu.be/bTORVA83vSI)

## License

MIT — see [LICENSE](LICENSE). Bundled fonts keep their own licenses, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
