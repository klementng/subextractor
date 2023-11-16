
<a name="readme-top"></a>

# Subtitle Extract

## About The Project

Extract text and image based subtitles from media files using ffmpeg.

## Installation
see [docker-compose.yml](./docker-compose.yml)

## Usage:
```sh
usage: main.py [-h] [--formats {ass,srt,vtt} [{ass,srt,vtt} ...]] [--languages LANGUAGES [LANGUAGES ...]] [--unknown_language_as UNKNOWN_LANGUAGE_AS] [--overwrite]
               [--disable_bitmap_extraction] [--postprocess_only] [--postprocessing POSTPROCESSING] [--scan_interval SCAN_INTERVAL] [--log_level LOG_LEVEL]
               [--log_file LOG_FILE] [--disable_progress_bar] [--exclude_videos EXCLUDE_VIDEOS] [--exclude_subtitles EXCLUDE_SUBTITLES] [--exclude_mode {e,e+a}]
               [--threads THREADS]
               path

positional arguments:
  path                  path to media file/folder

options:
  -h, --help            show this help message and exit
  --formats {ass,srt,vtt} [{ass,srt,vtt} ...]
                        output subtitles formats
  --languages LANGUAGES [LANGUAGES ...]
                        extract subtitle for selected languages, use 'all' to extract all languages
  --unknown_language_as UNKNOWN_LANGUAGE_AS
                        treat unknown language as
  --overwrite           overwrite existing subtitle file
  --disable_bitmap_extraction
                        disable extraction for bitmap based subtitle extraction via OCR
  --postprocess_only    only do conduct post processing
  --postprocessing POSTPROCESSING
                        path to postprocessing config file
  --scan_interval SCAN_INTERVAL
                        interval to monitor and scan folder in mins (set 0 to disable and exit upon completion)
  --log_level LOG_LEVEL
                        setting logging level
  --log_file LOG_FILE   path to log file
  --disable_progress_bar
                        enable progress bar
  --exclude_videos EXCLUDE_VIDEOS
                        path to a newline separated file with paths to video files to exclude (applied when --postprocess_only flag is NOT set)
  --exclude_subtitles EXCLUDE_SUBTITLES
                        path to a newline separated file with paths to subtitles files to exclude (applied only when --postprocess_only flag is set)
  --exclude_mode {e,e+a}
                        set file exclusion behavior, e = exclude only, e+a = exclude and append newly processed file
  --threads THREADS     set number of extraction threads 
```
