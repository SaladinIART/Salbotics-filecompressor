"""Create and compress sample images through real image code paths."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from salbotics_filecompressor.compressor import (
    IMAGE_OUTPUT_PDF,
    IMAGE_OUTPUT_SAME_FORMAT,
    CompressionOptions,
    compress_file,
    find_magick,
)
from salbotics_filecompressor.errors import FileCompressorError


def create_sample_image(path: Path, image_format: str) -> None:
    image = Image.effect_noise((960, 640), 85).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 920, 600), outline="white", width=6)
    draw.rectangle((70, 70, 890, 150), fill="white")
    draw.text((96, 96), f"Salbotics image smoke {image_format}", fill="black")
    for index in range(8):
        x = 90 + index * 96
        draw.ellipse((x, 220, x + 56, 276), fill=(40 + index * 20, 120, 180))
    image.save(path, image_format)
    image.close()


def smoke_builtin_images(root: Path) -> bool:
    checks = [
        ("jpg", "JPEG", IMAGE_OUTPUT_SAME_FORMAT),
        ("png", "PNG", IMAGE_OUTPUT_SAME_FORMAT),
        ("jpg", "JPEG", IMAGE_OUTPUT_PDF),
    ]
    ok = True
    for suffix, image_format, image_output in checks:
        source = root / f"sample.{suffix}"
        output_suffix = ".pdf" if image_output == IMAGE_OUTPUT_PDF else f".{suffix}"
        output = root / f"sample_{image_output.replace('-', '_')}{output_suffix}"
        create_sample_image(source, image_format)
        try:
            result = compress_file(
                source,
                output,
                CompressionOptions(target_kb=120, image_output=image_output),
            )
        except FileCompressorError as exc:
            print(f"FAIL: {source.name} -> {output.name}: {exc}")
            ok = False
            continue

        print(
            f"OK: {source.name} -> {output.name} | "
            f"{result.status} | {result.original_size_bytes / 1024:.1f} KB -> "
            f"{result.final_size_bytes / 1024:.1f} KB | {result.mode}"
        )
        if not output.exists() or output.stat().st_size <= 0:
            print(f"FAIL: missing or empty output: {output}")
            ok = False

    return ok


def smoke_imagemagick(root: Path) -> bool:
    magick = find_magick()
    if magick is None:
        print("SKIP: ImageMagick not found; extended image smoke not run.")
        return True

    source = root / "sample.bmp"
    output = root / "sample_compressed.bmp"
    create_sample_image(source, "BMP")
    try:
        result = compress_file(
            source,
            output,
            CompressionOptions(target_kb=120, image_output=IMAGE_OUTPUT_SAME_FORMAT),
        )
    except FileCompressorError as exc:
        print(f"FAIL: ImageMagick smoke failed: {exc}")
        return False

    print(
        f"OK: ImageMagick {magick} | {source.name} -> {output.name} | "
        f"{result.status} | {result.original_size_bytes / 1024:.1f} KB -> "
        f"{result.final_size_bytes / 1024:.1f} KB | {result.mode}"
    )
    return output.exists() and output.stat().st_size > 0


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="salbotics-filecompressor-images-") as temp_dir:
        root = Path(temp_dir)
        ok = smoke_builtin_images(root)
        ok = smoke_imagemagick(root) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
