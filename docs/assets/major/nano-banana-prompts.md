# Nano Banana Major Arcana Prompt Sheet

Use model `gemini-2.5-flash-image` or the currently configured Nano Banana image model.

Shared prompt:

```text
Create a circular, round-watch version of the Rider-Waite-Smith Major Arcana card "{CARD_TITLE}" for Astrolabe.

Output requirements:
- Square image for a 466x466 round display.
- The artwork must fill the full circular composition, not a rectangular card pasted into a circle.
- Preserve the card's canonical Rider-Waite-Smith symbolism, character count, posture, key objects, and color identity.
- Recompose the scene naturally for a circular crop with important symbols inside the safe central 88% diameter.
- No modern objects, no extra labels, no watermark, no border text.
- Rich but legible at watch scale; strong silhouettes, clean edges, high contrast.
- Keep the style close to Pamela Colman Smith linework and flat watercolor, with slightly cleaner edges for small displays.
```

Cards:

```text
00 The Fool
01 The Magician
02 The High Priestess
03 The Empress
04 The Emperor
05 The Hierophant
06 The Lovers
07 The Chariot
08 Strength
09 The Hermit
10 Wheel of Fortune
11 Justice
12 The Hanged Man
13 Death
14 Temperance
15 The Devil
16 The Tower
17 The Star
18 The Moon
19 The Sun
20 Judgement
21 The World
```

Post-process generated outputs into:

- `full/{number}-{slug}.png`: 466x466 RGBA, transparent outside the circle.
- `half/{number}-{slug}.png`: 233x233 RGBA, transparent outside the circle.
