# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP6.9 prepared the v0.2.0 public release:

- project root: `C:\Users\salbot01\Salbotics\Salbotics-filecompressor`
- Python package: `salbotics_filecompressor`
- package version: `0.2.0`
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
- Release target: `v0.2.0`.
- Release notes live at `docs/releases/v0.2.0.md`.
- Fresh v0.2.0 package was built with `scripts/build_exe.ps1`.
- Package verifier passed for `release/salbotics-filecompressor-windows.zip`.
- Frozen CLI smoke passed for `--list-engines`, `--list-formats`, and JPG
  compression.
- Current package sizes:
  - `dist/salbotics-filecompressor.exe`: 29,374,992 bytes.
  - `dist/salbotics-filecompressor-cli.exe`: 26,275,952 bytes.
  - `release/salbotics-filecompressor-windows.zip`: 55,191,035 bytes.
- Current ZIP SHA256:
  `15942B15FDAA7BEFB20087C2A85AFC59D86497FF9F391C152FF7C854A1034BEB`.
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

## Next Checkpoint: CP7.0

CP7.0 should start the next milestone after v0.2.0 is published.

## CP7.0 Master List

- Confirm the published v0.2.0 asset and SHA256.
- Decide next milestone: Office conversion, better GUI workflow, or advanced
  smart image optimization.
- Create issues for the chosen milestone.
- Keep v0.2.0 as the stable public baseline.
