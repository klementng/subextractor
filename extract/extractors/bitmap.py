"""
Bitmap-based subtitle extractor with OCR support.
"""

import logging
import os
import shutil
import tempfile

from babelfish import Language
from pgsrip import Options, Sup, pgsrip

from ..constants import FFMPEG_BITMAP_FORMATS
from ..exceptions import FFmpegError, OCRError
from ..path import SubtitlePath
from ..prober import StreamInfo
from .base import BaseExtractor

logger = logging.getLogger(__name__)


class BitmapSubtitleExtractor(BaseExtractor):
    """Extracts bitmap-based subtitles with OCR conversion."""

    def extract(self, video_path: str) -> list[str]:
        """
        Extract bitmap-based subtitles from video file.

        Args:
            video_path: Path to video file
            streams: List of subtitle streams

        Returns:
            List of paths to extracted subtitle files
        """
        logger.debug(f"Extracting bitmap subtitles from {video_path}")

        streams = self.media_prober.get_subtitle_streams(
            video_path, self.config.unknown_language_as
        )

        bitmap_streams = self.filter_streams_by_codec(streams, FFMPEG_BITMAP_FORMATS)

        if not bitmap_streams:
            logger.info("No bitmap-based subtitle streams found")
            return []

        # Step 1: Extract to PGS format
        sup_files = self._extract_to_sup(video_path, bitmap_streams)

        # Step 2: OCR to SRT format
        srt_files = self._ocr_to_srt(video_path, bitmap_streams, sup_files)

        # Step 3: Convert to other formats if needed
        converted_files = self._convert_to_formats(
            video_path, bitmap_streams, srt_files
        )

        all_files = sup_files + srt_files + converted_files
        logger.info(f"Extracted {len(all_files)} bitmap-based subtitle files")

        return all_files

    def _extract_to_sup(self, video_path: str, streams: list[StreamInfo]) -> list[str]:
        """Extract bitmap subtitles to PGS (.sup) format."""
        path_manager = SubtitlePath(video_path)
        ffmpeg_args = []
        sup_files = []

        for stream in streams:
            sup_path = path_manager.generate_subtitle_path(stream, "sup")

            if self.should_extract_stream(
                video_path, stream, sup_path, FFMPEG_BITMAP_FORMATS
            ):
                ffmpeg_args.extend(
                    ["-map", f"0:{stream.index}", "-c", "copy", sup_path]
                )
                sup_files.append(sup_path)

        if ffmpeg_args:
            try:
                self._run_ffmpeg_extraction(video_path, ffmpeg_args)
                logger.debug(f"Extracted {len(sup_files)} PGS files")
            except:
                for p in sup_files:
                    if os.path.exists(p) and os.path.getsize(p) == 0:
                        os.remove(p)

                raise

        return sup_files

    def _ocr_to_srt(
        self, video_path: str, streams: list[StreamInfo], sup_files: list[str]
    ) -> list[str]:
        """Perform OCR on PGS files to create SRT files."""
        path_manager = SubtitlePath(video_path)
        srt_files = []

        for stream in streams:
            sup_path = path_manager.generate_subtitle_path(stream, "sup")
            srt_path = path_manager.generate_subtitle_path(stream, "srt")

            if (
                sup_path in sup_files or os.path.exists(sup_path)
            ) and self.should_extract_stream(video_path, stream, srt_path):

                try:
                    self._perform_ocr(sup_path, srt_path, stream.language)
                    srt_files.append(srt_path)
                    logger.debug(f"OCR completed for stream {stream.index}")
                except OCRError as e:
                    logger.error(f"OCR failed for stream {stream.index}: {e}")

        return srt_files

    def _convert_to_formats(
        self, video_path: str, streams: list[StreamInfo], srt_files: list[str]
    ) -> list[str]:
        """Convert SRT files to other requested formats."""

        if (
            "srt" in self.config.desired_formats
            and len(self.config.desired_formats) == 1
        ):
            return []  # Only SRT requested, no conversion needed

        path_manager = SubtitlePath(video_path)
        converted_files = []

        for stream in streams:
            srt_path = path_manager.generate_subtitle_path(stream, "srt")

            if srt_path not in srt_files and not os.path.exists(srt_path):
                continue

            for fmt in self.config.desired_formats:
                if fmt == "srt":
                    continue

                output_path = path_manager.generate_subtitle_path(stream, fmt)

                if self.should_extract_stream(video_path, stream, output_path):
                    ffmpeg_args = ["-i", srt_path, output_path]
                    self._run_ffmpeg_conversion(ffmpeg_args)
                    converted_files.append(output_path)

        return converted_files

    def _perform_ocr(self, sup_path: str, srt_path: str, language: str):
        """Perform OCR on a PGS subtitle file."""
        if language == "unknown":
            if self.config.unknown_language_as == "unknown":
                raise OCRError("Cannot perform OCR on unknown language")
            else:
                language = self.config.unknown_language_as

        # Create temporary directory (pgsrip doesn't handle spaces well)
        temp_dir = tempfile.mkdtemp()
        temp_sup = os.path.join(temp_dir, "temp.sup")
        temp_srt = os.path.join(temp_dir, "temp.srt")

        try:
            # Copy to temp location
            shutil.copy2(sup_path, temp_sup)

            # Perform OCR
            logger.debug(f"Performing OCR with language: {language}")
            pgsrip.rip(
                Sup(temp_sup),
                Options(
                    languages={Language(language)},
                    overwrite=True,
                    one_per_lang=False,
                ),
            )

            # Copy result back
            if os.path.exists(temp_srt):
                shutil.copy2(temp_srt, srt_path)
            else:
                raise OCRError("OCR did not produce output file")

        except ValueError as e:
            raise OCRError(f"Invalid language for OCR: {language}")
        except Exception as e:
            raise OCRError(f"OCR failed: {e}")
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _run_ffmpeg_extraction(self, video_path: str, ffmpeg_args: list[str]):
        """Run FFmpeg to extract bitmap subtitles."""
        base_args = ["ffmpeg", "-v", "error", "-y", "-i", video_path]

        full_args = base_args + ffmpeg_args

        try:
            self.subprocess_runner.run(full_args)
        except Exception as e:
            raise FFmpegError(f"Bitmap subtitle extraction failed: {e}")

    def _run_ffmpeg_conversion(self, ffmpeg_args: list[str]):
        """Run FFmpeg to convert subtitle formats."""
        base_args = ["ffmpeg", "-v", "error", "-y"]
        full_args = base_args + ffmpeg_args

        try:
            self.subprocess_runner.run(full_args)
        except Exception as e:
            raise FFmpegError(f"Subtitle conversion failed: {e}")
