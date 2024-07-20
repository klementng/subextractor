import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

import cachetools
import cachetools.func
from babelfish import Language
from pgsrip import Options, Sup, pgsrip

SUPPORTED_FORMATS = [
    "ass",
    "srt",
    "vtt",
]

FFMPEG_TEXT_FORMATS = [
    "arib_caption",
    "ass",
    "eia_608",
    "hdmv_text_subtitle",
    "jacosub",
    "microdvd",
    "mov_text",
    "mpl2",
    "pjs",
    "realtext",
    "sami",
    "srt",
    "ssa",
    "stl",
    "subrip",
    "subviewer",
    "subviewer1",
    "text",
    "ttml",
    "vplayer",
    "webvtt",
]


FFMPEG_BITMAP_FORMATS = [
    "dvb_subtitle",
    "dvb_teletext",
    "dvd_subtitle",
    "hdmv_pgs_subtitle",
    "xsub",
]


class BaseSubtitleExtractor:

    log = logging.getLogger("BaseSubtitleExtractor")

    def __init__(
        self,
        formats: list[str] = ["srt"],
        wanted_languages: list[str] = ["all"],
        overwrite: bool = False,
        unknown_language_as: str | None = None,
    ) -> None:
        """Initialize the BaseSubtitleExtractor class object. This class should not be directly

        Args:
            formats (list[str], optional): List of target subtitle formats to output. Defaults to ['srt'].
            wanted_languages (list[str], optional): List of languages to embedded subtitle to extract from. Defaults to ['all'].
            overwrite (bool, optional): Force extraction if all output subtitle file already exist, skips extraction otherwise. Defaults to False.
            unknown_language_as (str | None, optional): Treat subtitle with no language tag as specified language. Defaults to None.

        Raises:
            TypeError: Occurs when desired format is not supported by ffmpeg
        """

        for f in formats:
            if f not in SUPPORTED_FORMATS:
                raise TypeError(f"{f} is not supported")

        self.formats = formats
        self.wanted_languages = wanted_languages
        self.unknown_language_as = (
            unknown_language_as if unknown_language_as != None else "unknown"
        )
        self.overwrite = overwrite

        if overwrite is True:
            self.log.warning("Overwriting of existing subtitle files is set")

        self._ffprobe_cache = cachetools.FIFOCache(128)

    @classmethod
    def _run_subprocess(cls, args: list[str]):
        """Wrapper method for running subprocess on system os

        Args:
            args (list[str]): list of arguments to pass to subprocess.run

        Raises:
            RuntimeError: occurs when return code of process !=0

        Returns:
            subprocess.CompletedProcess: CompletedProcess object with relevant information
        """

        cls.log.debug(f"Running '{args[0]}'. ARGS: {' '.join(args)}")

        c_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if c_process.returncode != 0:
            err_msg = "'{}' FAILED with error code: {}. STDERR: {}".format(
                c_process.returncode, c_process.stderr, str(c_process.stderr, "utf-8")
            )
            cls.log.critical(err_msg)
            cls.log.critical(f"ARGS: {' '.join(args)}")
            raise RuntimeError(err_msg)

        return c_process

    @classmethod
    def _run_ffprobe(cls, path: str) -> dict:
        """Probe a media file and retrieve information about its subtitle streams using ffprobe.

        Args:
            path: The path to a video file

        Returns:
            dict: A dictionary containing information of all subtitle stream from ffprobe.

            Example
                5: {"index": 5,
                    "codec_name": "subrip",
                    "codec_long_name": "SubRip subtitle",
                    "codec_type": "subtitle",
                    "codec_tag_string": "[0][0][0][0]",
                    "codec_tag": "0x0000",
                    "r_frame_rate": "0/0",
                    "avg_frame_rate": "0/0",
                    "time_base": "1/1000",
                    "start_pts": 42,
                    "start_time": "0.042000",
                    "disposition": {
                        "default": 0,
                        "dub": 0,
                        "original": 0,
                        "comment": 0,
                        "lyrics": 0,
                        "karaoke": 0,
                        "forced": 0,
                        "hearing_impaired": 0,
                        "visual_impaired": 0,
                        "clean_effects": 0,
                        "attached_pic": 0,
                        "timed_thumbnails": 0
                    },
                    "tags": {
                        "language": "fre"
                    }
                },

        Raises:
            RuntimeError: A RuntimeError exception is raised if the command fails.
        """

        args = [
            "ffprobe",
            "-of",
            "json",
            str(path),
            "-of",
            "json",
            "-show_entries",
            "stream:stream_tags:format_tags",
            "-select_streams",
            "s",
            "-v",
            "error",
        ]
        cls.log.debug(f"ffprobe media information at {path}...")
        try:
            process = cls._run_subprocess(args)
        except RuntimeError as e:
            cls.log.critical(f"ffprobe command failed!")
            raise

        streams_list = json.loads(process.stdout)["streams"]

        info = {}

        for s in streams_list:
            i = s["index"]
            info.setdefault(i, s)

        return info

    @classmethod
    def _run_ffmpeg(cls, path: str, args: list[str]) -> subprocess.CompletedProcess:
        """wrapper function for running ffmpeg

        Args:
            path (str): path to video file
            args (list[str]): arguments to pass to ffmpeg

        Raises:
            RuntimeError: Runtime error is raised when ffmpeg commands fail

        Returns:
            subprocess.CompletedProcess: A class that containing information about ffmpeg process that has finished running
        """

        cls.log.debug("Extracting subtitles...")
        ffmpeg = ["ffmpeg", "-v", "error", "-y", "-i", str(path)]

        try:
            return cls._run_subprocess(ffmpeg + args)
        except RuntimeError as e:
            cls.log.critical(f"FFmpeg command failed!")
            raise

    def get_subtitle_info(self, path: str) -> dict:
        """Return subtitle information from ffmpeg. Ensure that 'tags' & ['tags']['language'] keys are set

        Args:
            path (str): path to video file

        Returns:
            dict: subtitle information
        """

        # Check if in cache
        if path in self._ffprobe_cache:
            return self._ffprobe_cache[path]

        info = self._run_ffprobe(path)

        self.log.debug(f"Found {len(info)} subtitle stream(s)")
        for k in info:
            info[k].setdefault("tags", {})
            info[k]["tags"].setdefault("language", self.unknown_language_as)

        self._ffprobe_cache[path] = info
        return info

    def is_wanted(
        self, video_path: str, subtitle_path: str, stream_index: int, codecs: list = []
    ) -> bool:
        """Check for existing / missing subtitles to skipped or extracted

        Args:
            video_path (str): path to video file
            subtitle_path (str): output path of subtitle
            stream_index (int): index of subtitle stream in video
            codecs (list, optional): supported subtitle codec to extract from. Defaults to [].

        Returns:
            bool: True if subtitle needs to be extracted from video file, False to skip extraction.
        """

        ffprobe_info = self.get_subtitle_info(video_path)

        sub_lang = ffprobe_info[stream_index]["tags"]["language"]
        sub_codec = ffprobe_info[stream_index]["codec_name"]

        if os.path.exists(subtitle_path):

            if self.overwrite == True:
                self.log.debug(
                    f"Not skipping. --overwrite flag is set (stream:{stream_index})"
                )
                return True

            elif os.path.getsize(subtitle_path) == 0:
                os.remove(subtitle_path)
                self.log.debug(
                    f"Not skipping. Empty subtitle file found (stream:{stream_index}). Deleted file: {subtitle_path}"
                )

                return True

            else:
                self.log.debug(f"Skipping. File Exists (stream:{stream_index})")

                return False

        elif (
            "all" not in self.wanted_languages and sub_lang not in self.wanted_languages
        ):
            self.log.debug(
                f"Skipping. Selected track is not wanted language (stream:{stream_index})"
            )

            return False

        elif codecs != [] and sub_codec not in codecs:
            self.log.warning(
                f"Skipping. codec ({sub_codec}) not supported. (stream:{stream_index})"
            )

            return False

        else:
            self.log.debug(f"Not Skipping. Is wanted! (stream:{stream_index})")

            return True

    def format_subtitle_path(
        self, video_path: str, stream_index: int, subtitle_ext: str
    ) -> str:
        """
        Get output path of extracted subtitle

        Args:
            video_path (str): path to video file.
            stream_index (int): index of stream corresponding to subtitle stream in video file
            subtitle_ext (str): Extension to use for subtitle.

        Returns:
            str: output subtitle path in {video_path}.{title}.{lang}.{ext}"
        """

        sub_info = self.get_subtitle_info(video_path)

        pathlib_path: pathlib.Path = pathlib.Path(video_path)

        lang = sub_info[stream_index]["tags"]["language"]

        # Format and remove illegal characters
        title = sub_info[stream_index]["tags"].get("title")
        title = f"{stream_index} - {title}" if title != None else str(stream_index)
        title = re.sub(r"""NUL|[\/:*"<>|.%$^&£?]""", " - ", title)
        title = title.replace("  ", " ").strip()

        filename = f"{pathlib_path.stem}.{title}.{lang}.{subtitle_ext}"
        filepath = os.path.join(pathlib_path.parent, filename)

        return filepath

    def extract(self):
        raise NotImplementedError(
            "BaseSubtitleExtractor.extract() should not be used directly"
        )


class BitmapSubtitleExtractor(BaseSubtitleExtractor):

    log = logging.getLogger("BitmapSubtitleExtractor")

    def __init__(
        self,
        formats=["srt"],
        wanted_languages=["all"],
        overwrite=False,
        unknown_language_as: str | None = None,
    ) -> None:
        super().__init__(formats, wanted_languages, overwrite, unknown_language_as)

    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(
            parent.formats,
            parent.wanted_languages,
            parent.overwrite,
            parent.unknown_language_as,
        )
        obj._ffprobe_cache = parent._ffprobe_cache
        return obj

    @classmethod
    def _run_psgrip_ocr(
        cls, sup_input_path: str, srt_output_path: str, ocr_language: str
    ):
        """
        Performs OCR on a PGS subtitle file using the psgrip library and
        saves the result to an SRT subtitle file.

        Args:
            sup_input_path(str): path to the input PGS subtitle (.sup) file
            srt_output_path(str): path to the output SRT file
            ocr_language(str): iso language code used for performing OCR

        Raises:
            RuntimeError: Failed Extraction
            ValueError: Unknown Language
        """

        # required as bandaid fix, psgrip crashes with space in filename
        tmp_dir = tempfile.mkdtemp()
        tmp_sub = os.path.join(tmp_dir, "psgrip.sup")
        tmp_srt = os.path.join(tmp_dir, "psgrip.srt")

        cls.log.debug("Preforming OCR with psgrip...")
        with open(tmp_sub, "wb") as tmp:
            with open(sup_input_path, "rb") as sup:
                tmp.write(sup.read())

        try:
            pgsrip.rip(
                Sup(tmp_sub),
                Options(
                    languages={Language(ocr_language)},
                    overwrite=True,
                    one_per_lang=False,
                ),
            )
            with open(tmp_srt, "rb") as tmp:
                with open(srt_output_path, "wb") as srt:
                    srt.write(tmp.read())

        except ValueError as e:
            cls.log.critical(
                f"Unable to do OCR on unknown subtitle language: {ocr_language}"
            )
            raise e

        except Exception as e:
            cls.log.critical("OCR Failed..." + str(e))
            raise

        finally:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)

    def extract(self, video_path: str, stream_indexes: list) -> list[str]:
        """Extract subtitle files from a video file .

        Args:
            video_path (str): path to video
            stream_indexes (list): indexes of corresponding to subtitle streams in video file

        Returns:
            list[str]: paths to newly extracted / converted subtitles
        """

        self.log.debug(
            f"Processing subtitles for {video_path}, streams: {stream_indexes}"
        )

        ffmpeg_args = []
        # filelist = []
        convert_list = []

        # Extract / Convert bitmap based subtitles to PGS format
        for i in stream_indexes:
            sup_fp = self.format_subtitle_path(video_path, i, "sup")

            if self.is_wanted(video_path, sup_fp, i, FFMPEG_BITMAP_FORMATS):
                ffmpeg_args.extend(["-map", f"0:{i}", "-c", "copy", sup_fp])

        if ffmpeg_args != []:
            self.log.debug("Extracting subtitles to .sup format...")
            self._run_ffmpeg(video_path, ffmpeg_args)
        else:
            self.log.debug("all .sup format found. Skipping ffmpeg extraction..")

        # OCR bitmap based subtitles to SRT format
        for i in stream_indexes:
            lang = self.get_subtitle_info(video_path)[i]["tags"]["language"]
            sup_fp = self.format_subtitle_path(video_path, i, "sup")
            srt_fp = self.format_subtitle_path(video_path, i, "srt")

            if lang == None:
                self.log.warning(
                    f"Unable to do OCR on unknown subtitle language, skipping..stream:{i}"
                )

            elif self.is_wanted(video_path, srt_fp, i):
                self.log.debug("Performing OCR. Converting .sup to .srt")
                self._run_psgrip_ocr(sup_fp, srt_fp, lang)

            else:
                self.log.debug(".srt format found. Skipping OCR...")

            # Converting extracted srt to desired formats
            for ext in self.formats:
                if ext == "srt":
                    continue

                target_sub_path = self.format_subtitle_path(video_path, i, ext)

                if self.is_wanted(video_path, target_sub_path, i):
                    convert_list.append(target_sub_path)
                    # filelist.append(sub_f)

            if len(convert_list) != 0:
                self.log.debug("Converting .srt to desired format")
                self._run_ffmpeg(srt_fp, convert_list)

            else:
                self.log.debug("All desired format found, skipping...")

        return convert_list


class TextSubtitleExtractor(BaseSubtitleExtractor):

    log = logging.getLogger("TextSubtitleExtractor")

    def __init__(
        self,
        formats=["srt"],
        wanted_languages=["all"],
        overwrite=False,
        unknown_language_as=None,
    ) -> None:
        super().__init__(formats, wanted_languages, overwrite, unknown_language_as)

    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(
            parent.formats,
            parent.wanted_languages,
            parent.overwrite,
            parent.unknown_language_as,
        )
        obj._ffprobe_cache = parent._ffprobe_cache
        return obj

    def extract(self, video_path: str, stream_indexes: list) -> list[str]:
        """Extract text based subtitles from a video file .

        Args:
            video_path (str): path to video
            stream_indexes (list): indexes of corresponding to subtitle streams in video file

        Returns:
            list[str]: paths to newly extracted / converted subtitles
        """

        self.log.debug(
            f"Processing subtitles for {video_path}, streams: {stream_indexes}"
        )

        ffmpeg_args = []
        out_paths = []

        for i in stream_indexes:

            for ext in self.formats:
                out_path = self.format_subtitle_path(video_path, i, ext)

                if self.is_wanted(video_path, out_path, i, FFMPEG_TEXT_FORMATS):
                    ffmpeg_args.extend(["-map", f"0:{i}", out_path])
                    out_paths.append(out_path)

        if ffmpeg_args != []:
            self.log.debug("Extracting Subtitles...")
            self._run_ffmpeg(video_path, ffmpeg_args)
        else:
            self.log.debug("All desired format found, skipping...")

        return out_paths


class SubtitleExtractor(BaseSubtitleExtractor):

    log = logging.getLogger("SubtitleExtractor")

    def __init__(
        self,
        formats=["srt"],
        languages=["all"],
        overwrite=False,
        unknown_language_as: str | None = None,
        disable_bitmap_extract: bool = False,
    ) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)
        self.disable_bitmap_extract = disable_bitmap_extract
        if disable_bitmap_extract is True:
            self.log.warning("Bitmap based subtitle extraction is disabled")

    def extract(self, video_path: str) -> list[str]:
        """Extract text/bitmap based subtitles from a video file .

        Args:
            video_path (str): path to video

        Returns:
            list[str]: paths to newly extracted / converted subtitles
        """
        self.log.debug(f"Processing {video_path}")

        ffprobe_info = self.get_subtitle_info(video_path)

        text_streams = []
        bitmap_streams = []

        for stream_i in ffprobe_info:
            lang = ffprobe_info[stream_i]["tags"]["language"]
            codec = ffprobe_info[stream_i]["codec_name"]

            if "all" not in self.wanted_languages and lang not in self.wanted_languages:
                continue

            elif codec in FFMPEG_TEXT_FORMATS:
                text_streams.append(stream_i)

            elif codec in FFMPEG_BITMAP_FORMATS:
                bitmap_streams.append(stream_i)

            else:
                self.log.warning(
                    f"Subtitle codec '{codec}' is unsupported by ffmpeg. Skipping..."
                )

        extracted_files = []
        if len(text_streams) > 0:
            self.log.debug("Extracting text based subtitles")
            extractor_text = TextSubtitleExtractor.init(self)
            filelist1 = extractor_text.extract(video_path, text_streams)
            extracted_files.extend(filelist1)

        if len(bitmap_streams) > 0 and not self.disable_bitmap_extract:
            self.log.debug("Extracting bitmap based subtitles")
            extractor_bitmap = BitmapSubtitleExtractor.init(self)
            filelist2 = extractor_bitmap.extract(video_path, bitmap_streams)
            extracted_files.extend(filelist2)

        return extracted_files
