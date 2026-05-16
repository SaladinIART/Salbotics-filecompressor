# Release Checklist

Use this checklist before publishing a new Windows release.

## Validation

- Run unit tests:
  `python -m unittest discover -s tests -v`
- Run built-in image smoke tests:
  `python scripts/smoke_images.py`
- Run real PDF smoke test when Ghostscript is installed:
  `python scripts/smoke_real_pdf.py`
- Run CLI discovery checks:
  `salbotics-filecompressor --list-engines`
  `salbotics-filecompressor --list-formats`

## Package

- Build Windows executables:
  `.\scripts\build_exe.ps1`
- Confirm package verifier passes:
  `python scripts\verify_release_package.py`
- Confirm `release\salbotics-filecompressor-windows.zip` exists.

## Manual Smoke

- Open `dist\salbotics-filecompressor.exe`.
- Compress one PDF.
- Compress one JPG/PNG.
- Compress one folder containing a supported file and an unsupported file.
- Confirm warnings are understandable in the results table.

## Publish

- Update `CHANGELOG.md`.
- Push `main` and wait for GitHub Actions.
- Create a GitHub release with the ZIP attached.
- Include engine notes for Ghostscript, qpdf/mutool, and ImageMagick.
