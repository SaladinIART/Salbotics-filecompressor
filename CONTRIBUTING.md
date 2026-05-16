# Contributing

Thanks for helping improve Salbotics File Compressor.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Install Ghostscript separately if you want to run real compression smoke tests.
Set `SALBOTICS_FILECOMPRESSOR_GS` when Ghostscript is not on `PATH`.

## Before Opening a PR

- Keep generated files out of commits: `build`, `dist`, `release`, caches, and
  temporary PDFs.
- Add or update tests for behavior changes.
- Run `python -m unittest discover -s tests -v`.
- Update `README.md`, `CREDITS.md`, or `GEMINI.md` when behavior, licensing, or
  handoff context changes.

## Licensing

Project code is MIT licensed. Ghostscript is a separate dependency developed by
Artifex Software, Inc. Do not bundle Ghostscript binaries unless the licensing
decision has been reviewed.
