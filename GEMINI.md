# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.6 added validation scripts and release checklist:

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
- `scripts/smoke_images.py` creates temporary JPG/PNG samples and compresses
  them through real Pillow paths.
- `scripts/smoke_images.py` also runs an optional ImageMagick BMP smoke when
  ImageMagick is installed, otherwise it skips cleanly.
- `scripts/verify_release_package.py` validates the local Windows release ZIP.
- `docs/RELEASE_CHECKLIST.md` documents release validation steps.
- GitHub Actions runs unit tests and image smoke tests on Python 3.11, 3.12,
  and 3.13.
- libvips and LibreOffice are discovery-only until CP6.7+.
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
- `smoke test`: generated-sample validation script that exercises installed
  runtime paths without committing binary fixtures.
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

## Next Checkpoint: CP6.7

CP6.7 should improve GUI feedback and result usability.

## CP6.7 Master List

- Add clearer result notes for copy/kept-original/warning outcomes.
- Consider an "Open output folder" button after successful compression.
- Consider a compact engine status summary in the GUI without crowding the form.
- Preserve current CLI behavior and smoke tests.
- Keep GUI simple; avoid adding advanced compression controls.
