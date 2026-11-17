# Card templates

The 52 base PNGs are synthetic examples. Five additional `_rst_` PNGs are real crops from the user's second reference image. They cover Jc, 4h, Jd, 2d and Qc. Other RST cards still need examples; synthetic coverage of 52 cards does not establish real RST coverage. Do not interpret match scores as calibrated accuracy probabilities.

Use **Add card template** with a tightly cropped full visible card from your own screenshot. Name it with a standard card code (e.g. `Ah`). Multiple variants are stored in the local data directory. Recognition separately compares the rank and suit sections of the top-left corner, requires both a threshold and a margin over the runner-up, and rejects duplicate/uncertain predictions.

Different card artwork, rotations, overlap, and differing rank/suit placement may require adapting `signature()` and the contour detector. Use manual entry whenever a card is unknown.
