#!/usr/bin/env python3
"""Render cafe-base.png with the collision rects overlaid for visual debugging."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "assets/maps/cafe-base.png"
COLL = ROOT / "data/cafe-collision.json"
OUT = ROOT / "tools/_collision_overlay.png"

data = json.loads(COLL.read_text())
img = Image.open(MAP).convert("RGBA")
W, H = img.size

overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
d = ImageDraw.Draw(overlay)

wb = data["walk_bounds"]
d.rectangle([wb["x"], wb["y"], wb["x"]+wb["w"], wb["y"]+wb["h"]], outline=(0, 255, 0, 255), width=4)

for i, r in enumerate(data["blocked_rects"]):
    d.rectangle([r["x"], r["y"], r["x"]+r["w"], r["y"]+r["h"]],
                fill=(255, 0, 0, 35), outline=(255, 60, 60, 255), width=3)

# Draw 64-px grid for reference
for x in range(0, W, 64):
    d.line([(x, 0), (x, H)], fill=(255, 255, 255, 60), width=1)
for y in range(0, H, 64):
    d.line([(0, y), (W, y)], fill=(255, 255, 255, 60), width=1)

# Coord labels every 128 px
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
except Exception:
    font = ImageFont.load_default()
for x in range(0, W, 128):
    d.text((x+2, 2), str(x), fill=(255, 255, 0, 220), font=font)
for y in range(0, H, 128):
    d.text((2, y+2), str(y), fill=(255, 255, 0, 220), font=font)

# Index labels for each blocked rect
for i, r in enumerate(data["blocked_rects"]):
    d.text((r["x"]+4, r["y"]+4), f"#{i}", fill=(255, 255, 255, 255), font=font)

merged = Image.alpha_composite(img, overlay)
merged.save(OUT)
print(f"wrote {OUT}")
