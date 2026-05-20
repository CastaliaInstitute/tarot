#!/usr/bin/env python3
"""Generate round Major Arcana assets with Gemini Nano Banana."""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/assets/major"
RAW_DIR = OUT_DIR / "nanobanana/raw"
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

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

PROMPT = """Create a circular, round-watch version of the Rider-Waite-Smith Major Arcana card "{title}" for Astrolabe.

Output requirements:
- Square image for a 466x466 round display.
- The artwork must fill the full circular composition, not a rectangular card pasted into a circle.
- Preserve the card's canonical Rider-Waite-Smith symbolism, character count, posture, key objects, and color identity.
- Recompose the scene naturally for a circular crop with important symbols inside the safe central 88% diameter.
- No modern objects, no extra labels, no watermark, no border text.
- Rich but legible at watch scale; strong silhouettes, clean edges, high contrast.
- Keep the style close to Pamela Colman Smith linework and flat watercolor, with slightly cleaner edges for small displays.
"""


def circular_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def postprocess(src_path: Path, full_path: Path, half_path: Path) -> None:
    with Image.open(src_path) as im:
        square = im.convert("RGBA")
        square.thumbnail((466, 466), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (466, 466), (0, 0, 0, 0))
        x = (466 - square.width) // 2
        y = (466 - square.height) // 2
        canvas.alpha_composite(square, (x, y))
        canvas.putalpha(circular_mask(466))
        full_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(full_path, optimize=True)
        half = canvas.resize((233, 233), Image.Resampling.LANCZOS)
        half_path.parent.mkdir(parents=True, exist_ok=True)
        half.save(half_path, optimize=True)


def generate_image(api_key: str, model: str, prompt: str) -> bytes:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "1:1"},
        },
    }
    req = urllib.request.Request(
        f"{API_ROOT}/{model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Gemini API error {exc.code}: {detail}") from exc

    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError(f"No image returned by Gemini: {json.dumps(data)[:1200]}")


def selected_cards(selection: str) -> list[tuple[int, str, str]]:
    if selection == "all":
        return CARDS
    wanted = {item.strip().lower() for item in selection.split(",") if item.strip()}
    cards = [
        card for card in CARDS
        if f"{card[0]:02d}" in wanted or str(card[0]) in wanted or card[2] in wanted
    ]
    if not cards:
        raise ValueError(f"No cards matched selection: {selection}")
    return cards


def write_manifest(model: str, cards: list[tuple[int, str, str]]) -> None:
    manifest = {
        "deck": "rider-waite-round",
        "arcana": "major",
        "target": "Astrolabe 466x466 round display",
        "variants": {
            "full": {"diameter_px": 466, "path": "full"},
            "half": {"diameter_px": 233, "path": "half"},
        },
        "generator": {
            "script": "scripts/generate_nano_banana_major.py",
            "model": model,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": "Generated with Gemini Nano Banana, then resized and circular-alpha masked for Astrolabe.",
        },
        "cards": [
            {
                "number": number,
                "title": title,
                "slug": slug,
                "full": f"full/{number:02d}-{slug}.png",
                "half": f"half/{number:02d}-{slug}.png",
            }
            for number, title, slug in CARDS
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def build_contact_sheet() -> None:
    files = sorted((OUT_DIR / "full").glob("*.png"))
    thumb = 116
    cols = 6
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * thumb, rows * thumb), (20, 20, 24, 255))
    for i, path in enumerate(files):
        with Image.open(path) as im:
            tile = im.convert("RGBA").resize((thumb, thumb), Image.Resampling.LANCZOS)
        sheet.alpha_composite(tile, ((i % cols) * thumb, (i // cols) * thumb))
    sheet.convert("RGB").save(OUT_DIR / "contact-sheet-full.jpg", quality=88, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--card", default="all", help="all, a slug, a number, or comma-separated values")
    parser.add_argument("--model", default=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"))
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between API calls")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling Gemini")
    args = parser.parse_args()

    cards = selected_cards(args.card)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        raise SystemExit("Set GEMINI_API_KEY or GOOGLE_GEMINI_API_KEY")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for index, (number, title, slug) in enumerate(cards, start=1):
        prompt = PROMPT.format(title=title)
        filename = f"{number:02d}-{slug}.png"
        raw_path = RAW_DIR / filename
        full_path = OUT_DIR / "full" / filename
        half_path = OUT_DIR / "half" / filename
        print(f"[{index}/{len(cards)}] {title} -> {filename}")
        if args.dry_run:
            print(prompt)
            continue
        raw_path.write_bytes(generate_image(api_key or "", args.model, prompt))
        postprocess(raw_path, full_path, half_path)
        if index < len(cards) and args.sleep > 0:
            time.sleep(args.sleep)

    if not args.dry_run:
        write_manifest(args.model, cards)
        build_contact_sheet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
