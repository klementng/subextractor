
<a name="readme-top"></a>

# Subtitle Extract

## About The Project

Extract text and image based subtitles from media files using ffmpeg.

## Installation

see [docker-compose.yml](./docker-compose.yml)

## Usage

### Extract only mode

To extract subtitles only

```sh
usage: main.py [-h] [--threads THREADS] [--scan_interval SCAN_INTERVAL] [--disable_progress_bar] [--exclude_mode {e,e+a}] [--log_level LOG_LEVEL] [--log_file LOG_FILE]
               [--output_formats {ass,srt,vtt} [{ass,srt,vtt} ...]] [--languages LANGUAGES [LANGUAGES ...]] [--unknown_language_as UNKNOWN_LANGUAGE_AS]
               [--disable_bitmap_extraction] [--overwrite] [--exclude_videos EXCLUDE_VIDEOS]
               {extract,format,full} path

extract subtitle from video files

positional arguments:
  {extract,format,full}
                        select mode
  path                  path to media file/folder

options:
  -h, --help            show this help message and exit
  --threads THREADS     set number of running threads
  --scan_interval SCAN_INTERVAL
                        interval to scan folder in mins (set 0 to disable and exit upon completion)
  --disable_progress_bar
                        enable progress bar
  --exclude_mode {e,e+a}
                        set file exclusion behavior, e = exclude only, e+a = exclude and append newly processed file
  --log_level LOG_LEVEL
                        setting logging level
  --log_file LOG_FILE   path to log file
  --output_formats {ass,srt,vtt} [{ass,srt,vtt} ...]
                        output subtitles formats
  --languages LANGUAGES [LANGUAGES ...]
                        extract subtitle for selected languages, use 'all' to extract all languages
  --unknown_language_as UNKNOWN_LANGUAGE_AS
                        treat unknown language as
  --disable_bitmap_extraction
                        disable extraction for bitmap based subtitle extraction via OCR
  --overwrite           overwrite existing subtitle file
  --exclude_videos EXCLUDE_VIDEOS
                        path to a newline separated file with paths to video files to exclude
```

### Format only mode

To format / postprocessing of subtitles

```sh
usage: main.py [-h] [--threads THREADS] [--scan_interval SCAN_INTERVAL] [--disable_progress_bar] [--exclude_mode {e,e+a}] [--log_level LOG_LEVEL]
               [--log_file LOG_FILE] [--postprocessing POSTPROCESSING] [--exclude_subtitles EXCLUDE_SUBTITLES]
               {extract,format,full} path

Postprocessing of subtitles

positional arguments:
  {extract,format,full}
                        select mode
  path                  path to media file/folder

options:
  -h, --help            show this help message and exit
  --threads THREADS     set number of running threads
  --scan_interval SCAN_INTERVAL
                        interval to scan folder in mins (set 0 to disable and exit upon completion)
  --disable_progress_bar
                        enable progress bar
  --exclude_mode {e,e+a}
                        set file exclusion behavior, e = exclude only, e+a = exclude and append newly processed file
  --log_level LOG_LEVEL
                        setting logging level
  --log_file LOG_FILE   path to log file
  --postprocessing POSTPROCESSING
                        path to postprocessing config file
  --exclude_subtitles EXCLUDE_SUBTITLES
                        path to a newline separated file with paths to subtitles files to exclude
```
