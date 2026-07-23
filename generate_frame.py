#!/usr/bin/env python3
"""
Device frame builder — iPhone (Dynamic Island) and Android (punch-hole) styles.

Importable: build_frame(style, device_w) returns (frame RGBA, screen_box) where
screen_box = (x, y, w, h) of the transparent screen cutout. compose.py builds
frames in-memory at whatever scale the canvas needs — no pre-rendered asset,
no external tools, no AI.

CLI (optional, writes the asset like the original repo did):
    python3 generate_frame.py --style iphone --out assets/device_frame.png
"""

import argparse
from PIL import Image, ImageDraw, ImageChops

# Reference proportions (at device_w=1030, matching the original template)
REF_W = 1030
REF_H = 2800          # tall enough to bleed off any canvas
REF_CORNER_R = 77
REF_BEZEL = 15
REF_SCREEN_R = 62
REF_DI_W = 130        # iPhone Dynamic Island
REF_DI_H = 38
REF_DI_TOP = 14
REF_HOLE_R = 16       # Android punch-hole camera radius
REF_HOLE_TOP = 22


def build_frame(style: str = "iphone", device_w: int = REF_W):
    """Return (frame RGBA image, (screen_x, screen_y, screen_w, screen_h))."""
    s = device_w / REF_W
    w = device_w
    h = round(REF_H * s)
    corner_r = round(REF_CORNER_R * s)
    bezel = max(2, round(REF_BEZEL * s))
    screen_r = round(REF_SCREEN_R * s)
    screen_w = w - 2 * bezel
    screen_h = h - 2 * bezel

    frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)

    # Device body (dark grey outer, darker inner)
    fd.rounded_rectangle([0, 0, w - 1, h - 1], radius=corner_r, fill=(30, 30, 30, 255))
    fd.rounded_rectangle([1, 1, w - 2, h - 2], radius=max(1, corner_r - 1), fill=(20, 20, 20, 255))

    # Screen cutout (transparent)
    cutout = Image.new("L", (w, h), 255)
    ImageDraw.Draw(cutout).rounded_rectangle(
        [bezel, bezel, bezel + screen_w, bezel + screen_h], radius=screen_r, fill=0
    )
    frame.putalpha(ImageChops.multiply(frame.getchannel("A"), cutout))

    d = ImageDraw.Draw(frame)
    if style == "android":
        # centered punch-hole camera
        r = max(4, round(REF_HOLE_R * s))
        cy = bezel + round(REF_HOLE_TOP * s) + r
        d.ellipse([w // 2 - r, cy - r, w // 2 + r, cy + r], fill=(0, 0, 0, 255))
    else:
        # iPhone Dynamic Island
        di_w = round(REF_DI_W * s)
        di_h = round(REF_DI_H * s)
        di_x = (w - di_w) // 2
        di_y = bezel + round(REF_DI_TOP * s)
        d.rounded_rectangle([di_x, di_y, di_x + di_w, di_y + di_h], radius=di_h // 2, fill=(0, 0, 0, 255))

    return frame, (bezel, bezel, screen_w, screen_h)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--style", choices=["iphone", "android"], default="iphone")
    p.add_argument("--out", default="assets/device_frame.png")
    p.add_argument("--width", type=int, default=REF_W)
    args = p.parse_args()
    frame, box = build_frame(args.style, args.width)
    frame.save(args.out)
    print(f"Saved {args.out} ({frame.width}x{frame.height}, screen={box})")


if __name__ == "__main__":
    main()
