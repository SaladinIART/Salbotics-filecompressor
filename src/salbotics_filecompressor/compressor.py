"""Ghostscript-backed compression engine for Salbotics File Compressor."""

from __future__ import annotations

import os
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Literal, Sequence

from PIL import Image, ImageOps

from .errors import CompressionFailedError, FileCompressorError, GhostscriptNotFoundError


DEFAULT_TARGET_KB = 499
IMAGE_OUTPUT_SAME_FORMAT = "same-format"
IMAGE_OUTPUT_PDF = "pdf"
SUPPORTED_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})
SUPPORTED_INPUT_SUFFIXES = frozenset({".pdf", *SUPPORTED_IMAGE_SUFFIXES})
PRESERVE_TEXT_CANDIDATES: tuple[tuple[int, int], ...] = (
    (150, 75),
    (120, 65),
    (96, 55),
    (72, 45),
)
RASTER_CANDIDATES: tuple[tuple[int, int], ...] = (
    (110, 55),
    (96, 45),
    (84, 40),
    (72, 35),
    (60, 30),
    (50, 25),
)
IMAGE_CANDIDATES: tuple[tuple[float, int], ...] = (
    (1.0, 85),
    (0.9, 80),
    (0.8, 75),
    (0.7, 70),
    (0.6, 65),
    (0.5, 60),
    (0.4, 55),
)
RunCommand = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
ImageOutputMode = Literal["same-format", "pdf"]


@dataclass(frozen=True, slots=True)
class CompressionOptions:
    """User-selected compression options."""

    target_kb: int = DEFAULT_TARGET_KB
    grayscale: bool = False
    image_output: ImageOutputMode = IMAGE_OUTPUT_SAME_FORMAT

    def __post_init__(self) -> None:
        if self.image_output not in {IMAGE_OUTPUT_SAME_FORMAT, IMAGE_OUTPUT_PDF}:
            raise ValueError("image_output must be 'same-format' or 'pdf'")

    @property
    def target_bytes(self) -> int:
        """Return target size in bytes using binary kilobytes."""
        return self.target_kb * 1024


@dataclass(frozen=True, slots=True)
class CompressionResult:
    """Summary of one compression attempt."""

    input_path: Path
    output_path: Path
    original_size_bytes: int
    final_size_bytes: int
    target_size_bytes: int
    mode: str
    status: str
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class _CandidateResult:
    path: Path
    mode: str
    dpi: int
    quality: int
    size_bytes: int


def find_ghostscript() -> Path:
    """Locate Ghostscript executable."""
    configured = os.environ.get("SALBOTICS_FILECOMPRESSOR_GS") or os.environ.get("PDF499_GS")
    if configured:
        path = Path(configured)
        if path.exists():
            return path
        raise GhostscriptNotFoundError(
            f"configured Ghostscript path points to missing file: {path}"
        )

    for executable in ("gswin64c", "gswin32c", "gs"):
        found = shutil.which(executable)
        if found:
            return Path(found)

    for path in _standard_windows_ghostscript_paths():
        if path.exists():
            return path

    raise GhostscriptNotFoundError(
        "Ghostscript not found. Install Ghostscript and ensure gswin64c is on PATH, "
        "or set SALBOTICS_FILECOMPRESSOR_GS to the executable path."
    )


def _standard_windows_ghostscript_paths() -> list[Path]:
    roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    candidates: list[Path] = []
    for root in roots:
        if not root:
            continue
        gs_root = Path(root) / "gs"
        candidates.extend(gs_root.glob("gs*/bin/gswin64c.exe"))
        candidates.extend(gs_root.glob("gs*/bin/gswin32c.exe"))

    return sorted(set(candidates), reverse=True)


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, check=False, text=True)


def _ensure_pdf_input(input_path: Path) -> None:
    if not input_path.exists():
        raise CompressionFailedError(f"input PDF does not exist: {input_path}")
    if not input_path.is_file():
        raise CompressionFailedError(f"input path is not a file: {input_path}")
    if input_path.suffix.lower() != ".pdf":
        raise CompressionFailedError(f"input file must be a PDF: {input_path}")


def _ensure_supported_input(input_path: Path) -> None:
    if not input_path.exists():
        raise CompressionFailedError(f"input file does not exist: {input_path}")
    if not input_path.is_file():
        raise CompressionFailedError(f"input path is not a file: {input_path}")
    if input_path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise CompressionFailedError(f"unsupported file type: {input_path.suffix or '(none)'}")


def _is_supported_image(input_path: Path) -> bool:
    return input_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES


def _image_output_suffix(input_path: Path, options: CompressionOptions) -> str:
    if input_path.suffix.lower() == ".pdf" or options.image_output == IMAGE_OUTPUT_PDF:
        return ".pdf"
    return input_path.suffix.lower()


def _candidate_size(path: Path) -> int | None:
    if path.exists() and path.is_file() and path.stat().st_size > 0:
        return path.stat().st_size
    return None


def _invoke(command: Sequence[str], run_command: RunCommand) -> None:
    completed = run_command(command)
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        raise CompressionFailedError(details or "Ghostscript command failed")


def _preserve_text_command(
    gs_path: Path,
    input_path: Path,
    output_path: Path,
    dpi: int,
    quality: int,
    grayscale: bool,
) -> list[str]:
    command = [
        str(gs_path),
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dSAFER",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        f"-dColorImageResolution={dpi}",
        f"-dGrayImageResolution={dpi}",
        f"-dMonoImageResolution={max(dpi, 150)}",
        "-dAutoFilterColorImages=false",
        "-dAutoFilterGrayImages=false",
        "-dColorImageFilter=/DCTEncode",
        "-dGrayImageFilter=/DCTEncode",
        f"-dJPEGQ={quality}",
    ]
    if grayscale:
        command.extend(["-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray"])
    command.extend([f"-sOutputFile={output_path}", str(input_path)])
    return command


def _raster_command(
    gs_path: Path,
    input_path: Path,
    output_pattern: Path,
    dpi: int,
    quality: int,
    grayscale: bool,
) -> list[str]:
    device = "jpeggray" if grayscale else "jpeg"
    return [
        str(gs_path),
        f"-sDEVICE={device}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dSAFER",
        f"-r{dpi}",
        f"-dJPEGQ={quality}",
        f"-sOutputFile={output_pattern}",
        str(input_path),
    ]


def _build_pdf_from_images(
    image_paths: list[Path],
    output_path: Path,
    dpi: int,
    quality: int,
) -> None:
    if not image_paths:
        raise CompressionFailedError("Ghostscript produced no page images")

    opened: list[Image.Image] = []
    try:
        for image_path in image_paths:
            image = Image.open(image_path)
            opened.append(image.convert("RGB"))

        first, rest = opened[0], opened[1:]
        first.save(
            output_path,
            "PDF",
            resolution=float(dpi),
            quality=quality,
            optimize=True,
            save_all=True,
            append_images=rest,
        )
    finally:
        for image in opened:
            image.close()


def _resize_image(image: Image.Image, scale: float) -> Image.Image:
    if scale >= 1:
        return image.copy()

    width = max(1, math.floor(image.width * scale))
    height = max(1, math.floor(image.height * scale))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "WHITE")
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return image.convert("RGB")


def _save_jpeg_candidate(
    image: Image.Image,
    output_path: Path,
    scale: float,
    quality: int,
    grayscale: bool,
) -> None:
    candidate = _resize_image(ImageOps.exif_transpose(image), scale)
    try:
        output_image = candidate.convert("L") if grayscale else _flatten_to_rgb(candidate)
        try:
            output_image.save(
                output_path,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
        finally:
            if output_image is not candidate:
                output_image.close()
    finally:
        candidate.close()


def _save_png_candidate(
    image: Image.Image,
    output_path: Path,
    scale: float,
    quality: int,
    grayscale: bool,
) -> None:
    candidate = _resize_image(ImageOps.exif_transpose(image), scale)
    try:
        if grayscale:
            output_image = candidate.convert("L")
        elif candidate.mode in {"RGB", "L", "P"}:
            colors = max(16, min(256, quality * 3))
            output_image = candidate.convert("RGB").quantize(colors=colors)
        else:
            output_image = candidate.convert("RGBA")

        try:
            output_image.save(output_path, "PNG", optimize=True)
        finally:
            if output_image is not candidate:
                output_image.close()
    finally:
        candidate.close()


def _save_image_pdf_candidate(
    image: Image.Image,
    output_path: Path,
    scale: float,
    quality: int,
    grayscale: bool,
) -> None:
    candidate = _resize_image(ImageOps.exif_transpose(image), scale)
    try:
        output_image = candidate.convert("L") if grayscale else _flatten_to_rgb(candidate)
        try:
            output_image.save(
                output_path,
                "PDF",
                resolution=100.0,
                quality=quality,
                optimize=True,
            )
        finally:
            if output_image is not candidate:
                output_image.close()
    finally:
        candidate.close()


def _try_image_candidates(
    input_path: Path,
    work_dir: Path,
    options: CompressionOptions,
) -> list[_CandidateResult]:
    results: list[_CandidateResult] = []
    source_suffix = input_path.suffix.lower()
    output_suffix = _image_output_suffix(input_path, options)

    try:
        with Image.open(input_path) as image:
            image.load()
            for scale, quality in IMAGE_CANDIDATES:
                scale_label = int(scale * 100)
                candidate = work_dir / f"image-{scale_label}-{quality}{output_suffix}"
                try:
                    if options.image_output == IMAGE_OUTPUT_PDF:
                        _save_image_pdf_candidate(
                            image, candidate, scale, quality, options.grayscale
                        )
                    elif source_suffix in {".jpg", ".jpeg"}:
                        _save_jpeg_candidate(
                            image, candidate, scale, quality, options.grayscale
                        )
                    else:
                        _save_png_candidate(
                            image, candidate, scale, quality, options.grayscale
                        )
                except OSError:
                    continue

                size = _candidate_size(candidate)
                if size is not None:
                    mode = "image-pdf" if options.image_output == IMAGE_OUTPUT_PDF else "image"
                    results.append(
                        _CandidateResult(
                            path=candidate,
                            mode=mode,
                            dpi=scale_label,
                            quality=quality,
                            size_bytes=size,
                        )
                    )
    except OSError as exc:
        raise CompressionFailedError(f"could not read image: {exc}") from exc

    return results


def _try_preserve_text(
    gs_path: Path,
    input_path: Path,
    work_dir: Path,
    options: CompressionOptions,
    run_command: RunCommand,
) -> list[_CandidateResult]:
    results: list[_CandidateResult] = []
    for dpi, quality in PRESERVE_TEXT_CANDIDATES:
        candidate = work_dir / f"preserve-{dpi}-{quality}.pdf"
        try:
            _invoke(
                _preserve_text_command(
                    gs_path, input_path, candidate, dpi, quality, options.grayscale
                ),
                run_command,
            )
        except CompressionFailedError:
            continue

        size = _candidate_size(candidate)
        if size is not None:
            results.append(
                _CandidateResult(
                    path=candidate,
                    mode="preserve-text",
                    dpi=dpi,
                    quality=quality,
                    size_bytes=size,
                )
            )
    return results


def _try_raster(
    gs_path: Path,
    input_path: Path,
    work_dir: Path,
    options: CompressionOptions,
    run_command: RunCommand,
) -> list[_CandidateResult]:
    results: list[_CandidateResult] = []
    for dpi, quality in RASTER_CANDIDATES:
        candidate_dir = work_dir / f"raster-{dpi}-{quality}"
        candidate_dir.mkdir()
        output_pattern = candidate_dir / "page-%04d.jpg"
        candidate_pdf = work_dir / f"raster-{dpi}-{quality}.pdf"

        try:
            _invoke(
                _raster_command(
                    gs_path, input_path, output_pattern, dpi, quality, options.grayscale
                ),
                run_command,
            )
            image_paths = sorted(candidate_dir.glob("page-*.jpg"))
            _build_pdf_from_images(image_paths, candidate_pdf, dpi, quality)
        except CompressionFailedError:
            continue

        size = _candidate_size(candidate_pdf)
        if size is not None:
            results.append(
                _CandidateResult(
                    path=candidate_pdf,
                    mode="raster",
                    dpi=dpi,
                    quality=quality,
                    size_bytes=size,
                )
            )
    return results


def _choose_candidate(
    candidates: list[_CandidateResult],
    target_bytes: int,
) -> tuple[_CandidateResult, str, str | None]:
    if not candidates:
        raise CompressionFailedError("no usable compressed file could be produced")

    for candidate in candidates:
        if candidate.size_bytes <= target_bytes:
            return candidate, "success", None

    smallest = min(candidates, key=lambda candidate: candidate.size_bytes)
    warning = (
        f"target not reached; saved best readable candidate at "
        f"{smallest.size_bytes} bytes"
    )
    return smallest, "warning", warning


def _default_output_path(input_path: Path, output_dir: Path, options: CompressionOptions) -> Path:
    suffix = _image_output_suffix(input_path, options)
    base = output_dir / f"{input_path.stem}_compressed{suffix}"
    if not base.exists():
        return base

    counter = 2
    while True:
        candidate = output_dir / f"{input_path.stem}_compressed_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _skipped_result(
    input_path: Path,
    output_dir: Path,
    options: CompressionOptions,
    warning: str,
) -> CompressionResult:
    original_size = input_path.stat().st_size if input_path.exists() and input_path.is_file() else 0
    return CompressionResult(
        input_path=input_path,
        output_path=output_dir / input_path.name,
        original_size_bytes=original_size,
        final_size_bytes=0,
        target_size_bytes=options.target_bytes,
        mode="skipped",
        status="skipped",
        warning=warning,
    )


def _compress_pdf_file(
    source: Path,
    destination: Path,
    selected_options: CompressionOptions,
    run_command: RunCommand | None,
    gs_path: str | Path | None,
) -> CompressionResult:
    runner = run_command or _run_command
    ghostscript = Path(gs_path) if gs_path is not None else find_ghostscript()

    _ensure_pdf_input(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    original_size = source.stat().st_size
    if original_size <= selected_options.target_bytes:
        shutil.copy2(source, destination)
        return CompressionResult(
            input_path=source,
            output_path=destination,
            original_size_bytes=original_size,
            final_size_bytes=destination.stat().st_size,
            target_size_bytes=selected_options.target_bytes,
            mode="copy",
            status="already-under-target",
        )

    with tempfile.TemporaryDirectory(prefix="salbotics-filecompressor-") as temp_dir:
        work_dir = Path(temp_dir)
        candidates = _try_preserve_text(
            ghostscript, source, work_dir, selected_options, runner
        )

        if not any(candidate.size_bytes <= selected_options.target_bytes for candidate in candidates):
            candidates.extend(
                _try_raster(ghostscript, source, work_dir, selected_options, runner)
            )

        selected, status, warning = _choose_candidate(candidates, selected_options.target_bytes)
        shutil.copy2(selected.path, destination)

    return CompressionResult(
        input_path=source,
        output_path=destination,
        original_size_bytes=original_size,
        final_size_bytes=destination.stat().st_size,
        target_size_bytes=selected_options.target_bytes,
        mode=f"{selected.mode}:{selected.dpi}dpi:q{selected.quality}",
        status=status,
        warning=warning,
    )


def _compress_image_file(
    source: Path,
    destination: Path,
    selected_options: CompressionOptions,
) -> CompressionResult:
    _ensure_supported_input(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    original_size = source.stat().st_size
    if (
        selected_options.image_output == IMAGE_OUTPUT_SAME_FORMAT
        and original_size <= selected_options.target_bytes
    ):
        shutil.copy2(source, destination)
        return CompressionResult(
            input_path=source,
            output_path=destination,
            original_size_bytes=original_size,
            final_size_bytes=destination.stat().st_size,
            target_size_bytes=selected_options.target_bytes,
            mode="copy",
            status="already-under-target",
        )

    with tempfile.TemporaryDirectory(prefix="salbotics-filecompressor-image-") as temp_dir:
        work_dir = Path(temp_dir)
        candidates = _try_image_candidates(source, work_dir, selected_options)
        selected, status, warning = _choose_candidate(candidates, selected_options.target_bytes)
        shutil.copy2(selected.path, destination)

    mode = f"{selected.mode}:{selected.dpi}%:q{selected.quality}"
    return CompressionResult(
        input_path=source,
        output_path=destination,
        original_size_bytes=original_size,
        final_size_bytes=destination.stat().st_size,
        target_size_bytes=selected_options.target_bytes,
        mode=mode,
        status=status,
        warning=warning,
    )

def compress_file(
    input_path: str | Path,
    output_path: str | Path,
    options: CompressionOptions | None = None,
    *,
    run_command: RunCommand | None = None,
    gs_path: str | Path | None = None,
) -> CompressionResult:
    """Compress one supported file toward the requested target size."""
    source = Path(input_path)
    destination = Path(output_path)
    selected_options = options or CompressionOptions()

    if source.suffix.lower() == ".pdf":
        return _compress_pdf_file(
            source,
            destination,
            selected_options,
            run_command,
            gs_path,
        )

    if _is_supported_image(source):
        return _compress_image_file(source, destination, selected_options)

    _ensure_supported_input(source)
    raise CompressionFailedError(f"unsupported file type: {source.suffix or '(none)'}")


def compress_batch(
    input_paths: Iterable[str | Path],
    output_dir: str | Path,
    options: CompressionOptions | None = None,
    *,
    run_command: RunCommand | None = None,
    gs_path: str | Path | None = None,
) -> list[CompressionResult]:
    """Compress many supported files into one output directory."""
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    selected_options = options or CompressionOptions()

    results: list[CompressionResult] = []
    for input_path in input_paths:
        source = Path(input_path)
        if source.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
            results.append(
                _skipped_result(
                    source,
                    destination_dir,
                    selected_options,
                    f"unsupported file type: {source.suffix or '(none)'}",
                )
            )
            continue

        destination = _default_output_path(source, destination_dir, selected_options)
        try:
            results.append(
                compress_file(
                    source,
                    destination,
                    selected_options,
                    run_command=run_command,
                    gs_path=gs_path,
                )
            )
        except FileCompressorError as exc:
            original_size = source.stat().st_size if source.exists() and source.is_file() else 0
            results.append(
                CompressionResult(
                    input_path=source,
                    output_path=destination,
                    original_size_bytes=original_size,
                    final_size_bytes=0,
                    target_size_bytes=selected_options.target_bytes,
                    mode="failed",
                    status="failed",
                    warning=str(exc),
                )
            )
    return results
