# Local models

The application requires no GPU. Card detection uses calibrated RST slots or generic white-card contours. RST rank glyphs cover 2, 3, 4, 5, 8, T, J, Q, A from the three supplied originals. Exact high-confidence rank OCR provides a fallback, including 6, 7, 9, K; those ranks have rendered-font tests but still lack real RST validation images. Whole-card templates provide another fallback. An additional native LetsView frame is tested without adding templates from it; broader held-out accuracy remains unmeasured.

The default RST OCR backend is RapidOCR 1.4.4 with ONNX Runtime 1.31.1. Detection/recognition models and configuration come with the installed `rapidocr_onnxruntime` package and are collected into the executable's `_internal/rapidocr_onnxruntime` directory. PyInstaller also bundles ONNX Runtime native libraries. Runtime uses CPU and does not download models. The packaged smoke test requires this backend and verifies all three original images. Numeric-template OCR is retained as a limited fallback with a visible warning.

For EasyOCR, install `requirements-ocr.txt`, run `python scripts/setup_ocr.py` once, and enable `use_easyocr` in Detection layout. The explicit setup command downloads upstream models; normal application runtime disables model downloads. Files live in `%LOCALAPPDATA%/PokerVisionAI/models` (or `POKERVISION_DATA/models`).

The default executable excludes Torch/EasyOCR. To distribute the optional EasyOCR backend, remove the relevant exclusions from the spec, collect EasyOCR/Torch dependencies with PyInstaller, and ship its downloaded models separately after reviewing their licenses. That optional build has not been tested here; it is not needed for bundled RapidOCR.
