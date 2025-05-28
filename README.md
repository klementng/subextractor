
<a name="readme-top"></a>

# Subtitle Extract

> [!WARNING]  
> Breaking changes from V1 to V2, see new arguments below 

## About The Project

This Python script extracts both text and image-based subtitles from media files and saves them as .ass, .srt, or .vtt subtitle files. Additionally, it includes a customizable post-processor that standardizes the styling of .ass subtitles while retaining their original positioning.

In summary:
- `run script --> extract subtitle files --> postprocess --> output`

### Extraction

The extraction process first uses `ffprobe` to identify all available subtitle streams. Once identified, the `ffmpeg` command is executed to extract the desired subtitle streams into the specified formats.

For image-based subtitles, the subtitle stream is converted into .sup format, and OCR is performed using [pgsrip](https://pypi.org/project/pgsrip/) which uses `tesseract-ocr` to transcribe the subtitles into a .srt file. The .srt file is then converted into the desired formats.

### Postprocessing

Once the extraction is complete, the tool runs a postprocessor that edits the subtitle files using the [pysubs2](https://pypi.org/project/pysubs2/) package. The tool executes a default workflow defined in [postprocess.yml](./postprocess.yml) (or a custom defined workflow).

## Installation / Usage

### Docker run

Usage via docker run

```
docker run -u 1000:1000 -v /PATH/TO/MEDIA/DIR:/media -it --rm ghcr.io/klementng/subtitle-extract:latest full /media [options]
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
usage: main.py [-h] [--app-watch] [--app-scan-interval APP_SCAN_INTERVAL] [--app-enabled-extractor] [--no-app-enabled-extractor]
               [--app-enabled-postprocessor] [--no-app-enabled-postprocessor] [--extractor-exclude-enable]
               [--extractor-exclude-file EXTRACTOR_EXCLUDE_FILE] [--extractor-exclude-append] [--extractor-extract-bitmap]
               [--extractor-config-overwrite] [--no-extractor-config-overwrite]
               [--extractor-config-desired-formats EXTRACTOR_CONFIG_DESIRED_FORMATS [EXTRACTOR_CONFIG_DESIRED_FORMATS ...]]
               [--extractor-config-languages EXTRACTOR_CONFIG_LANGUAGES [EXTRACTOR_CONFIG_LANGUAGES ...]]
               [--extractor-config-unknown-language-as EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS]
               [--postprocessor-exclude-enable POSTPROCESSOR_EXCLUDE_ENABLE] [--postprocessor-exclude-file POSTPROCESSOR_EXCLUDE_FILE]
               [--postprocessor-exclude-append] [--postprocessor-config-workflow-file POSTPROCESSOR_CONFIG_WORKFLOW_FILE]

Application configuration

options:
  -h, --help            show this help message and exit
  --app-watch           Enable app watch mode (default: false)
  --app-scan-interval APP_SCAN_INTERVAL
                        App scan interval in seconds (default: 0)
  --app-enabled-extractor
                        Enable extractor (default: true)
  --no-app-enabled-extractor
                        Disable extractor
  --app-enabled-postprocessor
                        Enable postprocessor (default: true)
  --no-app-enabled-postprocessor
                        Disable postprocessor
  --extractor-exclude-enable
                        Enable extractor exclude (default: false)
  --extractor-exclude-file EXTRACTOR_EXCLUDE_FILE
                        Extractor exclude file path (default: ./extracted.txt)
  --extractor-exclude-append
                        Append to extractor exclude file (default: false)
  --extractor-extract-bitmap
                        Extract bitmap (default: false)
  --extractor-config-overwrite
                        Overwrite extractor config (default: true)
  --no-extractor-config-overwrite
                        Don't overwrite extractor config
  --extractor-config-desired-formats EXTRACTOR_CONFIG_DESIRED_FORMATS [EXTRACTOR_CONFIG_DESIRED_FORMATS ...]
                        List of desired formats (default: srt ass)
  --extractor-config-languages EXTRACTOR_CONFIG_LANGUAGES [EXTRACTOR_CONFIG_LANGUAGES ...]
                        List of languages (default: all)
  --extractor-config-unknown-language-as EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS
                        Unknown language fallback (default: eng)
  --postprocessor-exclude-enable POSTPROCESSOR_EXCLUDE_ENABLE
                        Postprocessor exclude enable (default: ./postprocessed.txt)
  --postprocessor-exclude-file POSTPROCESSOR_EXCLUDE_FILE
                        Postprocessor exclude file path (default: ./postprocessed.txt)
  --postprocessor-exclude-append
                        Append to postprocessor exclude file (default: false)
  --postprocessor-config-workflow-file POSTPROCESSOR_CONFIG_WORKFLOW_FILE
                        Postprocessor workflow file (default: postprocess.yaml)
```

</details>

## Postprocesser

To change styling of the ssa subtitle file, the [postprocess.yml](./postprocess.yml) file can be edited. To add custom actions bind / replace `/app/postprocessing/user_actions.py`
