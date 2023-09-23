import json
import logging
import operator
import os
import pathlib
import subprocess
import tempfile
import shutil
import re

import cachetools.func
from babelfish import Language
from pgsrip import Mkv, Options, Sup, pgsrip

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = [
    "ass",
    "srt",
    "vtt",
]

FFMPEG_TEXT_FORMATS = [
    'arib_caption',
    'ass',
    'eia_608',
    'hdmv_text_subtitle',
    'jacosub',
    'microdvd',
    'mov_text',
    'mpl2',
    'pjs',
    'realtext',
    'sami',
    'srt',
    'ssa',
    'stl',
    'subrip',
    'subviewer',
    'subviewer1',
    'text',
    'ttml',
    'vplayer',
    'webvtt'
]

FFMPEG_BITMAP_FORMATS = [
    'dvb_subtitle',
    'dvb_teletext',
    'dvd_subtitle',
    'hdmv_pgs_subtitle',
    'xsub'
]


class BaseSubtitleExtractor:

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None) -> None:
        """
        Initializes BaseSubtitleExtractor
        
        Args:
          formats: The "formats" parameter is a list that specifies desired format.
          languages: The `languages` parameter is a list that specifies the languages for which the
        subtitles should be extracted.
          overwrite: The `overwrite` parameter is a boolean value that determines whether existing files
        should be overwritten or not. Defaults to False
          unknown_language_as: The "unknown_language_as" parameter is an optional parameter that specifies
        how to handle unknown languages
        """
        for f in formats:
            if f not in SUPPORTED_FORMATS:
                raise TypeError(f"{f} is not supported")

        self.formats = formats
        self.languages = languages
        self.unknown_language_as = unknown_language_as
        self.overwrite = overwrite

    @staticmethod
    def _run_subprocess(args):
        """
        The function `_run_subprocess` runs a subprocess command and raises an error if the command fails.
        
        Args:
          args: The `args` parameter is a list of strings that represents the command and its arguments to
        be executed in the subprocess. The first element of the list (`args[0]`) is the command to be
        executed, and the remaining elements are the arguments to be passed to the command.
        
        Returns:
          On success, a CompletedProcess object is returned.
        
        Raises:
          RuntimeError: A RuntimeError exception is raised if the command fails.

        """

        logger.debug(
            f"[subprocess] Running '{args[0]}'. ARGS: {' '.join(args)}")

        completed_process = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if completed_process.returncode != 0:
            err_msg = f"[subprocess] '{args[0]}' FAILED with error code: {completed_process.returncode}. STDOUT: {str(completed_process.stderr,'utf-8')}"
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        return completed_process

    @staticmethod
    @cachetools.func.fifo_cache(maxsize=1)
    def _run_ffprobe(path):
        """
        The function `_run_ffprobe` is used to probe a media file and retrieve information about its
        subtitle streams using ffprobe.
        
        Args:
          path: The `path` parameter is the path to the media file that you want to probe using ffprobe. It
        should be a string representing the file path.
        
        Returns:
          The function `_run_ffprobe` returns a dictionary containing information about the subtitle
        streams found in the media file. Key of the dictionary is the name stream in the media file

        Raises:
          RuntimeError: A RuntimeError exception is raised if the command fails.
        """
        logger.debug("[ffprobe] Probing media file...")

        args = [
            'ffprobe',
            '-of', 'json', str(path),
            '-of', 'json',
            '-show_entries', 'stream:stream_tags:format_tags',
            '-select_streams', 's',
            '-v', 'error'
        ]

        process = BaseSubtitleExtractor._run_subprocess(args)
        streams_list = json.loads(process.stdout)["streams"]
        logger.debug(f"[ffprobe] Found {len(streams_list)} subtitle stream(s)")

        info = {}

        for s in streams_list:
            i = s['index']
            info.setdefault(i, s)

        return info

    @classmethod
    def _run_ffmpeg(cls, media_path, args):
        """
        The function `_run_ffmpeg` extracts subtitles from a media file using the FFmpeg library.
        
        Args:
          media_path: The `media_path` parameter is the path to the media file from which you want to
        extract subtitles.
        
          args: The `args` parameter is a list of additional arguments that will be passed to the `ffmpeg`
        command. These arguments can be used to specify various options and settings for the `ffmpeg`
        command.

        Returns:
          On success, a CompletedProcess object is returned.
        
        Raises:
          RuntimeError: A RuntimeError exception is raised if the command fails.
        
        """
        logger.debug("[ffmpeg] Extracting subtitles...")
        ffmpeg = ['ffmpeg', '-v', 'error', '-y', '-i', str(media_path)]

        return cls._run_subprocess(ffmpeg + args)

    @classmethod
    def get_subtitle_info(cls, path):
        return cls._run_ffprobe(path)

    def is_wanted(self, media_path, subtitle_path, stream_index, supported_codecs=[]):
        """
        The function `is_wanted` checks if a subtitle file exists and meets certain criteria, such as being
        the desired language and having a supported codec before extracting.
        
        Args:
        media_path: The path to the media file that you want to check for existing subtitles.
        subtitle_path: The `subtitle_path` parameter is the path to the subtitle file that you want to
        check for existence and other conditions.
        stream_index: The `stream_index` parameter is used to specify the index of the subtitle stream in
        the media file. It is used to identify the specific subtitle stream that is being checked.
        supported_codecs: The `supported_codecs` parameter is a list of codecs that are supported for the
        subtitle stream. If the codec of the subtitle stream is not in this list, the function will return
        False and skip the subtitle.
        
        Returns:
        a boolean value. It returns True if the conditions are met and the subtitle is wanted, and False
        otherwise.
        """

        logger.debug(f"[wanted] Checking for existing subtitles...")
        ffprobe_info = self.get_subtitle_info(media_path)

        if os.path.exists(subtitle_path):

            if self.overwrite == True:
                logger.warning(
                    f"[wanted] Not skipping. --overwrite flag is set (stream:{stream_index})")
                return True

            elif os.path.getsize(subtitle_path) == 0:
                logger.warning(
                    f"[wanted] Not skipping. Empty subtitle file found (stream:{stream_index})")
                return True

            else:
                logger.debug(f"[wanted] Skipping. File Exists (stream:{stream_index})")
                return False

        elif 'all' not in self.languages and \
                ffprobe_info.get(stream_index,{}).get("tags", {}).get('language', self.unknown_language_as) not in self.languages:

            logger.debug(
                f"[wanted] Skipping. Selected track is not wanted language (stream:{stream_index})")
            return False

        elif supported_codecs != [] and ffprobe_info[stream_index]['codec_name'] not in supported_codecs:
            logger.critical(
                f"[wanted] Skipping. codec ({ffprobe_info[stream_index]['codec_name']}) not supported. (stream:{stream_index})")
            return False

        logger.debug(f"[wanted] Not Skipping. Is wanted! (stream:{stream_index})")
        return True

    def format_subtitle_path(self, media_path:str, stream_index: int, subtitle_ext:str) -> str:
        """
        The function `format_subtitle_path` takes in a media path, stream index, and subtitle extension,
        and returns a formatted filepath based on the metadata of the subtitle stream.
        
        Args:
          media_path: The `media_path` parameter is the path to the media file for which the subtitle path
        is being formatted.
          stream_index: The `stream_index` parameter represents the index of the subtitle stream in the
        media file.
          subtitle_ext: The `subtitle_ext` parameter is the file extension for the subtitle file. It
        specifies the format in which the subtitle file will be saved, such as ".srt" for SubRip format or
        ".ass" for Advanced SubStation Alpha format.
        
        Returns:
          the formatted filepath for the subtitle file.
        """

        ffprobe_info = self.get_subtitle_info(media_path)
        
        pathlib_path:pathlib.Path = pathlib.Path(media_path)

        try:
            lang = ffprobe_info[stream_index]['tags']['language']
        except KeyError:
            lang = 'unknown' if self.unknown_language_as == None else self.unknown_language_as

        # Format and remove illegal characters
        title = ffprobe_info[stream_index].get('tags', {}).get("title", None)
        title = f"{stream_index} - {title}" if title != None else str(
            stream_index)
        title = re.sub(r"""NUL|[\/:*"<>|.%$^&£?]""",
                       " - ", title).replace("  ", " ").strip()

        filename = f"{pathlib_path.stem}.{title}.{lang}.{subtitle_ext}"
        filepath = os.path.join(pathlib_path.parent, filename)

        return filepath

    def extract(self):
        raise NotImplementedError("BaseSubtitleExtractor should not be used directly")


class BitmapSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)

    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(parent.formats, parent.languages,
                  parent.overwrite, parent.unknown_language_as)
        return obj

    def _run_psgrip_ocr(self, pgssub_path, srt_path, ocr_language):
        """
        The function `_run_psgrip_ocr` performs OCR on a PGS subtitle file using the psgrip library and
        saves the result as an SRT subtitle file.
        
        Args:
          pgssub_path: The `pgssub_path` parameter is the path to the input PGS subtitle file.
          srt_path: The `srt_path` parameter is the path to the output SRT file where the OCR results will
        be saved.
          ocr_language: The `ocr_language` parameter is the language code used for performing OCR (Optical
        Character Recognition) with psgrip. It specifies the language of the text in the input subtitle file
        (`pgssub_path`).
        """

        tmp_dir = tempfile.mkdtemp()
        tmp_sub = os.path.join(tmp_dir, "tmpfile.sup")
        tmp_srt = os.path.join(tmp_dir, "tmpfile.srt")

        logger.debug("[psgrip] Preforming OCR with psgrip...")

        with open(tmp_sub, "wb") as tmp:
            with open(pgssub_path, "rb") as sup:
                tmp.write(sup.read())

        pgsrip.rip(
            Sup(tmp_sub),
            Options(languages={Language(ocr_language)},
                    overwrite=True, one_per_lang=False))

        with open(tmp_srt, "rb") as tmp:
            with open(srt_path, "wb") as srt:
                srt.write(tmp.read())

        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

    def extract(self, media_path: str, stream_indexes: list):
        """
        The function extracts and converts subtitles from a media file using FFmpeg and OCR.
        
        Args:
          media_path (str): The `media_path` parameter is a string that represents the path to the media
        file for which subtitles need to be extracted.
          stream_indexes (list): The `stream_indexes` parameter is a list of integers that represents the
        indexes of the subtitle streams to be processed. These indexes are used to identify specific
        subtitle streams within the media file.
        
        Returns:
          a list of file paths.
        """

        logger.info(
            f"[BitMapSubtitleExtractor] Processing subtitles for {media_path}, streams: {stream_indexes}")

        ffmpeg_args = []
        filelist = []

        #Extract / Convert bitmap based subtitles to PGS format
        for i in stream_indexes:
            sup_f = self.format_subtitle_path(media_path, i, 'sup')

            if self.is_wanted(media_path, sup_f, i, FFMPEG_BITMAP_FORMATS):
                ffmpeg_args.extend(['-map', f"0:{i}", "-c", "copy", sup_f])

        if ffmpeg_args != []:
            logger.info(
                "[BitMapSubtitleExtractor] Extracting subtitles to .sup format...")
            self._run_ffmpeg(media_path, ffmpeg_args)
        else:
            logger.info(
                "[BitMapSubtitleExtractor] .sup format found. Skipping...")
        

        #OCR bitmap based subtitles to SRT format
        for i in stream_indexes:
            tmp_filelist = []
            lang = self.get_subtitle_info(media_path).get(i,{}).get('tags',{}).get('language', self.unknown_language_as) 
            sup_f = self.format_subtitle_path(media_path, i, 'sup')
            srt_f = self.format_subtitle_path(media_path, i, 'srt')

            if self.is_wanted(media_path, srt_f, i):
                logger.info(
                    "[BitMapSubtitleExtractor] Performing OCR. Converting .sup to .srt")
                self._run_psgrip_ocr(sup_f, srt_f, lang)
                filelist.append(srt_f)
            else:
                logger.info(
                    "[BitMapSubtitleExtractor] .srt format found. Skipping OCR...")

            # Convert SRT to desired subtitles formats
            for ext in self.formats:
                if ext == 'srt':
                    continue

                sub_f = self.format_subtitle_path(media_path, i, ext)

                if self.is_wanted(media_path, sub_f, i):
                    tmp_filelist.append(sub_f)
                    filelist.append(sub_f)

            if len(tmp_filelist) != 0:
                logger.info(
                    "[BitMapSubtitleExtractor] Converting .srt to desired format")
                self._run_ffmpeg(srt_f, tmp_filelist)

            else:
                logger.info(
                    "[BitMapSubtitleExtractor] All desired format found, skipping...")

        return filelist


class TextSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)

    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(parent.formats, parent.languages,
                  parent.overwrite, parent.unknown_language_as)
        return obj

    def extract(self, media_path: str, stream_indexes: list):
        """
        The function extracts text subtitles from a media file based on the specified stream indexes.
        
        Args:
          media_path (str): The `media_path` parameter is a string that represents the path to the media
        file for which subtitles need to be extracted.
          stream_indexes (list): The `stream_indexes` parameter is a list of indexes representing the
        desired subtitle streams to extract from the media file.
        
        Returns:
          a list of file paths for the extracted subtitles.
        """
        
        logger.info(
            f"[TextSubtitleExtractor] Processing subtitles for {media_path}, streams: {stream_indexes}")

        ffmpeg_args = []
        filelist = []

        for i in stream_indexes:

            for ext in self.formats:
                f = self.format_subtitle_path(media_path, i, ext)

                if self.is_wanted(media_path, f, i, FFMPEG_TEXT_FORMATS):
                    ffmpeg_args.extend(['-map', f"0:{i}", f])
                    filelist.append(f)

        if ffmpeg_args != []:
            logger.info("[TextSubtitleExtractor] Extracting Subtitles...")
            self._run_ffmpeg(media_path, ffmpeg_args)
        else:
            logger.info(
                "[TextSubtitleExtractor] All desired format found, skipping...")

        return filelist


class SubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None, extract_bitmap=True) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)
        self.extract_bitmap = extract_bitmap

    def extract(self, media_path):
        """
        The function extracts subtitles from a media file by categorizing each subtitle stream into either text-based and
        bitmap-based subtitles, and uses the appropriate extractor.  
        
        Args:
          media_path: The `media_path` parameter is the path to the media file from which you want to
        extract subtitles. It should be a string representing the file path.
        
        Returns:
          a list of files that were extracted.
        """
        logger.info(f"[SubtitleExtractor] Processing {media_path}")

        ffprobe_info = self.get_subtitle_info(media_path)

        text_streams = []
        bitmap_streams = []

        for stream_i in ffprobe_info.keys():

            if 'all' not in self.languages and ffprobe_info[stream_i].get('tags',{}).get('language') not in self.languages:
                continue

            elif ffprobe_info[stream_i]['codec_name'] in FFMPEG_TEXT_FORMATS:
                text_streams.append(stream_i)

            elif ffprobe_info[stream_i]['codec_name'] in FFMPEG_BITMAP_FORMATS:
                bitmap_streams.append(stream_i)

            else:
                logger.warning(f"[SubtitleExtractor] Subtitle format '{ffprobe_info[stream_i]['codec_name']}' is  unsupported by ffmpeg. Skipping...")
                continue

        filelist = []
        if len(text_streams) != 0:
            logger.info("[SubtitleExtractor] Extracting text based subtitles")
            extractor = TextSubtitleExtractor.init(self)
            filelist1 = extractor.extract(media_path, text_streams)
            filelist.extend(filelist1)

        if len(bitmap_streams) != 0 and self.extract_bitmap:
            logger.info("[SubtitleExtractor] Extracting bitmap based subtitles")
            extractor = BitmapSubtitleExtractor.init(self)
            filelist2 = extractor.extract(media_path, bitmap_streams)
            filelist.extend(filelist2)

        return filelist