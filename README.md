# Castalia Tarot

Round Rider-Waite-Smith tarot assets for Astrolabe and Castalia interfaces.

Site: https://tarot.castalia.institute/

## Assets

- Major Arcana full Astrolabe display: `docs/assets/major/full/*.png` at 466x466 RGBA.
- Major Arcana half-diameter display: `docs/assets/major/half/*.png` at 233x233 RGBA.
- Manifest: `docs/assets/major/manifest.json`.
- Nano Banana prompt sheet: `docs/assets/major/nano-banana-prompts.md`.

The current assets are local circular compositions from the Rider-Waite source deck. The prompt sheet captures the intended Nano Banana recomposition pass once Gemini credentials are available.

## Generate With Nano Banana

The repo includes a manually dispatched GitHub Action, **Generate Nano Banana Tarot**, that uses the organization secret `GEMINI_API_KEY` or `GOOGLE_GEMINI_API_KEY`.

Inputs:

- `card`: `all`, a card slug such as `fool`, a number such as `00`, or a comma-separated list.
- `model`: defaults to `gemini-2.5-flash-image`.
- `commit`: commits generated files back to `main` when enabled.

Generated files replace the existing `docs/assets/major/full` and `docs/assets/major/half` PNGs, update the manifest, and refresh the contact sheet.

## Rebuild

```bash
python3 scripts/build_round_tarot_major.py
```
