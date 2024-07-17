
<a name="readme-top"></a>

# Subtitle Extract

## About The Project

This Python script extracts both text and image-based subtitles from media files and saves them as .ass, .srt, or .vtt subtitle files. Additionally, it includes a customizable post-processor that standardizes the styling of .ass subtitles while retaining their original positioning.

## How It Works

In summary:

- `run script --> subtitle files --> postprocess --> output`

### Extraction

The extraction process first uses `ffprobe` to identify all available subtitle streams. Once identified, the `ffmpeg` command is executed to extract the desired subtitle streams into the specified formats.

For image-based subtitles, the subtitle stream is converted into .sup format, and OCR is performed using [pgsrip](https://pypi.org/project/pgsrip/) which uses `tesseract-ocr` to transcribe the subtitles into a .srt file. The .srt file is then converted into the desired formats.

### Postprocessing

Once the extraction is complete, the tool runs a postprocessor that edits the subtitle files using the [pysubs2](https://pypi.org/project/pysubs2/) package. The tool executes a default workflow defined in [postprocess.yml](./postprocess.yml) (or a custom defined workflow).

## Installation / Usage

### Docker run

Usage via docker run

```
docker run -v /PATH/TO/MEDIA/DIR:/media -it --rm ghcr.io/klementng/subtitle-extract:latest full /media [options]
```

### Docker compose

Used for watching directory for changes

- see [docker-compose.yml](./docker-compose.yml) for sample configuration

## Options

### Extract mode

Extract subtitles mode options:

<details>
  <summary>Show options</summary>

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

</details>

### Format options

Format / postprocessing of subtitles options:

<details>
  <summary>Show options</summary>

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

</details>

## Postprocesser

To change styling of the ssa subtitle file, the [postprocess.yml](./postprocess.yml) file can be edited.
