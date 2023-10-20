
<a name="readme-top"></a>


# Subtitle Extract

<!-- ABOUT THE PROJECT -->
## About The Project

Extract text and image based subtitles from media files using ffmpeg.

For image / bitmap based subtitiles, it is first converted to pgssub and extracted using [pgsrip](https://github.com/ratoaq2/pgsrip) to srt. From srt it is converted to the desired formats.

## Installation

### Docker Compose
```yaml
  subtitle-extract:
    #image: ghcr.io/klementng/subtitle-extract:main
    build: https://github.com/klementng/subtitle-extract.git#dev
    container_name: jellyfin-subtitle-extract
    user: ${PUID}:${PGID}
    environment:
      - TZ=${TZ}
    volumes:
      - ./subtitle-extract:/config
      - ./path/to/media/media
    command: /media --formats srt ass --languages eng --scan_interval 15 --log_level INFO --postprocessing postprocess.yml --unknown_language_as eng --exclude_videos /config/scanned-video.txt --exclude_mode e+a
    restart: unless-stopped
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage:

```sh
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
                        path to a newline separated file with paths to video files to exclude
  --exclude_subtitles EXCLUDE_SUBTITLES
                        path to a newline separated file with paths to subtitles files to exclude
  --exclude_mode {e,e+a}
                        set file exclusion behavior, e = exclude only, e+a = exclude and append new extracted file
  --threads THREADS     set number of extraction thread
```
