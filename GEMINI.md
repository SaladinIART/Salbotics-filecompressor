# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.8 built and verified a fresh Windows release package:

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
- GUI now shows compact engine readiness text for Ghostscript and ImageMagick.
- GUI result rows show user-facing notes for target hits, copied originals,
  kept-original safeguards, warnings, skips, and failures.
- GUI has an `Open output folder` button that enables after a successful run.
- Fresh local package was built with `scripts/build_exe.ps1`.
- Package verifier passed for `release/salbotics-filecompressor-windows.zip`.
- Frozen CLI smoke passed for `--list-engines`, `--list-formats`, and JPG
  compression.
- Current package sizes:
  - `dist/salbotics-filecompressor.exe`: 29,375,040 bytes.
  - `dist/salbotics-filecompressor-cli.exe`: 26,274,701 bytes.
  - `release/salbotics-filecompressor-windows.zip`: 55,190,151 bytes.
- Current ZIP SHA256:
  `2DDB7787BB2F66E5196D015BC7C680815C43456C7C378E3C8E96416BA38136E5`.
- libvips and LibreOffice are discovery-only until CP6.9+.
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
- `engine readiness summary`: compact GUI text that shows whether PDF and
  extended-image support are ready.
- `packaged CLI smoke`: validation that runs the frozen CLI executable from
  `dist/` instead of the source package.
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

## Next Checkpoint: CP6.9

CP6.9 should prepare public release notes and publish the next GitHub release.

## CP6.9 Master List

- Decide the release tag, likely `v0.2.0`.
- Draft release notes from CP6.1 through CP6.8.
- Attach `release/salbotics-filecompressor-windows.zip`.
- Include the ZIP SHA256 and external engine notes.
- Verify GitHub release page and repo README after publishing.
