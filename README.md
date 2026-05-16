# Salbotics File Compressor

Salbotics File Compressor is a Windows desktop and CLI utility for compressing
files toward a target size. The current release compresses PDFs, JPG/JPEG/PNG
images, and optional ImageMagick-backed WebP/BMP/TIFF images.

The app is built for local document workflows: pick a file or folder, choose a
target size, and save the best compressed result the engine can produce.

## Status

Current support:

- PDF input and PDF output
- JPG/JPEG/PNG image input through Pillow
- WebP/BMP/TIFF image input through optional ImageMagick
- same-format image output
- image-to-PDF output
- mixed folder batches
- default target size of **499 KB**
- custom target size
- optional grayscale compression
- single-file CLI mode
- Tkinter GUI
- PyInstaller build scripts for Windows executables

## Requirements

- Windows
- Python 3.11+
- Tkinter, included with normal Python installs
- Pillow, installed through package dependencies
- Ghostscript installed separately for real PDF compression
- Optional: qpdf and MuPDF mutool for safe PDF cleanup before Ghostscript
- Optional: ImageMagick for WebP, BMP, TIF, and TIFF inputs

Ghostscript can be found from `gswin64c`, `gswin32c`, `gs`, a normal Windows
install under `C:\Program Files\gs`, or the `SALBOTICS_FILECOMPRESSOR_GS`
environment variable. The legacy `PDF499_GS` variable is accepted during the
prototype migration period.

qpdf and mutool are detected from `PATH` or from
`SALBOTICS_FILECOMPRESSOR_QPDF` and `SALBOTICS_FILECOMPRESSOR_MUTOOL`. They are
not required; if missing or unable to produce a usable result, the app falls
back to Ghostscript.

ImageMagick is detected from `PATH` as `magick` or from
`SALBOTICS_FILECOMPRESSOR_MAGICK`. It is only required for WebP/BMP/TIFF input.

## Install for Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## CLI Usage

```powershell
salbotics-filecompressor input.pdf -o output.pdf --target-kb 499 --grayscale
salbotics-filecompressor photo.jpg -o photo-small.jpg --target-kb 499
salbotics-filecompressor photo.png -o photo.pdf --image-output pdf
salbotics-filecompressor graphic.webp -o graphic-small.webp --target-kb 499
salbotics-filecompressor screenshot.png -o screenshot-small.png --force-optimize --quality-mode smart
salbotics-filecompressor --batch-folder "C:\Files" --output-dir "C:\Compressed" --target-kb 499
salbotics-filecompressor --list-engines
salbotics-filecompressor --list-formats
```

Quality modes:

- `safe`: gentle optimization only, avoids deeper fallback passes.
- `smart`: default; tries low-damage near-target candidates first.
- `aggressive`: adds stronger image candidates when size matters most.

By default, files already under the target are copied. Add `--force-optimize`
to optimize them anyway.

`--list-engines` shows detected local engines such as Pillow, Ghostscript,
qpdf, MuPDF mutool, ImageMagick, libvips, and LibreOffice. qpdf and mutool are
used as optional safe PDF cleanup passes before Ghostscript when available.
ImageMagick is used for optional WebP/BMP/TIFF image compression. libvips and
LibreOffice are discovery-only for future checkpoints.

For local source runs without installing entry points:

```powershell
$env:PYTHONPATH="src"
python -m salbotics_filecompressor.cli input.pdf -o output.pdf
```

## GUI Usage

```powershell
$env:PYTHONPATH="src"
python -m salbotics_filecompressor.gui
```

Choose single-file or folder mode, select an output folder, set the target KB,
pick quality mode and image output mode, then run compression. Use Force
optimize when a file is already under target but you still want a smaller
output. Results appear in the table after processing.

## Development Checks

```powershell
$env:PYTHONPATH="src"
python -m salbotics_filecompressor.cli --help
python -c "from salbotics_filecompressor import CompressionOptions, CompressionResult; print('imports ok')"
python -m unittest discover -s tests -v
python scripts/smoke_real_pdf.py
```

`scripts/smoke_real_pdf.py` creates a temporary sample PDF and compresses it
with real Ghostscript. It prints `SKIP` when Ghostscript is not installed.

## Build Windows EXEs

```powershell
.\scripts\build_exe.ps1
```

The build writes:

```text
dist\salbotics-filecompressor.exe
dist\salbotics-filecompressor-cli.exe
release\salbotics-filecompressor-windows.zip
```

Generated folders are intentionally ignored by Git.

## Release Package

The Windows ZIP contains:

- `salbotics-filecompressor.exe`
- `salbotics-filecompressor-cli.exe`
- `README.md`
- `CREDITS.md`
- `salbotics-filecompressor.ico`

## Credits and Licensing

Project code is MIT licensed. See `LICENSE`.

Salbotics File Compressor uses Ghostscript as its main PDF compression backend.
Ghostscript is developed and licensed by Artifex Software, Inc. Ghostscript is
not bundled with this project, and this project is not endorsed by Artifex.
Optional PDF cleanup can use qpdf or MuPDF mutool when installed locally.

Image compression uses Pillow and optional ImageMagick.

See `CREDITS.md` for attribution and license notes.
