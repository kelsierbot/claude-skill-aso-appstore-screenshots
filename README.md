# Claude Skill: ASO Store Screenshots (no-API fork)

A [Claude Code](https://claude.com/claude-code) skill that analyzes your app's
codebase, discovers the core benefits that drive downloads, and composes
high-converting **App Store and Google Play** screenshots.

This is a fork of
[adamlyttleapps/claude-skill-aso-appstore-screenshots](https://github.com/adamlyttleapps/claude-skill-aso-appstore-screenshots)
with one big change and several additions:

## What's different in this fork

- **No Gemini / Nano Banana / MCP servers / API keys.** The original used a
  deterministic Pillow scaffold and then sent it to an image AI for "polish."
  This fork makes the compositor good enough on its own: gradient and radial-glow
  background styles, soft device shadows, and a deterministic breakout-panel
  effect (crop a real UI panel from your screenshot, scale it, float it over the
  frame). 100% local, reproducible output.
- **Exact store dimensions, no post-processing.** The original generated 9:16 AI
  images and then cropped/resized them to Apple's sizes. Deterministic
  composition renders at the exact target dimensions directly — the whole
  crop/resize phase is gone.
- **Google Play support.** `--preset play` (1080x1920) with a code-drawn Android
  punch-hole frame, plus `feature.py` for the required 1024x500 Play feature
  graphic. App Store presets (6.5"/6.7"/6.9") unchanged.
- **Screenshot capture built in.** The skill offers to capture screenshots from
  a connected Android device (adb), the iOS Simulator, or your project's render
  harness instead of making you hunt for files.
- **Portable fonts.** The original hardcoded macOS-only SF Pro paths; this fork
  resolves a heavy sans-serif across macOS/Linux/Windows, or drop your own at
  `assets/headline.ttf` (or pass `--font`).
- **Three style variants per screenshot** (flat / gradient / glow) replace the
  original's three AI rerolls — you still pick from 3, but they're instant,
  free, and identical every time you regenerate.

Everything else that made the original great is kept: the benefit-discovery
interview, screenshot rating and pairing, brand-colour workflow, per-set
consistency rules, memory-based resume, and the showcase image.

## Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/kelsierbot/claude-skill-aso-appstore-screenshots.git \
  ~/.claude/skills/aso-appstore-screenshots
```

Requires Python 3 with Pillow (`pip install pillow`).

## Use

In Claude Code, from your app's repo:

```
/aso-appstore-screenshots
```

Claude analyzes the codebase, interviews you about benefits, pairs screenshots,
and composes the set. Scripts can also be run standalone:

```bash
python3 compose.py --preset play --bg "#7A4FBF" --verb "ADOPT" \
  --desc "INFINITE COSMIC CATS" --screenshot shot.png --style glow --output out.png
python3 feature.py --bg "#7A4FBF" --verb "MYAPP" --desc "THE TAGLINE" \
  --screenshot shot.png --output feature.png
```

## Credits

Original skill by [Adam Lyttle](https://github.com/adamlyttleapps). Fork
maintained by kelsierbot.
