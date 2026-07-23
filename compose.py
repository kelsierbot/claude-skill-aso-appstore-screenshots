#!/usr/bin/env python3
"""
Store Screenshot Composer — fully deterministic, zero external APIs.

Composites headline text, a code-drawn device frame, and an app screenshot into
a pixel-perfect store image AT THE EXACT target dimensions (no crop/resize pass
needed — that dance only existed to work around AI generators' fixed ratios).

Presets:
    iphone67  1290x2796  (App Store Connect, iPhone 6.7", default)
    iphone65  1242x2688
    iphone69  1320x2868
    play      1080x1920  (Google Play phone screenshot, 9:16)

Styles (v1/v2/v3 variant picks without any AI):
    flat      solid brand colour (the classic high-converting look)
    gradient  diagonal two-hue blend (brand colour -> auto magenta-shift, or --bg2)
    glow      flat + a soft radial light behind the device

Optional deterministic breakout: crop a UI panel from the SOURCE screenshot,
scale it up, drop-shadow it, and float it over the device frame:
    --breakout X,Y,W,H        (pixel rect in the source screenshot)
    --breakout-scale 1.55     (how much bigger than on-device it appears)
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from generate_frame import build_frame

PRESETS = {
    "iphone67": (1290, 2796, "iphone"),
    "iphone65": (1242, 2688, "iphone"),
    "iphone69": (1320, 2868, "iphone"),
    "play": (1080, 1920, "android"),
}

# Layout proportions (relative to canvas; derived from the original 1290x2796 design)
DEVICE_W_FRAC = 1030 / 1290
DEVICE_Y_FRAC = 720 / 2796
TEXT_TOP_FRAC = 200 / 2796
VERB_MAX_FRAC = 256 / 1290
VERB_MIN_FRAC = 150 / 1290
DESC_FRAC = 124 / 1290
VERB_DESC_GAP_FRAC = 20 / 2796
LINE_GAP_FRAC = 24 / 2796
MAX_TEXT_W_FRAC = 0.92

# Portable heavy-weight font resolution (original hardcoded a macOS-only path)
FONT_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "headline.ttf"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "headline.otf"),
    "/Library/Fonts/SF-Pro-Display-Black.otf",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def resolve_font(explicit=None):
    if explicit:
        if os.path.exists(explicit):
            return explicit
        sys.exit(f"Font not found: {explicit}")
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    sys.exit(
        "No usable headline font found. Drop a heavy sans-serif at assets/headline.ttf "
        "in the skill directory, or pass --font /path/to/font.ttf"
    )


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def word_wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(font_path, text, max_w, size_max, size_min):
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for size in range(size_max, size_min - 1, -4):
        font = ImageFont.truetype(font_path, size)
        bbox = dummy.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            return font
    return ImageFont.truetype(font_path, size_min)


def draw_centered(draw, canvas_w, y, text, font, line_gap, max_w=None):
    lines = word_wrap(draw, text, font, max_w) if max_w else [text]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        draw.text((canvas_w // 2, y - bbox[1]), line, fill="white", font=font, anchor="mt")
        y += h + line_gap
    return y


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def compose(args):
    if args.size:
        canvas_w, canvas_h = (int(v) for v in args.size.lower().split("x"))
        frame_style = args.frame or "iphone"
    else:
        canvas_w, canvas_h, default_frame = PRESETS[args.preset]
        frame_style = args.frame or default_frame

    bg = hex_to_rgb(args.bg)
    font_path = resolve_font(args.font)

    # 1. Background
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (*bg, 255))
    if args.style == "gradient":
        # End colour: explicit --bg2, else an auto hue-shifted partner (toward magenta,
        # slightly deeper) — a real two-hue gradient, not a flat darken. Diagonal by default.
        if args.bg2:
            end = hex_to_rgb(args.bg2)
        else:
            import colorsys
            h, l, s = colorsys.rgb_to_hls(*[c / 255 for c in bg])
            h2 = (h - 0.07) % 1.0            # rotate toward pink/magenta
            l2 = max(0.0, l - 0.06)
            s2 = min(1.0, s + 0.12)
            end = tuple(int(c * 255) for c in colorsys.hls_to_rgb(h2, l2, s2))
        diag = args.gradient_dir == "diagonal"
        try:
            import numpy as np
            ys = np.linspace(0, 1, canvas_h)[:, None]
            xs = np.linspace(0, 1, canvas_w)[None, :]
            t = (xs + ys) / 2.0 if diag else np.repeat(ys, canvas_w, axis=1)
            arr = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
            for i in range(3):
                arr[..., i] = (bg[i] + (end[i] - bg[i]) * t).astype(np.uint8)
            arr[..., 3] = 255
            canvas = Image.fromarray(arr, "RGBA")
        except ImportError:
            # pure-Pillow fallback: vertical only, fast via 1-px column resize
            grad = Image.new("RGBA", (1, canvas_h))
            for yy in range(canvas_h):
                tv = yy / max(1, canvas_h - 1)
                grad.putpixel((0, yy), tuple(int(a + (b - a) * tv) for a, b in zip(bg, end)) + (255,))
            canvas = grad.resize((canvas_w, canvas_h))

    # 2. Headline (verb auto-fit, desc wrapped) — exact same treatment as the original
    verb_font = fit_font(
        font_path, args.verb.upper(), int(canvas_w * MAX_TEXT_W_FRAC),
        round(canvas_w * VERB_MAX_FRAC), round(canvas_w * VERB_MIN_FRAC),
    )
    desc_font = ImageFont.truetype(font_path, round(canvas_w * DESC_FRAC))
    line_gap = round(canvas_h * LINE_GAP_FRAC)
    draw = ImageDraw.Draw(canvas)
    y = round(canvas_h * TEXT_TOP_FRAC)
    y = draw_centered(draw, canvas_w, y, args.verb.upper(), verb_font, line_gap)
    y += round(canvas_h * VERB_DESC_GAP_FRAC)
    text_bottom = draw_centered(
        draw, canvas_w, y, args.desc.upper(), desc_font, line_gap, max_w=int(canvas_w * MAX_TEXT_W_FRAC)
    )

    # 3. Device geometry — below the text with a safe gap, bleeding off the bottom
    device_w = round(canvas_w * DEVICE_W_FRAC)
    device_y = max(round(canvas_h * DEVICE_Y_FRAC), text_bottom + round(canvas_h * 0.014))
    device_x = (canvas_w - device_w) // 2
    frame, (bez_x, bez_y, screen_w, _screen_h) = build_frame(frame_style, device_w)
    screen_x = device_x + bez_x
    screen_y = device_y + bez_y
    screen_r = round(62 * device_w / 1030)

    # 3b. Glow behind the device (style=glow)
    if args.style == "glow":
        glow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        light = tuple(min(255, int(c * 1.45 + 40)) for c in bg)
        cx, cy = canvas_w // 2, device_y + round(canvas_h * 0.18)
        max_r = round(canvas_w * 0.72)
        for r in range(max_r, 0, -8):
            a = int(90 * (1 - r / max_r))
            gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*light, a))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        canvas = Image.alpha_composite(canvas, glow)

    # 3c. Soft drop shadow behind the device
    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [device_x - 8, device_y + 14, device_x + device_w + 8, canvas_h + 200],
        radius=round(77 * device_w / 1030),
        fill=(0, 0, 0, 110),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    canvas = Image.alpha_composite(canvas, shadow)

    # 4. Screenshot into the screen area (fill width, top-aligned, rounded)
    shot = Image.open(args.screenshot).convert("RGBA")
    scale = screen_w / shot.width
    shot_r = shot.resize((screen_w, int(shot.height * scale)), Image.LANCZOS)
    screen_vis_h = canvas_h - screen_y + 500
    scr_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(scr_layer).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_vis_h],
        radius=screen_r, fill=(0, 0, 0, 255),
    )
    scr_layer.paste(shot_r, (screen_x, screen_y))
    scr_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(scr_mask).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_vis_h],
        radius=screen_r, fill=255,
    )
    scr_layer.putalpha(scr_mask)
    canvas = Image.alpha_composite(canvas, scr_layer)

    # 5. Device frame on top
    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    frame_layer.paste(frame, (device_x, device_y))
    canvas = Image.alpha_composite(canvas, frame_layer)

    # 6. Optional deterministic breakout panel (cropped from the SOURCE screenshot)
    if args.breakout:
        bx, by, bw, bh = (int(v) for v in args.breakout.split(","))
        panel = shot.crop((bx, by, bx + bw, by + bh))
        target_w = min(round(bw * scale * args.breakout_scale), round(canvas_w * 0.94))
        target_h = round(bh * (target_w / bw))
        panel = panel.resize((target_w, target_h), Image.LANCZOS)
        panel = rounded(panel, radius=max(12, round(target_w * 0.03)))
        # keep the panel at the same relative vertical position it has on-device
        py = screen_y + round(by * scale) - round((target_h - bh * scale) / 2)
        py = max(text_bottom + 30, min(py, canvas_h - target_h - 40))
        px = (canvas_w - target_w) // 2
        p_shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(p_shadow).rounded_rectangle(
            [px + 2, py + 18, px + target_w + 2, py + target_h + 18],
            radius=max(12, round(target_w * 0.03)), fill=(0, 0, 0, 130),
        )
        p_shadow = p_shadow.filter(ImageFilter.GaussianBlur(22))
        canvas = Image.alpha_composite(canvas, p_shadow)
        canvas.alpha_composite(panel, (px, py))

    # 7. Save at EXACT store dimensions — no post-processing pass exists or is needed
    out = canvas.convert("RGB")
    if args.output.lower().endswith((".jpg", ".jpeg")):
        out.save(args.output, "JPEG", quality=92)
    else:
        out.save(args.output, "PNG")
    print(f"OK {args.output} ({canvas_w}x{canvas_h}, {frame_style} frame, {args.style})")


def main():
    p = argparse.ArgumentParser(description="Compose a store screenshot (no AI, exact dimensions)")
    p.add_argument("--bg", required=True, help="Background hex colour (#E31837)")
    p.add_argument("--verb", required=True, help="Action verb (TRACK)")
    p.add_argument("--desc", required=True, help="Benefit descriptor (TRADING CARD PRICES)")
    p.add_argument("--screenshot", required=True, help="App screenshot path")
    p.add_argument("--output", required=True, help="Output file path (.png or .jpg)")
    p.add_argument("--preset", choices=sorted(PRESETS), default="iphone67")
    p.add_argument("--size", help="Explicit WxH override (e.g. 1080x2340)")
    p.add_argument("--frame", choices=["iphone", "android", "none"], default=None,
                   help="Device frame style (default: per preset)")
    p.add_argument("--style", choices=["flat", "gradient", "glow"], default="flat")
    p.add_argument("--bg2", help="Gradient end colour hex (default: auto hue-shift toward magenta)")
    p.add_argument("--gradient-dir", choices=["vertical", "diagonal"], default="diagonal")
    p.add_argument("--font", help="Path to a heavy sans-serif font (overrides auto-detect)")
    p.add_argument("--breakout", help="X,Y,W,H rect in the source screenshot to pop out")
    p.add_argument("--breakout-scale", type=float, default=1.55)
    args = p.parse_args()

    if args.frame == "none":
        sys.exit("--frame none is not supported yet; use iphone or android")
    compose(args)


if __name__ == "__main__":
    main()
