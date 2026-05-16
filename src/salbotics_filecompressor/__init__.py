"""Public package exports for Salbotics File Compressor."""

from .compressor import CompressionOptions, CompressionResult, compress_batch, compress_file
from .errors import (
    CompressionFailedError,
    FileCompressorError,
    GhostscriptNotFoundError,
)

__all__ = [
    "CompressionFailedError",
    "CompressionOptions",
    "CompressionResult",
    "FileCompressorError",
    "GhostscriptNotFoundError",
    "compress_batch",
    "compress_file",
]

__version__ = "0.1.0"
