"""
Configuration management for subtitle extraction.
"""

from dataclasses import dataclass


@dataclass
class ExtractorConfig:
    overwrite: bool = False

    # output format
    desired_formats: list[str] | tuple[str, str] = ("srt", "ass")

    # target languages
    languages: list[str] | tuple[str] = ("all",)
    unknown_language_as: str = "unknown"

    def is_language_wanted(self, language: str) -> bool:
        return "all" in self.languages or language in self.languages
