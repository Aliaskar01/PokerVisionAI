# Validation record

Validated on Windows 11, Python 3.12.5. LetsView-fix source test run: **138 passed in 37.17 seconds** (`python -m pytest -q`).

## LetsView capture and partial observation fix

An actual LetsView window was captured using Pillow's native window capture while covered by the editor. Saved original: `assets/screenshots/letsview_reference_4.png` (495×1130). This image was **not** used to extract rank templates. The pipeline detects a 50-pixel toolbar and reads **5s 4d / Qs 8c Jd, pot 4, hero stack 18**. This is one additional real-image check, not a population accuracy estimate. Lower opponent stacks and the pre-action panel remain unknown on this frame.

Regression tests additionally cover toolbar/side padding at 289, 493 and 740 pixels width, preview-coordinate mapping, a spectator with no visible hero cards, partial live-state display and restoration, no-table rejection, and migration of the previous built-in layout. Exact-rank OCR fallback for 6, 7, 9, K passes independent rendered-font tests; real RST examples of these ranks remain unverified.

Native end-to-end window capture **PASS**: `scripts/smoke_letsview.py --fixture` creates a separate native window displaying the saved LetsView frame, then captures it through the actual `CaptureWorker`, vision worker and live GUI. Verified fields: 5s 4d / Qs 8c Jd, pot 4, stack 18. Evidence: `artifacts/letsview-live.png`, `letsview-live-source.png`, `letsview-live-state.json`. The final fixture uses a smoothly resized 600-pixel-high image; an earlier 500-pixel nearest-neighbor fixture degraded tiny glyphs and was not recognized reliably. Low-resolution mirroring remains a limitation. This fixture is not an ongoing connection to the user's phone.

Packaged LetsView smoke checks four source frames plus live partial-state display and the split-equity calculation. The first build passed in `data/packaged-letsview-smoke`; the final-build evidence is recorded separately in `data/packaged-letsview-final`. Profile migration was additionally checked after preserving an explicit user choice to disable automatic cropping: five targeted tests passed.

## Automated coverage

- All ten displayed hand categories, wheel straight, kicker ordering, tied ranks, invalid duplicate cards.
- Seeded preflop/flop/turn/river simulations, 1–8 opponents, split-pot equity, exact opponent holdings, blocked/incompatible ranges, cancellation.
- Range expansion counts, cache reuse, finite nonnegative pot inputs, terminal-call EV, heads-up aggression model, eligible side pots, strategy mode/assumption guards.
- All 52 **synthetic** card assets, synthetic screenshot end-to-end, unknown and duplicate predictions, numeric OCR image tests, compact-number parsing, confidence rejection, pre-action classification.
- All three user-supplied original RST images: Qs Th / 3d Ad 4h, pot 60, stack 380; Jc 4h / Jd 2d Qc, pot 80, stack 380; 8c 5s / empty board, pot 1.50, stack 44.50. Visible opponent stacks are checked for all three. Ordinary GUI imports verify the old saved profile migrates and the recognized fields appear.
- Local neural OCR reads independently rendered amounts 108.25, 2.35K and 976.40 without using calibrated numeric glyphs. A rank learned from a small hero card transfers to a larger board card; recoloring and translating the observed 8 produces an unseen 8h combination that is recognized.
- Unreadable community cards retain an unknown board state instead of silently becoming preflop. The calculation guard, manual correction, empty-board UI, state round trip, and exact-only built-in layout migration are tested.
- RST card recognition at 75%, 150%, and 200%; height changes without moving table coordinates; card permutation; duplicate rejection; erased amounts; blank action panels; four-color suit mismatches. Small OCR labels may be unknown at fractional scales.
- Temporal smoothing, reset detection, finished-hand markers, SQLite round trips, JSON/CSV export.
- Qt offscreen startup, source list, manual entry, asynchronous probability display, cancellation, imported screenshot, synthetic AVI pause and seek.

Native Win32/MSS smoke test captured **17 frames without errors** from a temporary synthetic desktop window. `artifacts/native-capture.txt` and `artifacts/native-capture.png` contain the evidence. This verifies the capture plumbing, not a particular phone-mirroring program.

The final PyInstaller folder distribution built successfully. **The packaged Windows executable launched, calculated the expected one-third equity on a three-way board royal flush, wrote PASS, and exited with code 0.** Evidence: `data/packaged-smoke/smoke-result.txt` and `data/packaged-smoke/smoke-window.png`. Optional EasyOCR is excluded from this build.

The current source UI smoke test loads all three originals through **Load media**. Renderings are in `artifacts/rst-review-1.png` through `rst-review-3.png`; recognized fields are in the corresponding `rst-recognition-1.json` through `rst-recognition-3.json`. The current packaged smoke test checks all three originals and requires the RapidOCR backend to load successfully, in addition to the one-third equity calculation.

**Previous recognition-fix EXE: PASS, exit code 0.** Historical evidence: `data/packaged-recognition-smoke/smoke-result.txt` and `smoke-recognition.json`. The ordinary-import GUI tests were additionally rerun after adding a full calculation from reference 3 with an explicitly entered count of four opponents: **2 passed in 13.02 seconds**. All three source UI renderings were regenerated successfully.

`artifacts/manual-calculator.png` is an actual Qt widget rendering. The font fallback explicitly loads the installed Windows Segoe UI font when Qt's offscreen backend cannot enumerate system fonts.

## Measured CPU benchmark

Command: `python scripts/benchmark.py --simulations 10000`.
Hand: Ah Kh; board: Qh Jh 2c; random opponent ranges; seed 42.

| Opponents | Time (seconds) | Simulations / second |
|---|---:|---:|
| 1 | 0.330 | 30,260 |
| 3 | 0.641 | 15,605 |
| 8 | 2.085 | 4,796 |

Single local run, not a cross-machine guarantee. More overlapping custom ranges can be slower because joint rejection sampling is needed to avoid biased distributions.

## Explicitly unverified or limited

All three originals are available and tested. **These same images supply rank templates and regression expectations, so this is not held-out recognition accuracy.** The transformation and independent OCR-string tests check specific generalization properties, not broad accuracy on unseen poker screenshots.

Unseen RST cards/artwork, animations, folded avatars, graphical dealer buttons, and mirroring products other than the captured LetsView window remain unverified. Rank templates cover 2, 3, 4, 5, 8, T, J, Q, A; OCR fallback for real ranks 6, 7, 9, K still needs real-image validation. Numeric recognition is conservative at low resolution and fractional scaling. New-frame OCR took roughly 4–5.5 seconds in one local source run; unchanged region results are cached. Capture FPS is not recognition throughput.

RapidOCR 1.4.4 and ONNX Runtime 1.31.1 are installed and tested with their bundled CPU models. Runtime makes no model downloads. EasyOCR/Torch remains optional, untested, and excluded from the build. Numeric-template OCR remains a limited fallback with a visible error if neural OCR fails.

Side-pot construction and supplied per-pot EV are available in the Python API; automatic contribution inference and a side-pot GUI are absent. Bet/raise comparisons use a terminal heads-up fold/call model and do not model future streets or reraises. The program is not a poker solver.

The template recognizer is a calibrated-layout baseline; it does not include trained YOLO models, robust rotated-card segmentation, or an avatar classifier. Unknown evidence stays unknown; manually correct it before calculation.
