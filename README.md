# Salbotics File Compressor

Salbotics File Compressor is a Windows desktop and CLI utility for compressing
files toward a target size. The current release compresses PDFs plus JPG, JPEG,
and PNG images.

The app is built for local document workflows: pick a file or folder, choose a
target size, and save the best compressed result the engine can produce.

## Status

Current support:

- PDF input and PDF output
- JPG/JPEG/PNG image input
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

Ghostscript can be found from `gswin64c`, `gswin32c`, `gs`, a normal Windows
install under `C:\Program Files\gs`, or the `SALBOTICS_FILECOMPRESSOR_GS`
environment variable. The legacy `PDF499_GS` variable is accepted during the
prototype migration period.

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
salbotics-filecompressor --batch-folder "C:\Files" --output-dir "C:\Compressed" --target-kb 499
```

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
pick image output mode, and run compression. Results appear in the table after
processing.

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

Salbotics File Compressor uses Ghostscript as its PDF compression backend.
Ghostscript is developed and licensed by Artifex Software, Inc. Ghostscript is
not bundled with this project, and this project is not endorsed by Artifex.

Image compression uses Pillow.

See `CREDITS.md` for attribution and license notes.
