"""
Subtitle extraction module with support for text and bitmap-based subtitles.
"""

from .constants import SUPPORTED_FORMATS
from .exceptions import ExtractionError, FFmpegError, OCRError, UnsupportedCodecError
from .extractors import BaseExtractor, BitmapSubtitleExtractor, TextSubtitleExtractor
from .subprocess import SubprocessRunner


__all__ = [
    "BaseExtractor",
    "TextSubtitleExtractor",
    "BitmapSubtitleExtractor",
    "ExtractionError",
    "UnsupportedCodecError",
    "FFmpegError",
    "OCRError",
    "SUPPORTED_FORMATS",
]
