# Gemini Handoff: Salbotics File Compressor

## Product Goal

Build a Windows Python utility that compresses PDFs and common images toward
target file sizes. The promise is best effort, not guaranteed success for every
file.

## Current Checkpoint

CP5 prepared the first Windows release:

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
- Build script forces project-local `PYTHONPATH` during PyInstaller runs.
- Release ZIP path: `release\salbotics-filecompressor-windows.zip`.
- Packaged CLI smoke passed for JPG, image-to-PDF, and PDF compression.
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

## Next Checkpoint: CP6

CP6 should improve release polish and user-facing packaging.

## CP6 Master List

- Test GUI manually on real user PDFs/images.
- Consider a proper installer instead of ZIP-only distribution.
- Add screenshots or a short user guide.
- Decide whether to bundle or detect Ghostscript more visibly in GUI.
- Consider adding automated GUI smoke testing.
