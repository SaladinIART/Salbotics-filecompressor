# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.4 added optional ImageMagick image routing:

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
- libvips and LibreOffice are discovery-only until CP6.5+.
- Tests pass.

## Canonical Terms

- `target_kb`: requested maximum output size in binary kilobytes, default `499`.
- `preserve-text pass`: Ghostscript `pdfwrite` compression that keeps text
  selectable when possible.
- `raster fallback`: render PDF pages as images, then rebuild an image-only PDF.
- `PDF cleanup pass`: qpdf or mutool structural cleanup that may shrink a PDF
  without rasterizing or changing color.
- `extended image route`: ImageMagick path for WebP/BMP/TIF/TIFF input.
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

## Next Checkpoint: CP6.5

CP6.5 should improve output quality decisions and avoid worse/larger outputs.

## CP6.5 Master List

- Compare candidate size against original before saving warning outputs.
- Consider keeping original/copy when best candidate is larger and force optimize
  is off.
- Add mode-specific notes for when target cannot be reached.
- Preserve current qpdf/mutool/ImageMagick fallback tests.
- Keep GUI simple; no new controls unless needed.
