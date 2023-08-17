
<a name="readme-top"></a>


# Subtitle Extract

<!-- ABOUT THE PROJECT -->
## About The Project

Extract text and image based subtitles from media files using ffmpeg.

For image / bitmap based subtitiles, it is first converted to pgssub and extracted using [pgsrip](https://github.com/ratoaq2/pgsrip) to srt. From srt it is converted to the desired formats.

## Installation

### Docker Compose
```yaml
services:
    subtitle-extract:
        image: ghcr.io/klementng/subtitle-extract:main
        container_name: subtitle-extract
        user: 1000:1000
        volumes:
            - /path/to/media:/media
        
        command: --formats srt ass --languages eng --postprocessing postprocess.yml --scan_interval 720 
        restart: unless-stopped
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage:

```sh
usage: main.py [-h] [--path PATH] [--formats {ass,srt,vtt} [{ass,srt,vtt} ...]] [--languages LANGUAGES [LANGUAGES ...]] [--overwrite] [--postprocessing POSTPROCESSING]
               [--scan_interval SCAN_INTERVAL] [--log_level LOG_LEVEL] [--log_file LOG_FILE] [--progress_bar {on,off}]

options:
  -h, --help            show this help message and exit
  --path PATH           Path to media file/folder
  --formats {ass,srt,vtt} [{ass,srt,vtt} ...]
                        Subtitles formats to extract to
  --languages LANGUAGES [LANGUAGES ...]
                        Select subtitle languages stream to extract from, use 'all' to extract all languages
  --overwrite           Overwrite existing subtitle file
  --postprocessing POSTPROCESSING
                        Path to postprocessing config file
  --scan_interval SCAN_INTERVAL
                        Interval to scan folder in mins (set 0 to disable and exit upon completion)
  --log_level LOG_LEVEL
                        Setting logging level
  --log_file LOG_FILE   Path to log file
  --progress_bar {on,off}
                        Enable progress bar

```