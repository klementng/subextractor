"""
Custom exceptions for subtitle extraction.
"""


class ExtractionError(Exception):
    """Base exception for subtitle extraction errors."""


class UnsupportedCodecError(ExtractionError):
    """Raised when subtitle codec is not supported."""


class FFmpegError(ExtractionError):
    """Raised when FFmpeg operations fail."""


class OCRError(ExtractionError):
    """Raised when OCR operations fail."""
