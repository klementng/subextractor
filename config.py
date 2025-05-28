import os


from dotenv import load_dotenv

load_dotenv()


def convert_to_bool(value):
    return str(value).lower() in ("true", "t")


def get_list(value):
    return [v.strip() for v in value.split(",") if v.strip()]


APP_WATCH = convert_to_bool(os.getenv("APP_WATCH", "false"))
APP_SCAN_INTERVAL = int(os.getenv("APP_SCAN_INTERVAL", "0"))

APP_ENABLED_EXTRACTOR = convert_to_bool(os.getenv("APP_ENABLED_EXTRACTOR", "false"))
APP_ENABLED_POSTPROCESSOR = convert_to_bool(
    os.getenv("APP_ENABLED_POSTPROCESSOR", "false")
)

EXTRACTOR_EXCLUDE_ENABLE = convert_to_bool(
    os.getenv("EXTRACTOR_EXCLUDE_ENABLE", "false")
)
EXTRACTOR_EXCLUDE_FILE = os.getenv("EXTRACTOR_EXCLUDE_FILE", "./extracted.txt")
EXTRACTOR_EXCLUDE_APPEND = convert_to_bool(
    os.getenv("EXTRACTOR_EXCLUDE_APPEND", "false")
)
EXTRACTOR_EXTRACT_BITMAP = convert_to_bool(
    os.getenv("EXTRACTOR_EXTRACT_BITMAP", "false")
)

EXTRACTOR_CONFIG_OVERWRITE = convert_to_bool(
    os.getenv("EXTRACTOR_CONFIG_OVERWRITE", "true")
)
EXTRACTOR_CONFIG_DESIRED_FORMATS = get_list(
    os.getenv("EXTRACTOR_CONFIG_DESIRED_FORMATS", "srt,ass")
)
EXTRACTOR_CONFIG_LANGUAGES = get_list(os.getenv("EXTRACTOR_CONFIG_LANGUAGES", "all"))
EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS = os.getenv(
    "EXTRACTOR_CONFIG_UNKNOWN_LANGUAGE_AS", "eng"
)


POSTPROCESSOR_EXCLUDE_ENBALE = os.getenv(
    "POSTPROCESSOR_EXCLUDE_ENBALE", "./postprocessed.txt"
)
POSTPROCESSOR_EXCLUDE_FILE = os.getenv(
    "POSTPROCESSOR_EXCLUDE_FILE", "./postprocessed.txt"
)
POSTPROCESSOR_EXCLUDE_APPEND = convert_to_bool(
    os.getenv("POSTPROCESSOR_EXCLUDED_APPEND", "false")
)

POSTPROCESSOR_CONFIG_WORKFLOW_FILE = os.getenv(
    "POSTPROCESSOR_CONFIG_WORKFLOW_FILE", "postprocess.yaml"
)
