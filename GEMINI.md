# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP3 added JPG/JPEG/PNG support:

- project root: `C:\Users\salbot01\Salbotics\Salbotics-filecompressor`
- Python package: `salbotics_filecompressor`
- CLI command: `salbotics-filecompressor`
- app display name: `Salbotics File Compressor`
- PDF compression remains Ghostscript-backed.
- JPG/JPEG/PNG same-format compression uses Pillow.
- JPG/JPEG/PNG can output PDF.
- Folder batches process PDFs and supported images.
- Unsupported batch files are reported as `skipped`.
- CLI exposes `--image-output same-format|pdf`.
- GUI exposes image output mode and supported file picker.
- tests pass.

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

## Next Checkpoint: CP4

CP4 should initialize and publish the source-only GitHub repo.

## CP4 Master List

- Confirm `.gitignore` keeps generated artifacts out.
- Initialize Git if needed.
- Work around invalid `GH_TOKEN` env var by using keyring auth or clearing it
  for the publish command.
- Create public GitHub repo under `SaladinIART/Salbotics-filecompressor`.
- Push source-only main branch.
- Confirm GitHub Actions starts.
