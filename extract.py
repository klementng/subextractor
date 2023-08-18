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

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False,unknown_language_as=None) -> None:
        self._cache = cachetools.FIFOCache(maxsize=2)

        for f in formats:
            if f not in SUPPORTED_FORMATS:
                raise TypeError(f"{f} is not supported")

        self.formats = formats
        self.languages = languages
        self.unknown_language_as = unknown_language_as
        self.overwrite = overwrite

    def _subprocess_run(self, args):

        logger.debug(f"Running subprocess: {' '.join(args)}")

        process = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode != 0:
            logger.critical(f"Subprocess ({args[0]}) failed: {process.stderr}")
            raise RuntimeError(
                f"Subprocess ({args[0]}) failed: {process.stderr}")

        return process

    @cachetools.cachedmethod(operator.attrgetter('_cache'))
    def _ffprobe_info(self, path):
        args = [
            'ffprobe',
            '-of', 'json', str(path),
            '-of', 'json',
            '-show_entries', 'stream:stream_tags:format_tags',
            '-select_streams', 's',
            '-v', 'error'
        ]

        process = self._subprocess_run(args)
        streams_list = json.loads(process.stdout)["streams"]
        logger.debug(f"Found {len(streams_list)} subtitles stream")

        info = {}

        for s in streams_list:
            i = s['index']

            info.setdefault(i, s)
        return info

    def _ffmpeg_extract(self, media_path, args):
        ffmpeg = ['ffmpeg', '-v', 'error', '-y', '-i', str(media_path)]

        return self._subprocess_run(ffmpeg + args)

    def _is_wanted(self, media_path, subtitle_path, stream_index, supported=[]):
        ffprobe_info = self.get_subtitle_info(media_path)

        if self.overwrite == False and os.path.exists(subtitle_path):

            if os.path.getsize(subtitle_path) == 0:
                logger.warning("Found an empty subtitle file, not skipping...")
                return True

            else:
                logger.debug("Existing file found, overwrite = false, skipping...")
                return False

        elif 'all' not in self.languages and ffprobe_info.get("tag",{}).get('language',self.unknown_language_as) not in self.languages:
            logger.debug(
                f"Subtitle track not in wanted language {self.languages}, skipping...")
            return False

        elif supported != [] and ffprobe_info[stream_index]['codec_name'] not in supported:
            logger.critical(
                f"Subtitle codec ({ffprobe_info[stream_index]['codec_name']}) not supported, skipping...")
            return False

        else:
            return True

    def get_subtitle_info(self, path, keys=None):
        info = self._ffprobe_info(path)

        if keys == None:
            return info
        else:
            for k in keys:
                try:
                    info = info[k]
                except KeyError:
                    return None

            return info

    def format_subtitle_path(self, media_path, stream_index, subtitle_ext, filename_only=False):
        
        ffprobe_info = self.get_subtitle_info(media_path)
        media_path = pathlib.Path(media_path)

        try:
            lang = ffprobe_info[stream_index]['tags']['language']
        except KeyError:
            lang = 'unknown' if self.unknown_language_as == None else self.unknown_language_as 

        title_old = ffprobe_info[stream_index].get('tags',{}).get("title", 'Untitled')
        title_old = f"{stream_index} - {title_old}"
        title_old = re.sub("[^\w_.)( -]"," ",title_old) # remove illegal character
        filename_old = f"{media_path.stem}.{title_old}.{lang}.{subtitle_ext}"
        filepath_old = os.path.join(media_path.parent, filename_old)

        title = ffprobe_info[stream_index].get('tags',{}).get("title", None)
        title = f"{stream_index} - {title}" if title != None else str(stream_index)
        title = re.sub(r"""NUL|[\/:*"<>|.%$^&£?]"""," - ",title).replace("  "," ").strip()
        filename = f"{media_path.stem}.{title}.{lang}.{subtitle_ext}"
        filepath = os.path.join(media_path.parent, filename)

        # migrate to new filename format
        if os.path.exists(filepath_old):
            logger.warning("Performing migration to new filename format")
            os.rename(filepath_old,filepath)

        if filename_only:
            return filename
        else:
            return filepath


class BitMapSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)
    
    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(parent.formats, parent.languages, parent.overwrite, parent.unknown_language_as)
        obj._cache = parent._cache
        return obj

    def _psgrip_extract(self, pgssub_path, srt_path, ocr_language):
        
        tmp_dir = tempfile.mkdtemp()
        tmp_sub = os.path.join(tmp_dir,"tmpfile.sup")
        tmp_srt = os.path.join(tmp_dir,"tmpfile.srt")

        logger.debug("Preforming OCR with psgrip...")

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
        logger.info(
            f"[BitMapSubtitleExtractor] Processing subtitles for {media_path}, streams: {stream_indexes}")

        ffmpeg_args = []
        filelist = []

        for i in stream_indexes:
            sup_f = self.format_subtitle_path(media_path, i, 'sup')

            if self._is_wanted(media_path, sup_f, i, FFMPEG_BITMAP_FORMATS):
                ffmpeg_args.extend(['-map', f"0:{i}", "-c", "copy", sup_f])

        if ffmpeg_args != []:
            logger.info(
                "[BitMapSubtitleExtractor] Extracting subtitles to .sup format...")
            self._ffmpeg_extract(media_path, ffmpeg_args)
        else:
            logger.info(
                "[BitMapSubtitleExtractor] .sup format found. Skipping...")

        for i in stream_indexes:
            tmp_filelist = []
            lang = self.get_subtitle_info(
                media_path, keys=[i, 'tags', 'language'])
            sup_f = self.format_subtitle_path(media_path, i, 'sup')
            srt_f = self.format_subtitle_path(media_path, i, 'srt')

            if self._is_wanted(media_path, srt_f, i):
                logger.info(
                    "[BitMapSubtitleExtractor] Performing OCR. Converting .sup tp .srt")
                self._psgrip_extract(sup_f, srt_f, lang)
                filelist.append(srt_f)
            else:
                logger.info(
                    "[BitMapSubtitleExtractor] .srt format found. Skipping OCR...")

            # Convert to desired subtitles
            for ext in self.formats:
                if ext == 'srt':
                    continue

                sub_f = self.format_subtitle_path(media_path, i, ext)

                if self._is_wanted(media_path, sub_f, i):
                    tmp_filelist.append(sub_f)
                    filelist.append(sub_f)

            if len(tmp_filelist) != 0:
                logger.info(
                    "[BitMapSubtitleExtractor] Converting .srt to desired format")
                self._ffmpeg_extract(srt_f, tmp_filelist)

            else:
                logger.info(
                    "[BitMapSubtitleExtractor] All desired format found, skipping...")

        return filelist


class TextSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)

    @classmethod
    def init(cls, parent: BaseSubtitleExtractor):
        obj = cls(parent.formats, parent.languages, parent.overwrite, parent.unknown_language_as)
        obj._cache = parent._cache
        return obj

    def extract(self, media_path: str, stream_indexes: list):
        logger.info(
            f"[TextSubtitleExtractor] Processing subtitles for {media_path}, streams: {stream_indexes}")

        ffmpeg_args = []
        filelist = []

        for i in stream_indexes:

            for ext in self.formats:
                f = self.format_subtitle_path(media_path, i, ext)

                if self._is_wanted(media_path, f, i, FFMPEG_TEXT_FORMATS):
                    ffmpeg_args.extend(['-map', f"0:{i}", f])
                    filelist.append(f)

        if ffmpeg_args != []:
            logger.info("[TextSubtitleExtractor] Extracting Subtitles...")
            self._ffmpeg_extract(media_path, ffmpeg_args)
        else:
            logger.info(
                "[TextSubtitleExtractor] All desired format found, skipping...")

        return filelist


class SubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False, unknown_language_as=None,extract_bitmap=True) -> None:
        super().__init__(formats, languages, overwrite, unknown_language_as)
        self.extract_bitmap = extract_bitmap

    def extract(self, media_path):
        logger.info(f"[SubtitleExtractor] Processing {media_path}")

        ffprobe_info = self.get_subtitle_info(media_path)

        text_streams = []
        bitmap_streams = []

        for i in ffprobe_info.keys():

            if 'all' not in self.languages and ffprobe_info[i]['tags'].get('language') not in self.languages:
                continue

            elif ffprobe_info[i]['codec_name'] in FFMPEG_TEXT_FORMATS:
                text_streams.append(i)

            elif ffprobe_info[i]['codec_name'] in FFMPEG_BITMAP_FORMATS:
                bitmap_streams.append(i)

            else:
                pass

        filelist = []
        if len(text_streams) != 0:
            extractor = TextSubtitleExtractor.init(self)
            filelist1 = extractor.extract(media_path, text_streams)
            filelist.extend(filelist1)

        if len(bitmap_streams) != 0 and self.extract_bitmap:
            extractor = BitMapSubtitleExtractor.init(self)
            filelist2 = extractor.extract(media_path, bitmap_streams)
            filelist.extend(filelist2)

        return filelist
