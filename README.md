# PokerVision AI

Local Windows desktop application for Texas Hold'em observation, manual equity calculation, and offline hand review. **No mouse clicks, keyboard injection, betting automation, or game control.** Live observation has no strategy panel or betting recommendations.

## Run on this computer

```powershell
cd 'C:\Рабочий стол\pp1\PokerVisionAI'
.\.venv\Scripts\python.exe main.py
```

The built folder distribution is `dist/PokerVisionAI/PokerVisionAI.exe`. Keep the entire directory, including `_internal`; the executable alone is not portable. The build includes local RapidOCR ONNX models and runs on CPU without downloads or API keys.

## Install on another Windows 10/11 computer

Check Python versions first:

```powershell
py -0p
```

This build targets 64-bit Python **3.12**. Install it from [python.org](https://www.python.org/downloads/windows/) if it is not available. Select the launcher during installation. Then:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The pinned NumPy version requires Python 3.12; use that interpreter rather than a different installed version. Activation is optional; using the full interpreter path avoids PowerShell execution-policy issues. Development/testing dependencies are in `requirements-dev.txt`. Runtime requires no API keys, cloud service, paid API, or GPU.

## Modes

### Manual calculator

Enter two hole cards (`Ah Kh`, `10h Qs`, or suit symbols) and 0, 3, 4, or 5 community cards. Enter 1–8 opponents. Blank amounts mean **unknown**, not zero. The default opponent assumption is one opponent with a random range; it is labeled as an assumption.

Choose 1,000 / 10,000 / 50,000 / 100,000 simulations. Input edits trigger a debounced calculation. **Cancel** stops ongoing simulation. Duplicate cards, impossible boards, negative/nonfinite amounts, and blocked ranges are rejected.

Ranges support `AA`, `AKs`, `AKo`, `77+`, `AJs+`, `AJo+`, explicit holdings `AhKd`, and comma-separated combinations. Enter one range for all opponents or use `|` to separate one range per opponent. Profiles are **assumptions**, not inferred hidden cards. Combinations are equally weighted. Dash notation and weighted ranges are not supported.

Win means an outright win. Tie means sharing first place. Equity is expected pot share, including `1/n` of a pot shared by `n` winners. Sampling error excludes uncertainty about opponent ranges.

### Live observation

1. Mirror the phone to a visible Windows window.
2. Open **Live observation**, click **Refresh**, select that window, and click **Capture window**.
3. Alternatively enter a physical-pixel rectangle through **Region**, including negative coordinates on monitors to the left of the primary display.
4. Choose 5, 10, 15, or 30 FPS before starting. Use **Pause / resume**, **Stop**, and **Save screenshot** as needed.
5. Edit recognized fields when necessary. Provenance is displayed beside each field. Manual overrides persist during the current tracked hand and clear when a new hand is recognized.

**Capture window** reads the selected window through Pillow's native Windows window capture. This was verified to retrieve LetsView while an editor covered it. Minimized windows are rejected; other mirroring renderers may not support this method. If a window returns a blank image, use **Region** and keep that area unobscured. Region capture uses MSS and reads visible desktop pixels. Neither method sends game controls.

The built-in RST profile locates the portrait felt inside the mirror, removes the toolbar/side margins from the coordinate system, and maps preview boxes back to the original frame. `auto_table_crop: false` disables this for a custom layout. If the table is not found, the state stays unknown. Live mode displays a recognized board and amounts even when hero cards are absent, while withholding equity until the required cards and opponent count are known.

Major card changes require three consecutive valid observations. Contradictory boards and board resets create new hand IDs. Pot changes reuse cached showdown equity. Changes of cards, opponents, or ranges alter the cache key. Intervening hand boundaries with identical cards cannot be guaranteed without visible reset/finished-hand evidence; inspect saved histories.

### Offline review

Load PNG/JPEG/BMP, MP4/AVI/MOV/MKV, or an exported JSON state. Video can be paused and scrubbed; pause before making corrections. Recognition of a new frame clears previous frame corrections. Screenshot/video imports provide observed information; the user must supply missing opponents and assumptions.

**Load media** opens your image using the selected detection layout. The three supplied original screenshots are retained and tested: Qs Th / 3d Ad 4h (pot 60), Jc 4h / Jd 2d Qc (pot 80), and 8c 5s / empty board (pot 1.50, stack 44.50). **RST reference** selects the RST layout and opens the second image. Opponent activity and call amount remain unknown; enter the active opponent count to calculate equity. These images also supply rank calibration, so they are regression checks, not an independent accuracy benchmark.

The **Synthetic demo** selects the generic profile and uses generated artwork, explicitly not an RST screenshot. Switch back through **Detection layout → RST supplied screenshot** before processing RST media. New installations start with the RST profile; existing saved custom layouts are preserved.

For fold/check/call comparison, enter pot and call and confirm both:

- No further betting (terminal decision model).
- Hero is eligible for the whole pot, with no side pots.

Pot includes chips already committed, including the opponent's bet, and excludes hero's pending call. Pot odds = `call / (pot + call)`. Call EV = `equity × (pot + call) − call`. Past contributions are sunk. These values ignore rake and ICM. A check EV is computed only in the explicitly terminal model.

For heads-up bet/raise comparisons also enter effective stack, candidate additional investments, assumed fold probability (0–1), and a **separate calling range**. Calling equity is simulated against that range. The model permits only fold/call responses, assumes no further bets or reraises, and does not validate the site's minimum legal raise. A comparison is not a claim of full-game optimal play. Multiway aggression EV is deliberately unavailable.

The Python API supports contribution-based side-pot construction and EV using separate equities for each eligible pot (`poker/pot_odds.py`, `poker/expected_value.py`). The GUI does not infer contributions or automatically calculate side-pot equities. Unmatched excess is treated as a refund. Do not use whole-pot call EV for a partially eligible all-in.

## Mirroring

For Android, [scrcpy](https://github.com/Genymobile/scrcpy) is a free mirroring option. Install its official Windows release, enable USB debugging on your phone, connect by USB, authorize your own computer on the phone, and start scrcpy. PokerVision only observes the mirror; it has no scrcpy control integration.

For iPhone, use an AirPlay receiver or a USB mirroring product that already displays your phone in a Windows window. Establish mirroring first, then select that window. This project does not include an iOS mirroring driver or guarantee compatibility with every receiver. Some receivers may be paid; PokerVision itself does not require one specific product.

## Recognition and calibration — read before using RST images

All three supplied originals are retained as `assets/screenshots/rst_reference_1.png` through `rst_reference_3.png`. The third is the user's `frame.png`. Normal **Load media** imports are tested as well as direct pipeline recognition. An unchanged saved layout from the previous built-in RST profile is upgraded automatically; custom coordinates are preserved.

The RST layout scales by **image width**, using `reference_size: [493, 1077]`; the optional bottom action panel does not stretch the table coordinates. A test crops reference 2 to 985 pixels tall and verifies unchanged card/amount coordinates; this crop is not the first original screenshot. Fixed card slots handle the small hero cards touching the pale panel. The pipeline normalizes scaled images to the reference width. Cards were checked at 75%, 150%, and 200% scale; small numeric labels can return unknown at noninteger scales. Borders around a mirrored phone and genuinely different UI arrangements still require calibration.

**Detection layout** edits validated JSON with `x, y, w, h` in 0–1 reference coordinates. Profiles without `reference_size` retain the legacy full-frame normalized behavior. The preview draws resolved zones. Add `seat_5` through `seat_8`, corresponding `stack_5`/`stack_8`, `bet_1`, etc., or `call_amount` if applicable. A call amount is accepted only with actual turn controls, never pre-action controls.

Card detection uses calibrated slots for RST and light-card contours for generic layouts. The RST recognizer isolates the rank glyph, normalizes its size, and reads the four-color suit from its ink: blue diamonds, green clubs, red hearts, black spades. Rank recognition is independent of the court artwork. Nine observed ranks have templates: **2, 3, 4, 5, 8, T, J, Q, A**. When no template matches confidently, local OCR accepts only an exact rank with confidence at least 0.94, including **6, 7, 9, K**. These four fallback ranks have independent rendered-font tests, not real RST image coverage. Add tightly cropped variants through **Add card template** for the whole-card fallback. Rotated/overlapping cards, different corner positions, and other themes may return unknown. Scores are not calibrated accuracy probabilities. Duplicates and partial sets are rejected. An unreadable board is kept distinct from an observed empty board, and calculation is blocked until it is corrected.

Table detection uses a colored-felt rectangle with portrait aspect, size and fill checks. The RST profile uses it to offset/scale the coordinates inside a mirror window. Generic/custom profiles can leave this disabled. Player stacks and explicit status text provide limited evidence: visible avatars/stacks do not imply active opponents. Unknown activity remains unknown, so live equity requires an entered opponent count when activity cannot be established. Dealer detection only accepts explicit text evidence; graphical dealer icons are not trained. No YOLO weights are bundled.

Pre-action labels such as **Check/Fold**, **Check**, and **Call Any** are distinguished from actual betting controls by text OCR. The supplied RST panel also has a visual template: all three control columns must match. A plain gray panel, a cropped-away panel, or changed controls do not suffice. The template fallback never classifies a player's actual turn or supplies a call amount.

### OCR

The RST profile uses **RapidOCR + ONNX Runtime**, with bundled models, CPU inference, and no runtime network calls. Numeric fields use single-line recognition; action and player-status regions use text detection. Wider regions include the complete pot label and shifted stack text. Decimal and compact amounts are parsed (`1.50 → 1.5`, `1.20K → 1200`). Tests cover all three originals plus independently rendered unseen amounts. Uncertain readings return unknown. OCR results are cached for unchanged regions; processing a new frame can take several seconds on CPU even when capture runs faster.

The generic/synthetic profile retains numeric template OCR. If the neural backend fails to load, it falls back to these limited templates with a visible warning. Model files come from [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) via `rapidocr-onnxruntime`.

Optional EasyOCR improves general text coverage and adds English/Russian action labels:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
.\.venv\Scripts\python.exe scripts/setup_ocr.py
```

This optional setup downloads model weights once and may install large Torch dependencies. It is unnecessary for the bundled RapidOCR backend. Set `use_easyocr` to `true` only when explicitly choosing EasyOCR. The optional EasyOCR backend was not evaluated or included in the executable. See [models/README.md](models/README.md) for packaging implications.

## History and privacy

**Save analysis** stores state, provenance, probabilities, range assumptions, conditional explanations, corrections, and available tracked events in SQLite. Completed live hand boundaries automatically save their observed event history. Use **Saved hands** to reopen a state in offline review, then **Export last save** for JSON or CSV. A saved state can be recalculated with different assumptions; no decisions are sent to the game.

Default location: `%LOCALAPPDATA%\PokerVisionAI` (database, layout, user templates, optional model files). Set `POKERVISION_DATA` to another writable directory before starting. Media frames are saved only when explicitly requested; the application does not record video. Close the application before copying the SQLite database for backup.

## Verification and packaging

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/benchmark.py --simulations 10000
.\.venv\Scripts\python.exe scripts/smoke_gui.py
.\.venv\Scripts\python.exe scripts/build_exe.py
```

`scripts/smoke_gui.py` uses Qt offscreen and writes `artifacts/manual-calculator.png`. `scripts/smoke_rst.py` loads all three originals through the normal UI path and writes `artifacts/rst-review-1.png` through `rst-review-3.png`, with recognized-state JSON beside each. `scripts/smoke_desktop.py` checks Win32/MSS capture on an interactive Windows desktop. `PokerVisionAI.exe --smoke-test` verifies a three-way split and all three original screenshots using the packaged OCR models, writes diagnostic files into the data directory, and exits automatically.
    
Build output: `dist/PokerVisionAI/PokerVisionAI.exe`. Assets resolve relative to PyInstaller's resource directory; writable settings remain outside the bundle. See `VALIDATION.md` for measured results and unverified areas. No performance or accuracy promises apply across machines.

## Architecture

`poker/` contains input validation, the Treys evaluator, range expansion, rejection-sampled Monte Carlo, bounded caching, pot arithmetic, and conditional strategy analysis. Multiway ranges are independently drawn and jointly rejected on collisions, avoiding sequential-renormalization bias. `capture/` owns read-only sources. `vision/` owns conservative recognition. `tracking/` handles temporal consistency. `gui/` uses worker threads and a latest-frame mailbox. `storage/` owns SQLite and exports. Optional OCR imports are lazy; the manual calculator does not require capture or model weights.

External implementation references: [Treys](https://github.com/ihendley/treys), [Qt QThread documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html), [EasyOCR](https://github.com/JaidedAI/EasyOCR). The specified RST website could not be retrieved during development; no page assets were copied.
