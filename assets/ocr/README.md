# RST digit samples

Small binary glyph crops from the user-provided reference 2 supplement the synthetic fonts. The original image and labels are retained under `assets/screenshots`. Rebuild these crops with `scripts/calibrate_rst_reference.py`.

Digits are classified independently, then parsed; the runtime does not return pre-entered screenshot amounts. Tiny decimal points are retained, off-baseline specks are rejected. Fractional scaling or low resolution can still return unknown instead of an amount. This calibration set is not independent test data.
