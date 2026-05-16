"""Error types for Salbotics File Compressor."""


class FileCompressorError(Exception):
    """Base exception for Salbotics File Compressor failures."""


class GhostscriptNotFoundError(FileCompressorError):
    """Raised when Ghostscript is not available."""


class CompressionFailedError(FileCompressorError):
    """Raised when no usable PDF can be produced."""
