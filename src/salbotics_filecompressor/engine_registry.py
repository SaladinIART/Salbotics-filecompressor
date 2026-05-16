"""Engine discovery for Salbotics File Compressor."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from PIL import __version__ as PILLOW_VERSION

from .compressor import find_ghostscript, find_magick, find_mutool, find_qpdf


ENGINE_CAPABILITIES: Mapping[str, tuple[str, ...]] = {
    "pillow": ("image_compress", "image_to_pdf"),
    "ghostscript": ("pdf_compress", "pdf_raster_fallback"),
    "qpdf": ("pdf_cleanup", "pdf_stream_compress"),
    "mutool": ("pdf_cleanup", "pdf_image_stream_compress"),
    "imagemagick": ("image_compress", "image_convert", "image_to_pdf"),
    "libvips": ("image_compress", "image_convert"),
    "libreoffice": ("office_to_pdf",),
}
BUILTIN_IMAGE_INPUTS = (".jpg", ".jpeg", ".png")
EXTENDED_IMAGE_INPUTS = (".bmp", ".tif", ".tiff", ".webp")
OFFICE_INPUTS = (".doc", ".docx", ".odp", ".ods", ".odt", ".ppt", ".pptx", ".xls", ".xlsx")
PDF_INPUTS = (".pdf",)
SAME_IMAGE_OUTPUTS = (
    ".bmp",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
)


@dataclass(frozen=True, slots=True)
class EngineInfo:
    """Detected conversion or compression engine."""

    name: str
    display_name: str
    available: bool
    capabilities: tuple[str, ...]
    input_extensions: tuple[str, ...]
    output_extensions: tuple[str, ...]
    path: Path | None = None
    version: str | None = None
    note: str | None = None


Which = Callable[[str], str | None]


def detect_engines(*, which: Which | None = None) -> list[EngineInfo]:
    """Return known engines and whether they are available locally."""
    finder = which or shutil.which
    return [
        _pillow_engine(),
        _ghostscript_engine(),
        _optional_path_engine(
            name="qpdf",
            display_name="qpdf",
            path_finder=(
                find_qpdf
                if which is None
                else lambda: _find_executable(("qpdf",), finder)
            ),
            version_args=("--version",),
            input_extensions=PDF_INPUTS,
            output_extensions=PDF_INPUTS,
            unavailable_note="Install qpdf for safe PDF stream/object cleanup.",
        ),
        _optional_path_engine(
            name="mutool",
            display_name="MuPDF mutool",
            path_finder=(
                find_mutool
                if which is None
                else lambda: _find_executable(("mutool",), finder)
            ),
            version_args=("-v",),
            input_extensions=PDF_INPUTS,
            output_extensions=PDF_INPUTS,
            unavailable_note="Install MuPDF tools for optional PDF cleanup passes.",
        ),
        _optional_path_engine(
            name="imagemagick",
            display_name="ImageMagick",
            path_finder=(
                find_magick
                if which is None
                else lambda: _find_executable(("magick",), finder)
            ),
            version_args=("-version",),
            input_extensions=(*BUILTIN_IMAGE_INPUTS, *EXTENDED_IMAGE_INPUTS),
            output_extensions=(*SAME_IMAGE_OUTPUTS, ".pdf"),
            unavailable_note="Install ImageMagick to unlock broader image formats.",
        ),
        _command_engine(
            name="libvips",
            display_name="libvips",
            executable_names=("vips",),
            which=finder,
            version_args=("--version",),
            input_extensions=(*BUILTIN_IMAGE_INPUTS, *EXTENDED_IMAGE_INPUTS, ".svg"),
            output_extensions=SAME_IMAGE_OUTPUTS,
            unavailable_note="Install libvips for fast, low-memory image processing.",
        ),
        _libreoffice_engine(finder),
    ]


def available_engines(engines: Iterable[EngineInfo] | None = None) -> list[EngineInfo]:
    """Return locally available engines."""
    detected = list(engines) if engines is not None else detect_engines()
    return [engine for engine in detected if engine.available]


def supported_input_extensions(engines: Iterable[EngineInfo] | None = None) -> tuple[str, ...]:
    """Return sorted input extensions supported by available engines."""
    supported: set[str] = set()
    for engine in available_engines(engines):
        supported.update(engine.input_extensions)
    return tuple(sorted(supported))


def supported_format_rows(engines: Iterable[EngineInfo] | None = None) -> list[tuple[str, str]]:
    """Return supported input extensions with available engine names."""
    detected = list(engines) if engines is not None else detect_engines()
    rows: list[tuple[str, str]] = []
    for extension in supported_input_extensions(detected):
        engine_names = [
            engine.name
            for engine in detected
            if engine.available and extension in engine.input_extensions
        ]
        rows.append((extension, ", ".join(engine_names)))
    return rows


def format_engine_table(engines: Iterable[EngineInfo] | None = None) -> str:
    """Format engine discovery as CLI text."""
    detected = list(engines) if engines is not None else detect_engines()
    lines = ["Engine        Status       Capabilities"]
    for engine in detected:
        status = "available" if engine.available else "missing"
        capabilities = ", ".join(engine.capabilities)
        details = f"{engine.name:<13} {status:<12} {capabilities}"
        if engine.version:
            details += f" | {engine.version}"
        elif engine.note:
            details += f" | {engine.note}"
        lines.append(details)
    return "\n".join(lines)


def format_supported_formats(engines: Iterable[EngineInfo] | None = None) -> str:
    """Format supported input extensions as CLI text."""
    rows = supported_format_rows(engines)
    if not rows:
        return "No supported formats detected."

    lines = ["Extension   Available engines"]
    for extension, engine_names in rows:
        lines.append(f"{extension:<11} {engine_names}")
    return "\n".join(lines)


def _pillow_engine() -> EngineInfo:
    return EngineInfo(
        name="pillow",
        display_name="Pillow",
        available=True,
        capabilities=ENGINE_CAPABILITIES["pillow"],
        input_extensions=BUILTIN_IMAGE_INPUTS,
        output_extensions=(*BUILTIN_IMAGE_INPUTS, ".pdf"),
        version=f"Pillow {PILLOW_VERSION}",
    )


def _ghostscript_engine() -> EngineInfo:
    try:
        path = find_ghostscript()
    except Exception as exc:
        return EngineInfo(
            name="ghostscript",
            display_name="Ghostscript",
            available=False,
            capabilities=ENGINE_CAPABILITIES["ghostscript"],
            input_extensions=PDF_INPUTS,
            output_extensions=PDF_INPUTS,
            note=str(exc),
        )

    return EngineInfo(
        name="ghostscript",
        display_name="Ghostscript",
        available=True,
        capabilities=ENGINE_CAPABILITIES["ghostscript"],
        input_extensions=PDF_INPUTS,
        output_extensions=PDF_INPUTS,
        path=path,
        version=_read_version(path, ("--version",)),
    )


def _command_engine(
    *,
    name: str,
    display_name: str,
    executable_names: Sequence[str],
    which: Which,
    version_args: Sequence[str],
    input_extensions: Sequence[str],
    output_extensions: Sequence[str],
    unavailable_note: str,
) -> EngineInfo:
    path = _find_executable(executable_names, which)
    if path is None:
        return EngineInfo(
            name=name,
            display_name=display_name,
            available=False,
            capabilities=ENGINE_CAPABILITIES[name],
            input_extensions=tuple(input_extensions),
            output_extensions=tuple(output_extensions),
            note=unavailable_note,
        )

    return EngineInfo(
        name=name,
        display_name=display_name,
        available=True,
        capabilities=ENGINE_CAPABILITIES[name],
        input_extensions=tuple(input_extensions),
        output_extensions=tuple(output_extensions),
        path=path,
        version=_read_version(path, version_args),
    )


def _optional_path_engine(
    *,
    name: str,
    display_name: str,
    path_finder: Callable[[], Path | None],
    version_args: Sequence[str],
    input_extensions: Sequence[str],
    output_extensions: Sequence[str],
    unavailable_note: str,
) -> EngineInfo:
    path = path_finder()
    if path is None:
        return EngineInfo(
            name=name,
            display_name=display_name,
            available=False,
            capabilities=ENGINE_CAPABILITIES[name],
            input_extensions=tuple(input_extensions),
            output_extensions=tuple(output_extensions),
            note=unavailable_note,
        )

    return EngineInfo(
        name=name,
        display_name=display_name,
        available=True,
        capabilities=ENGINE_CAPABILITIES[name],
        input_extensions=tuple(input_extensions),
        output_extensions=tuple(output_extensions),
        path=path,
        version=_read_version(path, version_args),
    )


def _libreoffice_engine(which: Which) -> EngineInfo:
    path = _find_executable(("soffice", "libreoffice"), which) or _find_standard_libreoffice()
    if path is None:
        return EngineInfo(
            name="libreoffice",
            display_name="LibreOffice",
            available=False,
            capabilities=ENGINE_CAPABILITIES["libreoffice"],
            input_extensions=OFFICE_INPUTS,
            output_extensions=PDF_INPUTS,
            note="Install LibreOffice to convert Office documents to PDF.",
        )

    return EngineInfo(
        name="libreoffice",
        display_name="LibreOffice",
        available=True,
        capabilities=ENGINE_CAPABILITIES["libreoffice"],
        input_extensions=OFFICE_INPUTS,
        output_extensions=PDF_INPUTS,
        path=path,
        version=_read_version(path, ("--version",)),
    )


def _find_executable(executable_names: Sequence[str], which: Which) -> Path | None:
    for executable_name in executable_names:
        found = which(executable_name)
        if found:
            return Path(found)
    return None


def _find_standard_libreoffice() -> Path | None:
    roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    for root in roots:
        if not root:
            continue
        path = Path(root) / "LibreOffice" / "program" / "soffice.exe"
        if path.exists():
            return path
    return None


def _read_version(path: Path, args: Sequence[str]) -> str | None:
    try:
        completed = subprocess.run(
            [str(path), *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    output = (completed.stdout or completed.stderr or "").strip()
    return output.splitlines()[0] if output else None
