"""
Text-based subtitle extractor using FFmpeg.
"""

import logging
import os

from ..constants import FFMPEG_TEXT_FORMATS
from ..exceptions import FFmpegError
from ..path import SubtitlePath
from ..prober import StreamInfo
from .base import BaseExtractor
from ..subprocess import SubprocessError

logger = logging.getLogger(__name__)


class TextSubtitleExtractor(BaseExtractor):
    """Extracts text-based subtitles using FFmpeg."""

    def extract(self, video_path: str) -> list[str]:
        """
        Extract text-based subtitles from video file.

        Args:
            video_path: Path to video file
            streams: List of subtitle streams

        Returns:
            List of paths to extracted subtitle files
        """
        logger.debug(f"Extracting text subtitles from {video_path}")

        streams = self.media_prober.get_subtitle_streams(
            video_path, self.config.unknown_language_as
        )

        # Filter streams by supported codecs
        text_streams = self.filter_streams_by_codec(streams, FFMPEG_TEXT_FORMATS)

        if not text_streams:
            logger.debug("No text-based subtitle streams found")
            return []

        path_manager = SubtitlePath(video_path)
        ffmpeg_args = []
        output_paths = []

        # Build FFmpeg arguments for all streams and formats
        for stream in text_streams:
            for fmt in self.config.desired_formats:
                output_path = path_manager.generate_subtitle_path(stream, fmt)

                if self.should_extract_stream(
                    video_path, stream, output_path, FFMPEG_TEXT_FORMATS
                ):
                    ffmpeg_args.extend(["-map", f"0:{stream.index}", output_path])
                    output_paths.append(output_path)

        if ffmpeg_args:
            try:
                self._run_ffmpeg_extraction(video_path, ffmpeg_args)
                logger.info(f"Extracted {len(output_paths)} text-based subtitle files")
            except:

                for p in output_path:
                    if os.path.exists(p) and os.path.getsize(p) == 0:
                        os.remove(p)

                raise

        else:
            logger.info("No text-based subtitles to extract")

        return output_paths

    def _run_ffmpeg_extraction(self, video_path: str, ffmpeg_args: list[str]):
        """Run FFmpeg to extract subtitles."""
        base_args = [
            "ffmpeg",
            "-v",
            "error",
            "-y",  # Overwrite output files
            "-i",
            video_path,
        ]

        full_args = base_args + ffmpeg_args

        try:
            result = self.subprocess_runner.run(full_args)
            logger.debug("FFmpeg extraction completed successfully")
        except SubprocessError as e:
            raise FFmpegError(f"Text subtitle extraction failed: {e}")
