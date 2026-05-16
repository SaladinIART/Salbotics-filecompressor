# Changelog

## 0.1.0 - 2026-05-16

- Migrated the original `pdf499` prototype into the centralized Salbotics
  project folder.
- Renamed package to `salbotics_filecompressor`.
- Renamed CLI command to `salbotics-filecompressor`.
- Added GitHub-ready docs and MIT license.
- Preserved PDF-to-PDF compression behavior using Ghostscript.
- Added JPG/JPEG/PNG compression using Pillow.
- Added image-to-PDF output mode.
- Added mixed folder batch behavior with skipped unsupported files.
- Added CLI `--image-output same-format|pdf`.
- Added GUI image output mode and supported file picker.
- Added clean PyInstaller build script for Windows GUI and CLI executables.
- Prepared first Windows release ZIP.
