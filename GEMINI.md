# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.5 added output quality safeguards:

- project root: `C:\Users\salbot01\Salbotics\Salbotics-filecompressor`
- Python package: `salbotics_filecompressor`
- CLI command: `salbotics-filecompressor`
- app display name: `Salbotics File Compressor`
- `engine_registry.py` detects Pillow, Ghostscript, qpdf, mutool, ImageMagick,
  libvips, and LibreOffice.
- CLI exposes `--list-engines` and `--list-formats`.
- CLI exposes `--force-optimize` and `--quality-mode safe|smart|aggressive`.
- GUI exposes Force optimize and Safe/Smart/Aggressive quality mode controls.
- Default behavior still copies under-target files unless force optimize is on.
- Smart mode tries gentler near-target image/PDF candidates first.
- Safe PDF mode avoids raster fallback.
- PDF routing now tries qpdf cleanup, then mutool cleanup, then Ghostscript.
- qpdf/mutool cleanup is skipped when grayscale is requested because those
  tools do not perform color conversion.
- Image routing uses Pillow for JPG/JPEG/PNG.
- Image routing uses optional ImageMagick for WebP/BMP/TIF/TIFF.
- ImageMagick is detected from `PATH` as `magick` or from
  `SALBOTICS_FILECOMPRESSOR_MAGICK`.
- Same-format outputs keep the original when every compression candidate is
  larger or equal.
- Target-miss warnings include the selected mode that produced the saved
  best-effort candidate.
- Image-to-PDF still saves the requested PDF output even when the converted PDF
  is larger than the original image.
- libvips and LibreOffice are discovery-only until CP6.6+.
- Tests pass.

## Canonical Terms

- `target_kb`: requested maximum output size in binary kilobytes, default `499`.
- `preserve-text pass`: Ghostscript `pdfwrite` compression that keeps text
  selectable when possible.
- `raster fallback`: render PDF pages as images, then rebuild an image-only PDF.
- `PDF cleanup pass`: qpdf or mutool structural cleanup that may shrink a PDF
  without rasterizing or changing color.
- `extended image route`: ImageMagick path for WebP/BMP/TIF/TIFF input.
- `keep original safeguard`: copy the original output when same-format
  compression would not reduce file size.
- `best effort`: save the best readable output even when target is missed.

## Decisions Locked

- Windows target.
- Tkinter GUI.
- CLI plus GUI.
- Ghostscript required for real PDF compression.
- qpdf/mutool are optional and must not be required to run the app.
- ImageMagick is optional and must not be required for JPG/JPEG/PNG or PDF work.
- Ghostscript is credited to Artifex Software, Inc.; do not imply endorsement.
- Ghostscript is not bundled.
- Default target is 499 KB, editable by user.
- Grayscale is opt-in.
- Password-protected PDFs unsupported in v1.
- JPG/JPEG/PNG supported by built-in Pillow path.
- WebP/BMP/TIF/TIFF supported when ImageMagick is installed.
- Image output mode is user-selectable: same format or PDF.
- Same-format compression should not save a larger file over a smaller original.

## Next Checkpoint: CP6.6

CP6.6 should improve real-world validation and packaged smoke tests.

## CP6.6 Master List

- Add sample-driven smoke tests for image compression paths.
- Add optional ImageMagick smoke test that skips cleanly when missing.
- Add a release-build verification checklist.
- Consider a small synthetic PDF/image fixture set if repo size remains tiny.
- Preserve current unit tests and GUI simplicity.
