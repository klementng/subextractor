import os
import re
from pathlib import Path

from .prober import StreamInfo


class SubtitlePath:
    ILLEGAL_CHARS_PATTERN = re.compile(r"""NUL|[\/:*"<>|.%$^&£?]""")

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _generate_filename(self, stream: StreamInfo, extension: str) -> str:
        """Generate filename for subtitle file."""

        title = stream.title
        if title:
            title = f"{stream.index} - {title}"
        else:
            title = str(stream.index)

        title = self._clean_filename_component(title)

        base_name = self.base_path.stem
        language = stream.language

        return f"{base_name}.{title}.{language}.{extension}"

    def _clean_filename_component(self, component: str) -> str:
        """Clean a filename component of illegal characters."""
        cleaned = self.ILLEGAL_CHARS_PATTERN.sub(" - ", component)
        return cleaned.replace("  ", " ").strip()

    def generate_subtitle_path(self, stream: StreamInfo, extension: str) -> str:
        """
        Generate output path for a subtitle file.

        Args:
            stream: StreamInfo object
            extension: File extension (without dot)

        Returns:
            Full path to the subtitle file
        """
        filename = self._generate_filename(stream, extension)
        return str(self.base_path.parent / filename)

    def file_exists_and_valid(self, path: str) -> bool:
        """
        Check if subtitle file exists and is valid (non-empty).

        Args:
            path: Path to check

        Returns:
            True if file exists and is valid
        """
        if not os.path.exists(path):
            return False

        size = os.path.getsize(path)
        if size == 0:  # Remove empty files
            os.remove(path)
            return False

        return True
