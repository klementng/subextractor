"""
Media file information extraction and caching.
"""

import json
import logging
from typing import Any

import cachetools

from .exceptions import FFmpegError
from .subprocess import SubprocessRunner

logger = logging.getLogger(__name__)


class StreamInfo:
    """Represents information about a subtitle stream."""

    def __init__(self, stream_data: dict[str, Any]):
        self.data = stream_data
        self.index = stream_data.get("index")
        self.codec_name = stream_data.get("codec_name")
        self.codec_type = stream_data.get("codec_type")
        self.data.setdefault("tags", {})

    @property
    def language(self) -> str:
        """Get the language of the stream."""
        return self.data["tags"].get("language", "unknown")

    @language.setter
    def language(self, value: str):
        self.data["tags"]["language"] = value

    @property
    def title(self) -> str:
        return self.data["tags"].get("title", "")

    @property
    def disposition(self) -> dict[str, int]:
        return self.data.get("disposition", {})

    def is_forced(self) -> bool:
        return bool(self.disposition.get("forced", 0))

    def is_default(self) -> bool:
        return bool(self.disposition.get("default", 0))


class MediaProber:
    """Handles media file probing using FFprobe."""

    def __init__(self, cache_size: int = 128):
        self.subprocess_runner = SubprocessRunner(30)
        self._cache = cachetools.LFUCache(maxsize=cache_size)

    def get_subtitle_streams(
        self, video_path: str, unknown_language_as
    ) -> list[StreamInfo]:
        """
        Get subtitle stream information from a video file.

        Args:
            video_path: Path to the video file
            unknown_language_as: Default language for streams without language tags

        Returns:
            Dictionary mapping stream indices to StreamInfo objects

        Raises:
            FFmpegError: If ffprobe fails
        """
        cache_key = f"{video_path}:{unknown_language_as}"

        if cache_key in self._cache:
            logger.debug(f"Using cached probe data for {video_path}")
            return self._cache[cache_key]

        try:
            stream_data = self._probe_file(video_path)
            streams = []

            for data in stream_data:
                stream = StreamInfo(data)
                if not stream.language or stream.language == "und":
                    stream.language = unknown_language_as
                streams.append(stream)

            self._cache[cache_key] = streams
            logger.debug(f"Found {len(streams)} subtitle stream(s) in {video_path}")

            return streams

        except Exception as e:
            raise FFmpegError(f"Failed to probe video file '{video_path}': {e}")

    def _probe_file(self, video_path: str) -> list:
        """Run ffprobe on a video file."""
        args = [
            "ffprobe",
            "-of",
            "json",
            "-show_entries",
            "stream:stream_tags:format_tags",
            "-select_streams",
            "s",
            "-v",
            "error",
            str(video_path),
        ]

        logger.debug(f"Probing media file: {video_path}")

        try:
            result = self.subprocess_runner.run(args)
            probe_data = json.loads(result.stdout)
            return probe_data.get("streams", [])
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Invalid JSON from ffprobe: {e}")
