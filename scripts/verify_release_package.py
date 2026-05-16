"""Verify the local Windows release ZIP contains expected files."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ZIP = PROJECT_ROOT / "release" / "salbotics-filecompressor-windows.zip"
REQUIRED_NAMES = {
    "salbotics-filecompressor.exe",
    "salbotics-filecompressor-cli.exe",
    "README.md",
    "CREDITS.md",
    "salbotics-filecompressor.ico",
}


def main() -> int:
    if not RELEASE_ZIP.exists():
        print(f"FAIL: release ZIP not found: {RELEASE_ZIP}")
        return 1

    with ZipFile(RELEASE_ZIP) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}

    missing = sorted(REQUIRED_NAMES - names)
    if missing:
        print(f"FAIL: missing release files: {', '.join(missing)}")
        return 1

    print(f"OK: {RELEASE_ZIP}")
    for name in sorted(REQUIRED_NAMES):
        print(f" - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
