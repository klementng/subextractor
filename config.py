import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Application configuration")

    parser.add_argument("path", help="Path to media file/folder", default="/media")
    parser.add_argument(
        "--log_level", help="Logging level (default: INFO)", default="INFO"
    )
    parser.add_argument(
        "--log_file", help="Path to log file (default: None)", default=None
    )

    # App settings
    parser.add_argument(
        "--app-watch",
        action="store_true",
        default=False,
        help="Enable app watch mode (default: false)",
    )
    parser.add_argument(
        "--app-scan-interval",
        type=int,
        default=0,
        help="App scan interval in seconds (default: 0)",
    )
    parser.add_argument(
        "--app-enabled-extractor",
        action="store_true",
        default=True,
        help="Enable extractor (default: true)",
    )
    parser.add_argument(
        "--no-app-enabled-extractor",
        dest="app_enabled_extractor",
        action="store_false",
        help="Disable extractor",
    )
    parser.add_argument(
        "--app-enabled-postprocessor",
        action="store_true",
        default=True,
        help="Enable postprocessor (default: true)",
    )
    parser.add_argument(
        "--no-app-enabled-postprocessor",
        dest="app_enabled_postprocessor",
        action="store_false",
        help="Disable postprocessor",
    )

    # Extractor settings
    parser.add_argument(
        "--extractor-exclude-enable",
        action="store_true",
        default=False,
        help="Enable extractor exclude (default: false)",
    )
    parser.add_argument(
        "--extractor-exclude-file",
        type=str,
        default="./extracted.txt",
        help="Extractor exclude file path (default: ./extracted.txt)",
    )
    parser.add_argument(
        "--extractor-exclude-append",
        action="store_true",
        default=False,
        help="Append to extractor exclude file (default: false)",
    )
    parser.add_argument(
        "--extractor-extract-bitmap",
        action="store_true",
        default=False,
        help="Extract bitmap (default: false)",
    )
    parser.add_argument(
        "--extractor-config-overwrite",
        action="store_true",
        default=False,
        help="Overwrite extractor config (default: true)",
    )
    parser.add_argument(
        "--no-extractor-config-overwrite",
        dest="extractor_config_overwrite",
        action="store_false",
        help="Don't overwrite extractor config",
    )
    parser.add_argument(
        "--extractor-config-desired-formats",
        nargs="+",
        default=["srt", "ass"],
        help="List of desired formats (default: srt ass)",
    )
    parser.add_argument(
        "--extractor-config-languages",
        nargs="+",
        default=["all"],
        help="List of languages (default: all)",
    )
    parser.add_argument(
        "--extractor-config-unknown-language-as",
        type=str,
        default="eng",
        help="Unknown language fallback (default: eng)",
    )

    # Postprocessor settings
    parser.add_argument(
        "--postprocessor-exclude-enable",
        action="store_true",
        default=False,
        help="Postprocessor exclude enable (default: False)",
    )
    parser.add_argument(
        "--postprocessor-exclude-file",
        type=str,
        default="./postprocessed.txt",
        help="Postprocessor exclude file path (default: ./postprocessed.txt)",
    )
    parser.add_argument(
        "--postprocessor-exclude-append",
        action="store_true",
        default=False,
        help="Append to postprocessor exclude file (default: false)",
    )
    parser.add_argument(
        "--postprocessor-config-workflow-file",
        type=str,
        default="postprocess.yaml",
        help="Postprocessor workflow file (default: postprocess.yaml)",
    )

    args = parser.parse_args()

    # No need to convert list arguments since they're already lists
    return args


config = parse_args()

PATH = config.path
LOG_LEVEL = config.log_level
LOG_FILE = config.log_file

APP_WATCH = config.app_watch
APP_SCAN_INTERVAL = config.app_scan_interval
APP_ENABLED_EXTRACTOR = config.app_enabled_extractor
APP_ENABLED_POSTPROCESSOR = config.app_enabled_postprocessor
EXTRACTOR_EXCLUDE_ENABLE = config.extractor_exclude_enable
EXTRACTOR_EXCLUDE_FILE = config.extractor_exclude_file
EXTRACTOR_EXCLUDE_APPEND = config.extractor_exclude_append
EXTRACTOR_EXTRACT_BITMAP = config.extractor_extract_bitmap
EXTRACTOR_CONFIG_OVERWRITE = config.extractor_config_overwrite
EXTRACTOR_CONFIG_DESIRED_FORMATS = config.extractor_config_desired_formats
EXTRACTOR_CONFIG_LANGUAGES = config.extractor_config_languages
EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS = config.extractor_config_unknown_language_as
POSTPROCESSOR_EXCLUDE_ENABLE = config.postprocessor_exclude_enable
POSTPROCESSOR_EXCLUDE_FILE = config.postprocessor_exclude_file
POSTPROCESSOR_EXCLUDE_APPEND = config.postprocessor_exclude_append
POSTPROCESSOR_CONFIG_WORKFLOW_FILE = config.postprocessor_config_workflow_file
