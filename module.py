import glob
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from extract import (
    BitmapSubtitleExtractor,
    TextSubtitleExtractor,
    ExtractorConfig,
    MediaProber,
)

from postprocessing import SubtitleFormatter

logger = logging.getLogger(__name__)


class Module(ABC):
    def __init__(
        self,
        excluded_enable: bool = False,
        excluded_filelist: str = "",
        excluded_append: bool = True,
        **kwargs,
    ) -> None:

        self.excluded_enable = excluded_enable
        self.excluded_filelist = excluded_filelist
        self.excluded_append = excluded_append

    def add_excluded_files(self, paths: list[str]):
        if self.excluded_enable == False:
            return set()

        if self.excluded_append and self.excluded_filelist:
            with open(self.excluded_filelist, "a") as f:
                f.write("\n".join(paths))

    def get_excluded_files(self) -> set:
        if self.excluded_enable == False or not self.excluded_filelist:
            return set()

        if not os.path.exists(self.excluded_filelist):
            logger.warning("No excluded file! File not found!")
            return set()

        with open(self.excluded_filelist) as f:
            return set(f.read().splitlines())

    def get_filelist(self, path):
        extensions = "|".join(self.get_file_extensions())
        regex = f"(?i)\\.({extensions})$"
        excluded_files = self.get_excluded_files()
        files = set()

        if os.path.isdir(path):
            for f in glob.iglob(os.path.join(path, "**", "**"), recursive=True):
                if re.search(regex, f) and f not in excluded_files:
                    files.add(f)
        else:
            files = {path}

        logger.info(
            f"Found {len(files)} files to be processed, {len(excluded_files)} excluded"
        )
        return list(files)

    @abstractmethod
    def get_file_extensions(self) -> list[str]:
        pass

    @abstractmethod
    def process(self, path):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls):
        pass


class ExtractionModule(Module):

    def __init__(self, config: ExtractorConfig, extract_bitmap=False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config

        self.extract_bitmap = extract_bitmap
        self.prober = MediaProber()

    @classmethod
    def from_dict(cls, settings: dict):

        config = ExtractorConfig(**settings.pop("config"))
        return cls(config, **settings)

    def get_file_extensions(self) -> tuple[str, str, str, str, str]:
        return ("mkv", "mp4", "webm", "ts", "ogg")

    def process(self, filepaths: list[str]):
        extractor1 = TextSubtitleExtractor(self.config, self.prober)
        extractor2 = BitmapSubtitleExtractor(self.config, self.prober)

        output_files = []
        for path in filepaths:
            try:
                output_files += extractor1.extract(path)

                if self.extract_bitmap:
                    output_files += extractor2.extract(path)

            except Exception as e:
                logger.critical(f"An error has occuerd while extracting: {e}")

        if self.excluded_append:
            self.add_excluded_files(filepaths)

        return output_files


class PostprocessorModule(Module):

    def __init__(
        self,
        workflow_file: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.workflow_file = workflow_file

    @classmethod
    def from_dict(cls, settings: dict):
        return cls(settings["config"]["workflow_file"], **settings)

    def get_file_extensions(self) -> tuple[str, str, str]:
        return ("ass", "srt", "vtt")

    def process(self, filepaths: list[str]):
        formatter = SubtitleFormatter(self.workflow_file)

        output_files = []
        for path in filepaths:
            try:
                output_files += formatter.format(path)
            except Exception as e:
                logger.critical(f"An error has occuerd while formatting: {e}")

        if self.excluded_append:
            self.add_excluded_files(output_files)

        return output_files
