"""Command-line interface for Salbotics File Compressor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compressor import (
    DEFAULT_TARGET_KB,
    IMAGE_OUTPUT_PDF,
    IMAGE_OUTPUT_SAME_FORMAT,
    QUALITY_AGGRESSIVE,
    QUALITY_SAFE,
    QUALITY_SMART,
    CompressionOptions,
    CompressionResult,
    compress_batch,
    compress_file,
)
from .errors import FileCompressorError
from .engine_registry import format_engine_table, format_supported_formats


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="salbotics-filecompressor",
        description="Compress PDF and image files toward a target size.",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="PDF, JPG, JPEG, or PNG file to compress for single-file mode.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path for single-file mode.",
    )
    parser.add_argument(
        "--batch-folder",
        type=Path,
        help="Folder containing files to compress.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output folder for batch mode.",
    )
    parser.add_argument(
        "--target-kb",
        type=int,
        default=DEFAULT_TARGET_KB,
        help=f"Target size in KB. Default: {DEFAULT_TARGET_KB}.",
    )
    parser.add_argument(
        "--grayscale",
        action="store_true",
        help="Allow grayscale conversion in later compression passes.",
    )
    parser.add_argument(
        "--image-output",
        choices=[IMAGE_OUTPUT_SAME_FORMAT, IMAGE_OUTPUT_PDF],
        default=IMAGE_OUTPUT_SAME_FORMAT,
        help=(
            "Output format for image inputs. "
            f"Default: {IMAGE_OUTPUT_SAME_FORMAT}."
        ),
    )
    parser.add_argument(
        "--force-optimize",
        action="store_true",
        help="Optimize even when the file is already under the target size.",
    )
    parser.add_argument(
        "--quality-mode",
        choices=[QUALITY_SAFE, QUALITY_SMART, QUALITY_AGGRESSIVE],
        default=QUALITY_SMART,
        help=f"Compression strategy. Default: {QUALITY_SMART}.",
    )
    parser.add_argument(
        "--list-engines",
        action="store_true",
        help="List detected compression/conversion engines and exit.",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List currently supported input formats and exit.",
    )
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.target_kb <= 0:
        parser.error("--target-kb must be greater than 0")

    using_batch = args.batch_folder is not None
    using_single = args.input_file is not None

    if using_batch and using_single:
        parser.error("choose either single-file mode or --batch-folder, not both")

    if using_batch:
        if args.output_dir is None:
            parser.error("--output-dir is required with --batch-folder")
        if args.output is not None:
            parser.error("--output is only valid in single-file mode")
        return

    if using_single:
        if args.output is None:
            parser.error("--output is required in single-file mode")
        if args.output_dir is not None:
            parser.error("--output-dir is only valid with --batch-folder")
        return

    parser.error("provide input_file or --batch-folder")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_engines:
        print(format_engine_table())
        return 0

    if args.list_formats:
        print(format_supported_formats())
        return 0

    _validate_args(parser, args)

    options = CompressionOptions(
        target_kb=args.target_kb,
        grayscale=args.grayscale,
        image_output=args.image_output,
        force_optimize=args.force_optimize,
        quality_mode=args.quality_mode,
    )

    try:
        if args.batch_folder is not None:
            input_paths = sorted(path for path in args.batch_folder.iterdir() if path.is_file())
            results = compress_batch(input_paths, args.output_dir, options)
            for result in results:
                print(_format_result(result))
        else:
            result = compress_file(args.input_file, args.output, options)
            print(_format_result(result))
    except FileCompressorError as exc:
        print(f"salbotics-filecompressor error: {exc}", file=sys.stderr)
        return 1

    return 0


def _format_result(result: CompressionResult) -> str:
    final_kb = result.final_size_bytes / 1024
    original_kb = result.original_size_bytes / 1024
    target_kb = result.target_size_bytes / 1024
    warning = result.warning
    suffix = f" WARNING: {warning}" if warning else ""
    return (
        f"{result.output_path} | {result.status} | "
        f"{original_kb:.1f} KB -> {final_kb:.1f} KB "
        f"(target {target_kb:.1f} KB, mode {result.mode}){suffix}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
