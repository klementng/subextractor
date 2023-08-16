import json
import logging
import operator
import os
import pathlib
import subprocess

import cachetools.func
from babelfish import Language
from pgsrip import Mkv, Options, Sup, pgsrip

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = [
    "ass",
    "srt",
    "ssa",
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

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False) -> None:
        self._cache = cachetools.FIFOCache(maxsize=5)

        for f in formats:
            if f not in SUPPORTED_FORMATS:
                raise TypeError(f"{f} is not supported")

        self.formats = formats
        self.languages = languages
        self.overwrite = overwrite

    def _subprocess_run(self, args):

        logger.debug(f"Running subprocess: {args}")
        
        process = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode != 0:
            logger.critical(f"Subprocess ({args[0]}) failed: {process.stderr}")
            raise RuntimeError(
                f"Subprocess ({args[0]}) failed: {process.stderr}")

        return process

    @cachetools.cachedmethod(operator.attrgetter('_cache'))
    def _run_ffprobe(self,path):
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

            info.setdefault(i,s)
        return info        

    def _ffmpeg_extract(self, media_path, args):
        ffmpeg = ['ffmpeg', '-i', str(media_path), '-y', '-v', 'error']

        return self._subprocess_run(ffmpeg + args)
    
    def _skip(self,media_path,subtitle_path,stream_index,supported=[]):
        ffprobe_info = self.get_subtitle_info(media_path)

        if self.overwrite == False and os.path.exists(subtitle_path):
            logger.debug("Existing file found, overwrite = false, skipping...")
            return True
                
        elif 'all' not in self.languages and ffprobe_info[stream_index]['tags'].get('language') not in self.languages:
            logger.debug("Subtitle track not in wanted language, skipping...")
            return True
        
        elif supported != [] and ffprobe_info[stream_index]['codec_name'] not in supported:
            logger.critical("Subtitle not supported by ffmpeg, skipping...")
            return True
        
        else:
            return False
    

    def get_subtitle_info(self ,path, keys=None):
        info = self._run_ffprobe(path)
        
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

        lang = ffprobe_info[stream_index]['tags'].get('language','unknown')
        title = ffprobe_info[stream_index]['tags'].get("title",'Untitled')

        title = f"{stream_index} - {title}"

        media_path = pathlib.Path(media_path)

        filename = f"{media_path.stem}.{title}.{lang}.{subtitle_ext}"

        if filename_only:
            return filename
        
        else:
            return os.path.join(media_path.parent,filename)



class BitMapSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False) -> None:
        super().__init__(formats, languages, overwrite)
    
    @classmethod
    def init_from_parent(cls, parent:BaseSubtitleExtractor):
        return cls(parent.formats, parent.languages,parent.overwrite)
    
    
    def _psgrip_extract(self, pgssub_path,srt_path,ocr_language):

        logger.debug("Preforming OCR with psgrip...")
        
        with open("tmpfile.sup","wb") as tmp:
            with open(pgssub_path, "rb") as sup:
                tmp.write(sup.read())
        
        pgsrip.rip(
            Sup("tmpfile.sup"), 
            Options(languages={Language(ocr_language)},
                    overwrite=True, one_per_lang=False))
        
        with open("tmpfile.srt","rb") as tmp:
            with open(srt_path, "wb") as srt:
                srt.write(tmp.read())
        
        os.remove("tmpfile.sup")
        os.remove("tmpfile.srt")

    def extract(self,media_path: str, stream_indexes: list):
        logger.info(f"Processing (BITMAP) subtitles for {media_path}, stream: {stream_indexes}")

        ffmpeg_args = []
        filelist = []

        for i in stream_indexes:
            sup_f = self.format_subtitle_path(media_path,i,'sup')
            
            if not self._skip(media_path,sup_f,i,FFMPEG_BITMAP_FORMATS):
                ffmpeg_args.extend(['-map', f"0:{i}", "-c", "copy", sup_f])
            
        if ffmpeg_args != []:
            self._ffmpeg_extract(media_path, ffmpeg_args)

        for i in stream_indexes:
            tmp_filelist = []
            lang = self.get_subtitle_info(media_path,keys=[i,'tags','language'])            
            sup_f = self.format_subtitle_path(media_path,i,'sup')
            srt_f = self.format_subtitle_path(media_path,i,'srt')

            if not self._skip(media_path,srt_f,i):
                self._psgrip_extract(sup_f,srt_f,lang)
                filelist.append(srt_f)
            
            # Convert to desired subtitles
            logger.debug("Converting extracted subtitles to desired formats...")
            for ext in self.formats:
                if ext == 'srt':
                    continue

                sub_f =  self.format_subtitle_path(media_path,i,ext)
                
                if not self._skip(media_path,sub_f,i):
                    tmp_filelist.append(sub_f)
                    filelist.append(sub_f)
            
            if len(tmp_filelist) != 0:
                self._ffmpeg_extract(srt_f,tmp_filelist)

        return filelist

class TextSubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False) -> None:
        super().__init__(formats, languages, overwrite)

    @classmethod
    def init_from_parent(cls, parent:BaseSubtitleExtractor):
        return cls(parent.formats, parent.languages,parent.overwrite)

    def extract(self, media_path: str, stream_indexes: list):
        logger.info(f"Processing (TEXT) subtitles for {media_path}, stream: {stream_indexes}")

        
        ffmpeg_args = []
        filelist = []

        for i in stream_indexes:

            for ext in self.formats:
                f = self.format_subtitle_path(media_path,i,ext)
                
                if not self._skip(media_path,f,i,FFMPEG_TEXT_FORMATS):
                    ffmpeg_args.extend(['-map', f"0:{i}", f])
                    filelist.append(f)
        
        if ffmpeg_args != []:
            self._ffmpeg_extract(media_path, ffmpeg_args)

        return filelist


class SubtitleExtractor(BaseSubtitleExtractor):

    def __init__(self, formats=['srt'], languages=['all'], overwrite=False) -> None:
        super().__init__(formats, languages, overwrite)
    
    def extract(self,media_path):
        logger.info(f"Processing {media_path}")

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
            extractor = TextSubtitleExtractor.init_from_parent(self)
            filelist1 = extractor.extract(media_path,text_streams)
            filelist.extend(filelist1)

        if len(bitmap_streams) != 0:
            extractor = BitMapSubtitleExtractor.init_from_parent(self)
            filelist2 = extractor.extract(media_path,bitmap_streams)
            filelist.extend(filelist2)

        return filelist

















