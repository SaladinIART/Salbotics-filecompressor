# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.1 added engine discovery:

- project root: `C:\Users\salbot01\Salbotics\Salbotics-filecompressor`
- Python package: `salbotics_filecompressor`
- CLI command: `salbotics-filecompressor`
- app display name: `Salbotics File Compressor`
- `engine_registry.py` detects Pillow, Ghostscript, qpdf, mutool, ImageMagick,
  libvips, and LibreOffice.
- CLI exposes `--list-engines` and `--list-formats`.
- Current compression routing is unchanged: Ghostscript for PDFs and Pillow for
  JPG/JPEG/PNG.
- Optional engines are discovery-only until CP6.2+.
- Tests pass.

## Canonical Terms

- `target_kb`: requested maximum output size in binary kilobytes, default `499`.
- `preserve-text pass`: Ghostscript `pdfwrite` compression that keeps text
  selectable when possible.
- `raster fallback`: render PDF pages as images, then rebuild an image-only PDF.
- `best effort`: save the best readable output even when target is missed.

## Decisions Locked

- Windows target.
- Tkinter GUI.
- CLI plus GUI.
- Ghostscript required for real PDF compression.
- Ghostscript is credited to Artifex Software, Inc.; do not imply endorsement.
- Ghostscript is not bundled.
- Default target is 499 KB, editable by user.
- Grayscale is opt-in.
- Password-protected PDFs unsupported in v1.
- JPG/JPEG/PNG supported in v1.
- Image output mode is user-selectable: same format or PDF.

## Next Checkpoint: CP6.2

CP6.2 should add smart compression modes and force optimize.

## CP6.2 Master List

- Add `force_optimize` and quality mode options.
- Keep under-target copy behavior unless force optimize is enabled.
- Add near-target smart optimization before full recompression.
- Update GUI with simple Force optimize and Safe/Smart/Aggressive controls.
- Preserve current PDF/image tests.
