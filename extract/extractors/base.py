"""
Base extractor interface
"""

import logging
from abc import ABC, abstractmethod

from extract.subprocess import SubprocessRunner

from ..config import ExtractorConfig
from ..path import SubtitlePath
from ..prober import MediaProber, StreamInfo

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for subtitle extractors."""

    def __init__(self, config: ExtractorConfig, media_probe: MediaProber):
        self.config = config
        self.subprocess_runner = SubprocessRunner()
        self.media_prober = media_probe

    @abstractmethod
    def extract(self, video_path: str, streams: list[StreamInfo]) -> list[str]:
        """
        Extract subtitles from video file.

        Args:
            video_path: Path to video file
            streams: List of streams to extract

        Returns:
            List of paths to extracted subtitle files
        """
        pass

    def should_extract_stream(
        self,
        video_path: str,
        stream: StreamInfo,
        output_path: str,
        supported_codecs: list[str] = [],
    ) -> bool:
        """
        Determine if a stream should be extracted.

        Args:
            video_path: Path to video file
            stream: Stream information
            output_path: Target output path
            supported_codecs: List of supported codecs (None = all supported)

        Returns:
            True if stream should be extracted
        """
        path = SubtitlePath(video_path)

        if path.file_exists_and_valid(output_path):
            if not self.config.overwrite:
                logger.debug(f"Skipping existing file: {output_path}")
                return False
            logger.debug(f"Overwriting existing file: {output_path}")

        if not self.config.is_language_wanted(stream.language):
            logger.debug(
                f"Skipping unwanted language '{stream.language}' for stream {stream.index}"
            )
            return False

        # Check codec support
        if supported_codecs and stream.codec_name not in supported_codecs:
            logger.warning(
                f"Skipping unsupported codec '{stream.codec_name}' for stream {stream.index}"
            )
            return False

        logger.debug(
            f"Will extract stream {stream.index} ({stream.language}, {stream.codec_name})"
        )
        return True

    def filter_streams_by_codec(
        self, streams: list[StreamInfo], supported_codecs: list[str]
    ) -> list[StreamInfo]:
        """Filter streams by supported codecs."""
        filtered = []
        for stream in streams:
            if stream.codec_name in supported_codecs:
                filtered.append(stream)
            else:
                logger.debug(
                    f"Filtered out stream {stream.index} with unsupported codec: {stream.codec_name}"
                )

        return filtered
