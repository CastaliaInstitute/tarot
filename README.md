# Castalia Tarot

Round Rider-Waite-Smith tarot assets for Astrolabe and Castalia interfaces.

Site: https://tarot.castalia.institute/

## Assets

- Major Arcana full Astrolabe display: `docs/assets/major/full/*.png` at 466x466 RGBA.
- Major Arcana half-diameter display: `docs/assets/major/half/*.png` at 233x233 RGBA.
- Manifest: `docs/assets/major/manifest.json`.
- Nano Banana prompt sheet: `docs/assets/major/nano-banana-prompts.md`.

The current assets are local circular compositions from the Rider-Waite source deck. The prompt sheet captures the intended Nano Banana recomposition pass once Gemini credentials are available.

## Rebuild

```bash
python3 scripts/build_round_tarot_major.py
```

