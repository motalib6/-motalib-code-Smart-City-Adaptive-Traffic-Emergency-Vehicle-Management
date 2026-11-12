"""Regenerate the PWA icons (public/icons/*.png).

The PNG icons are binary, so they are NOT stored in the GitHub snapshot
push — run this once after cloning (needs Pillow: pip install pillow):

    python scripts/generate_pwa_icons.py

Then rebuild: npm run build
"""
from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "public", "icons")
os.makedirs(OUT, exist_ok=True)


def icon(size, fname):
    img = Image.new("RGB", (size, size), (11, 18, 32))
    d = ImageDraw.Draw(img)
    m = size // 8
    d.rounded_rectangle([m, m, size - m, size - m], radius=size // 6, fill=(21, 198, 179))
    cx = size // 2
    for i, col in enumerate([(220, 38, 38), (234, 179, 8), (34, 197, 94)]):
        y = size // 4 + i * (size // 4)
        d.ellipse([cx - size // 10, y - size // 10, cx + size // 10, y + size // 10], fill=col)
    img.save(os.path.join(OUT, fname))


icon(192, "icon-192.png")
icon(512, "icon-512.png")
icon(512, "icon-maskable-512.png")
print("icons written to", OUT)
