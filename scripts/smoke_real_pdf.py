"""Create and compress a sample PDF with real Ghostscript when available."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from salbotics_filecompressor.compressor import CompressionOptions, compress_file, find_ghostscript
from salbotics_filecompressor.errors import FileCompressorError, GhostscriptNotFoundError


def create_sample_pdf(path: Path) -> None:
    pages: list[Image.Image] = []
    for page_number in range(1, 5):
        image = Image.effect_noise((1654, 2339), 90).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 80, 1574, 2259), outline="white", width=8)
        draw.rectangle((100, 100, 1554, 240), fill="white")
        draw.text((140, 140), f"Salbotics smoke page {page_number}", fill="black")
        for row in range(12):
            y = 260 + row * 130
            draw.line((140, y, 1514, y), fill=(255, 255, 255), width=3)
        pages.append(image)

    first, rest = pages[0], pages[1:]
    first.save(path, "PDF", resolution=200.0, save_all=True, append_images=rest)
    for page in pages:
        page.close()


def main() -> int:
    try:
        gs_path = find_ghostscript()
    except GhostscriptNotFoundError as exc:
        print(f"SKIP: {exc}")
        return 0

    with tempfile.TemporaryDirectory(prefix="salbotics-filecompressor-smoke-") as temp_dir:
        root = Path(temp_dir)
        source = root / "sample.pdf"
        output = root / "sample_compressed.pdf"
        create_sample_pdf(source)

        try:
            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=499, grayscale=True),
                gs_path=gs_path,
            )
        except FileCompressorError as exc:
            print(f"FAIL: {exc}")
            return 1

        print(f"Ghostscript: {gs_path}")
        print(f"Source: {result.original_size_bytes / 1024:.1f} KB")
        print(f"Output: {result.final_size_bytes / 1024:.1f} KB")
        print(f"Status: {result.status}")
        print(f"Mode: {result.mode}")
        if result.warning:
            print(f"Warning: {result.warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
