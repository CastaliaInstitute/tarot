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

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/assets/major"
RAW_DIR = OUT_DIR / "nanobanana/raw"
SOURCE_DIR = Path(os.getenv("RIDER_WAITE_SOURCE_DIR", "/Users/danielmcshan/GitHub/LAIKA/rider-waite-tarot"))
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

PROMPT = """Use the provided Rider-Waite-Smith source card image as the canonical content reference.

Create a generated circular, round-watch version of the Major Arcana card "{title}" for Astrolabe.

Output requirements:
- Square image for a 466x466 round display.
- The artwork must be newly recomposed for a circle, not a crop and not a rectangular card pasted into a circle.
- Remove the rectangular card frame, title strip, inner border, and printed caption from the source image.
- Extend the source scene outward so the landscape, sky, floor, architecture, vegetation, water, and atmosphere continue naturally to the circular edge.
- Do not leave a visible rectangle, card mat, border shadow, framed poster, or blurred duplicate of the original card behind the subject.
- Preserve the source card's exact subject matter: character count, posture, gestures, key objects, symbolic animals/plants/tools, landscape, color identity, and visual hierarchy.
- Keep the same narrative content as the source card while adapting placement and proportions for a circular composition.
- Important symbols must sit inside the safe central 88% diameter.
- No modern objects, no extra labels, no title banner, no card border, no watermark, no border text.
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
        canvas = ImageOps.fit(
            im.convert("RGBA"),
            (466, 466),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        canvas.putalpha(circular_mask(466))
        full_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(full_path, optimize=True)
        half = canvas.resize((233, 233), Image.Resampling.LANCZOS)
        half_path.parent.mkdir(parents=True, exist_ok=True)
        half.save(half_path, optimize=True)


def source_path_for(slug: str) -> Path:
    return SOURCE_DIR / f"major_arcana_{slug}.png"


def image_part(path: Path) -> dict:
    return {
        "inlineData": {
            "mimeType": "image/png",
            "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        }
    }


def generate_image(api_key: str, model: str, prompt: str, source_path: Path) -> bytes:
    body = {
        "contents": [{"parts": [image_part(source_path), {"text": prompt}]}],
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
            "source": str(SOURCE_DIR),
            "note": "Generated with Gemini Nano Banana from Rider-Waite source-image references, then resized and circular-alpha masked for Astrolabe.",
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
    global SOURCE_DIR

    parser = argparse.ArgumentParser()
    parser.add_argument("--card", default="all", help="all, a slug, a number, or comma-separated values")
    parser.add_argument("--model", default=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"))
    parser.add_argument("--source-dir", default=str(SOURCE_DIR), help="Directory containing major_arcana_<slug>.png")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between API calls")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling Gemini")
    args = parser.parse_args()

    SOURCE_DIR = Path(args.source_dir).expanduser().resolve()
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
        source_path = source_path_for(slug)
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        print(f"[{index}/{len(cards)}] {title} -> {filename}")
        if args.dry_run:
            print(f"Source: {source_path}")
            print(prompt)
            continue
        raw_path.write_bytes(generate_image(api_key or "", args.model, prompt, source_path))
        postprocess(raw_path, full_path, half_path)
        if index < len(cards) and args.sleep > 0:
            time.sleep(args.sleep)

    if not args.dry_run:
        write_manifest(args.model, cards)
        build_contact_sheet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
