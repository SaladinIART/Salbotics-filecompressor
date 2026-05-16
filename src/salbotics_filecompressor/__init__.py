"""Public package exports for Salbotics File Compressor."""

from .compressor import CompressionOptions, CompressionResult, compress_batch, compress_file
from .engine_registry import EngineInfo, detect_engines, supported_input_extensions
from .errors import (
    CompressionFailedError,
    FileCompressorError,
    GhostscriptNotFoundError,
)

__all__ = [
    "CompressionFailedError",
    "CompressionOptions",
    "CompressionResult",
    "EngineInfo",
    "FileCompressorError",
    "GhostscriptNotFoundError",
    "compress_batch",
    "compress_file",
    "detect_engines",
    "supported_input_extensions",
]

__version__ = "0.2.0"
