# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code skill (`aso-appstore-screenshots`) that guides users through creating high-converting App Store AND Google Play screenshots — 100% locally with Pillow. No image-AI service, no API keys, no MCP servers. Invoked via the `/aso-appstore-screenshots` slash command from within a user's app project.

This is the kelsierbot fork of adamlyttleapps/claude-skill-aso-appstore-screenshots with the Gemini/Nano-Banana enhancement stage removed and the deterministic compositor upgraded to stand on its own.

## Architecture

- **SKILL.md** — The skill prompt. Multi-phase workflow: Benefit Discovery → Screenshot Pairing → Generation (single deterministic stage, three style variants) → optional Play feature graphic → Showcase. Uses Claude Code's memory system to persist state so users can resume mid-workflow.
- **compose.py** — Pillow compositor. Renders at EXACT store dimensions (presets: iphone65/67/69, play). Styles: flat / gradient / glow. Soft device shadow always. Optional deterministic breakout (`--breakout X,Y,W,H` crops a panel from the source screenshot, scales it, floats it with a drop shadow). Portable heavy-font resolution with `--font` override or `assets/headline.ttf`.
- **generate_frame.py** — Importable device-frame builder: `build_frame(style, device_w)` returns an in-memory RGBA frame (iphone = Dynamic Island, android = punch-hole) plus its screen box. compose.py builds frames at whatever scale it needs — the pre-rendered asset is optional (CLI still writes one for compatibility).
- **feature.py** — Google Play feature graphic (1024x500): headline left, framed device bleeding off the right.
- **showcase.py** — Side-by-side preview of up to 3 final screenshots (portable fonts).

## Running compose.py

```bash
# Requires: pip install Pillow  (a bold system font is auto-detected on macOS/Linux/Windows)
python3 compose.py --preset play --bg "#7A4FBF" --verb "ADOPT" \
  --desc "INFINITE COSMIC CATS" --screenshot shot.png --style glow --output out.png
```

## Key Design Decisions

- **Single-stage deterministic generation** — the compositor IS the generator. Regeneration is instant, free, and reproducible; iteration honours every tweak exactly.
- **Exact store dimensions natively** — the original's crop/resize phase existed only because AI generators output fixed aspect ratios. It is gone.
- **Frames are code-drawn in-memory** at any scale (no fixed template dependency), one style per store.
- **Three style variants (flat/gradient/glow) replace the AI pick-of-3** — same UX, zero cost. The user's pick on screenshot 1 locks the style for the set.
- **Breakouts are real crops of the real screenshot**, not AI hallucinations — Claude reads the screenshot, finds the panel rect, passes pixel coordinates.
- **Memory is central to the workflow** — benefits, assessments, pairings, brand colour, chosen style, and generation state persist across conversations.
