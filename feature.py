#!/usr/bin/env python3
"""
Google Play Feature Graphic composer — 1024x500, required for a Play listing.

Headline block on the left, framed device peeking in from the right and
bleeding off the edges. Same deterministic, zero-API approach as compose.py.

    python3 feature.py --bg "#7A4FBF" --verb "ADOPT" --desc "INFINITE COSMIC CATS" \
        --screenshot shot.png --output feature.png [--style gradient] [--frame android]
"""

import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from compose import hex_to_rgb, resolve_font, word_wrap
from generate_frame import build_frame

W, H = 1024, 500


def compose_feature(args):
    bg = hex_to_rgb(args.bg)
    font_path = resolve_font(args.font)

    canvas = Image.new("RGBA", (W, H), (*bg, 255))
    if args.style == "gradient":
        dark = tuple(int(c * 0.74) for c in bg)
        grad = Image.new("RGBA", (W, 1))
        for x in range(W):
            t = x / (W - 1)
            grad.putpixel((x, 0), tuple(int(a + (b - a) * t) for a, b in zip(bg, dark)) + (255,))
        canvas = grad.resize((W, H))

    # Device on the right, tilted composition kept simple: upright, bleeding right+bottom
    device_w = 300
    frame, (bez_x, bez_y, screen_w, _sh) = build_frame(args.frame, device_w)
    device_x = W - device_w + 40
    device_y = 70

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [device_x - 6, device_y + 10, device_x + device_w + 6, H + 100], radius=24, fill=(0, 0, 0, 110)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(canvas, shadow)

    shot = Image.open(args.screenshot).convert("RGBA")
    scale = screen_w / shot.width
    shot_r = shot.resize((screen_w, int(shot.height * scale)), Image.LANCZOS)
    screen_x = device_x + bez_x
    screen_y = device_y + bez_y
    scr_r = round(62 * device_w / 1030)
    scr_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(scr_layer).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, H + 100], radius=scr_r, fill=(0, 0, 0, 255)
    )
    scr_layer.paste(shot_r, (screen_x, screen_y))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, H + 100], radius=scr_r, fill=255
    )
    scr_layer.putalpha(mask)
    canvas = Image.alpha_composite(canvas, scr_layer)
    frame_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    frame_layer.paste(frame, (device_x, device_y))
    canvas = Image.alpha_composite(canvas, frame_layer)

    # Headline block, left-aligned in the safe area left of the device
    draw = ImageDraw.Draw(canvas)
    text_area_w = device_x - 90
    verb_font = None
    for size in range(120, 48, -4):
        f = ImageFont.truetype(font_path, size)
        if draw.textlength(args.verb.upper(), font=f) <= text_area_w:
            verb_font = f
            break
    verb_font = verb_font or ImageFont.truetype(font_path, 48)
    desc_font = ImageFont.truetype(font_path, 44)

    desc_lines = word_wrap(draw, args.desc.upper(), desc_font, text_area_w)
    vb = draw.textbbox((0, 0), args.verb.upper(), font=verb_font)
    verb_h = vb[3] - vb[1]
    desc_h = sum((draw.textbbox((0, 0), l, font=desc_font)[3] - draw.textbbox((0, 0), l, font=desc_font)[1]) + 12 for l in desc_lines)
    total_h = verb_h + 16 + desc_h
    y = (H - total_h) // 2
    draw.text((50, y - vb[1]), args.verb.upper(), fill="white", font=verb_font)
    y += verb_h + 16
    for line in desc_lines:
        lb = draw.textbbox((0, 0), line, font=desc_font)
        draw.text((50, y - lb[1]), line, fill="white", font=desc_font)
        y += (lb[3] - lb[1]) + 12

    out = canvas.convert("RGB")
    if args.output.lower().endswith((".jpg", ".jpeg")):
        out.save(args.output, "JPEG", quality=92)
    else:
        out.save(args.output, "PNG")
    print(f"OK {args.output} (1024x500 feature graphic)")


def main():
    p = argparse.ArgumentParser(description="Google Play feature graphic (1024x500, no AI)")
    p.add_argument("--bg", required=True)
    p.add_argument("--verb", required=True)
    p.add_argument("--desc", required=True)
    p.add_argument("--screenshot", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--style", choices=["flat", "gradient"], default="gradient")
    p.add_argument("--frame", choices=["iphone", "android"], default="android")
    p.add_argument("--font")
    args = p.parse_args()
    compose_feature(args)


if __name__ == "__main__":
    main()
