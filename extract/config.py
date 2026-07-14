"""
Configuration management for subtitle extraction.
"""

import logging
from dataclasses import dataclass

from extract.prober import StreamInfo

logger = logging.getLogger(__name__)


@dataclass
class ExtractorConfig:
    overwrite: bool = False

    # output format
    desired_formats: list[str] | tuple[str, str] = ("srt", "ass")

    # target languages
    languages: list[str] | tuple[str] = ("all",)
    unknown_language_as: str = "unknown"
    extract_sdh: bool = True

    def is_stream_wanted(self, stream: StreamInfo) -> bool:

        if self.extract_sdh == False and stream.is_sdh():
            logger.debug(f"Skipping unwanted SDH stream ({stream.index})")
            return False

        is_wanted_lang = "all" in self.languages or stream.language in self.languages

        if not is_wanted_lang:
            logger.debug(
                f"Skipping unwanted language '{stream.language}' for stream {stream.index}"
            )

        return is_wanted_lang
