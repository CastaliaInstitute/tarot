#!/usr/bin/env python3
"""Build round Astrolabe Major Arcana assets from local Rider-Waite sources."""

from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/assets/major"
SOURCE_DIR = Path(os.getenv("TAROT_SOURCE_DIR", str(ROOT / "source/rider-waite/major")))

CARDS = [
    (0, "The Fool", "fool"),
    (1, "The Magician", "magician"),
    (2, "The High Priestess", "priestess"),
    (3, "The Empress", "empress"),
    (4, "The Emperor", "emperor"),
    (5, "The Hierophant", "hierophant"),
    (6, "The Lovers", "lovers"),
    (7, "The Chariot", "chariot"),
    (8, "Strength", "strength"),
    (9, "The Hermit", "hermit"),
    (10, "Wheel of Fortune", "fortune"),
    (11, "Justice", "justice"),
    (12, "The Hanged Man", "hanged"),
    (13, "Death", "death"),
    (14, "Temperance", "temperance"),
    (15, "The Devil", "devil"),
    (16, "The Tower", "tower"),
    (17, "The Star", "star"),
    (18, "The Moon", "moon"),
    (19, "The Sun", "sun"),
    (20, "Judgement", "judgement"),
    (21, "The World", "world"),
]


def circular_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def make_round_card(src: Image.Image, size: int) -> Image.Image:
    src = ImageOps.exif_transpose(src).convert("RGB")

    # Full-bleed backdrop keeps the round watch face visually filled while the
    # original rectangular card remains legible in the center.
    bg = ImageOps.fit(src, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    bg = bg.filter(ImageFilter.GaussianBlur(max(2, size // 36)))
    bg = Image.blend(bg, Image.new("RGB", (size, size), (18, 16, 22)), 0.22)

    margin = max(10, round(size * 0.045))
    fg_h = size - (2 * margin)
    fg_w = round(fg_h * src.width / src.height)
    if fg_w > size - (2 * margin):
        fg_w = size - (2 * margin)
        fg_h = round(fg_w * src.height / src.width)
    fg = src.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

    x = (size - fg_w) // 2
    y = (size - fg_h) // 2
    bg.paste(fg, (x, y))

    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring)
    inset = max(2, size // 110)
    ring_draw.ellipse(
        (inset, inset, size - inset - 1, size - inset - 1),
        outline=(230, 206, 120, 210),
        width=max(2, size // 90),
    )

    out = bg.convert("RGBA")
    out.alpha_composite(ring)
    out.putalpha(circular_mask(size))
    return out


def main() -> int:
    full_dir = OUT_DIR / "full"
    half_dir = OUT_DIR / "half"
    full_dir.mkdir(parents=True, exist_ok=True)
    half_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "deck": "rider-waite-round",
        "arcana": "major",
        "target": "Astrolabe 466x466 round display",
        "variants": {
            "full": {"diameter_px": 466, "path": "full"},
            "half": {"diameter_px": 233, "path": "half"},
        },
        "source": {
            "name": "Rider-Waite-Smith Major Arcana",
            "path": "source/rider-waite/major",
        },
        "generator": {
            "script": "scripts/build_round_tarot_major.py",
            "note": "Local circular composition from Rider-Waite source images. Nano Banana generation was not run because no Gemini credential is configured locally.",
        },
        "cards": [],
    }

    for number, title, slug in CARDS:
        src_path = SOURCE_DIR / f"{number:02d}-{slug}.jpg"
        if not src_path.exists():
            src_path = SOURCE_DIR / f"{number:02d}-{slug}.png"
        if not src_path.exists():
            src_path = SOURCE_DIR / f"major_arcana_{slug}.png"
        if not src_path.exists():
            raise FileNotFoundError(src_path)

        with Image.open(src_path) as src:
            full = make_round_card(src, 466)
            half = full.resize((233, 233), Image.Resampling.LANCZOS)

        filename = f"{number:02d}-{slug}.png"
        full.save(full_dir / filename, optimize=True)
        half.save(half_dir / filename, optimize=True)
        manifest["cards"].append(
            {
                "number": number,
                "title": title,
                "slug": slug,
                "source": f"source/rider-waite/major/{number:02d}-{slug}.jpg",
                "full": f"full/{filename}",
                "half": f"half/{filename}",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {len(CARDS)} full and {len(CARDS)} half assets under {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
